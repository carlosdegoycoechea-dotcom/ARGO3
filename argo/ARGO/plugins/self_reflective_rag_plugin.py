"""
Self-Reflective RAG Plugin
Self-evaluates response quality and detects hallucinations

Based on: "Self-RAG: Learning to Retrieve, Generate, and Critique" (2023)
https://arxiv.org/abs/2310.11511

Capabilities:
- Self-evaluation of generated responses
- Hallucination detection
- Consistency verification
- Confidence scoring
- Automatic regeneration if quality is low

INTEGRATION: Uses POST_LLM_CALL hook, does NOT modify core
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import re

from core.plugins import (
    Plugin,
    BaseIntelligencePlugin,
    PluginMetadata,
    PluginCapability
)
from core.plugins.hooks import HookPoint

logger = logging.getLogger(__name__)


class SelfReflectiveRAGPlugin(BaseIntelligencePlugin):
    """
    Self-Reflective RAG implementation

    Flow:
    1. POST_LLM_CALL: Intercept generated response
    2. Self-evaluate quality (relevance, support, consistency)
    3. Check for hallucinations
    4. If quality < threshold: mark for regeneration
    5. Return enhanced response with confidence scores
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.quality_threshold = self.config.get('quality_threshold', 0.6)
        self.check_hallucinations = self.config.get('check_hallucinations', True)
        self.model_router = None
        self.project_id = None

    @property
    def name(self) -> str:
        return "self_reflective_rag"

    @property
    def capability(self) -> str:
        return "self_reflection"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, model_router, project_id: str):
        """Initialize with model router"""
        self.model_router = model_router
        self.project_id = project_id
        logger.info(f"✅ Self-Reflective RAG initialized (threshold={self.quality_threshold})")

    async def enhance(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance response with self-reflection

        Args:
            query: Original query
            context: Contains response, sources, etc.

        Returns:
            Enhanced context with quality scores
        """
        response = context.get('response', '')

        if not response:
            return context

        # Self-evaluation dimensions
        relevance_score = await self._evaluate_relevance(query, response)
        support_score = await self._evaluate_support(response, context.get('sources', []))
        consistency_score = await self._evaluate_consistency(response)

        # Overall quality
        overall_quality = (relevance_score + support_score + consistency_score) / 3

        logger.debug(f"Self-Reflection scores: R={relevance_score:.2f} S={support_score:.2f} C={consistency_score:.2f}")

        # Check for hallucinations
        has_hallucination = False
        if self.check_hallucinations:
            has_hallucination = await self._detect_hallucination(response, context.get('sources', []))

        # Add metadata
        context['self_reflection'] = {
            'relevance_score': relevance_score,
            'support_score': support_score,
            'consistency_score': consistency_score,
            'overall_quality': overall_quality,
            'has_hallucination': has_hallucination,
            'confidence': overall_quality if not has_hallucination else overall_quality * 0.5
        }

        # Mark for regeneration if quality is low
        if overall_quality < self.quality_threshold or has_hallucination:
            logger.warning(f"⚠️ Low quality response (Q={overall_quality:.2f}, H={has_hallucination})")
            context['needs_regeneration'] = True
            context['regeneration_reason'] = "Low quality or hallucination detected"

        return context

    async def _evaluate_relevance(self, query: str, response: str) -> float:
        """
        Evaluate if response is relevant to query

        Returns:
            Relevance score 0-1
        """
        if not self.model_router:
            return 0.7  # Default

        prompt = f"""Evaluate if this response is relevant to the question.

Question: "{query}"

Response: "{response[:500]}"

On a scale of 0.0 to 1.0, how relevant is the response?
- 0.0 = completely irrelevant (off-topic)
- 0.5 = partially relevant
- 1.0 = highly relevant (directly answers question)

Respond with ONLY a number:"""

        try:
            result = self.model_router.run(
                task_type="analysis",
                project_id=self.project_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )

            score = float(result.content.strip())
            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.error(f"Relevance evaluation failed: {e}")
            return 0.7

    async def _evaluate_support(self, response: str, sources: List) -> float:
        """
        Evaluate if response is supported by sources

        Returns:
            Support score 0-1
        """
        if not sources:
            return 0.5  # No sources to verify

        if not self.model_router:
            return 0.7

        # Get source texts
        source_texts = []
        for src in sources[:3]:  # Top 3 sources
            if isinstance(src, dict):
                source_texts.append(src.get('content', ''))
            else:
                source_texts.append(getattr(src, 'content', ''))

        sources_combined = "\n\n".join(source_texts)[:1000]

        prompt = f"""Evaluate if this response is supported by the provided sources.

Response: "{response[:500]}"

Sources: "{sources_combined}"

On a scale of 0.0 to 1.0, how well is the response supported?
- 0.0 = not supported (makes claims not in sources)
- 0.5 = partially supported
- 1.0 = fully supported (all claims backed by sources)

Respond with ONLY a number:"""

        try:
            result = self.model_router.run(
                task_type="analysis",
                project_id=self.project_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )

            score = float(result.content.strip())
            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.error(f"Support evaluation failed: {e}")
            return 0.7

    async def _evaluate_consistency(self, response: str) -> float:
        """
        Evaluate internal consistency of response

        Returns:
            Consistency score 0-1
        """
        # Rule-based checks
        score = 1.0

        # Check for contradictory phrases
        contradictions = [
            (r"yes.*but.*no", 0.3),
            (r"always.*never", 0.3),
            (r"impossible.*possible", 0.3),
            (r"cannot.*can", 0.2)
        ]

        response_lower = response.lower()
        for pattern, penalty in contradictions:
            if re.search(pattern, response_lower):
                score -= penalty
                logger.debug(f"Contradiction detected: {pattern}")

        # Check for hedging/uncertainty
        uncertainty_markers = ["might", "maybe", "possibly", "unclear", "uncertain"]
        uncertainty_count = sum(1 for marker in uncertainty_markers if marker in response_lower)

        if uncertainty_count > 3:
            score -= 0.1 * (uncertainty_count - 3)
            logger.debug(f"High uncertainty: {uncertainty_count} markers")

        return max(0.0, min(1.0, score))

    async def _detect_hallucination(self, response: str, sources: List) -> bool:
        """
        Detect potential hallucinations

        Returns:
            True if hallucination detected
        """
        # Rule-based hallucination detection
        hallucination_indicators = [
            "according to my knowledge",
            "as far as i know",
            "i believe",
            "in my experience",
            "generally speaking",
            "it's common knowledge"
        ]

        response_lower = response.lower()

        for indicator in hallucination_indicators:
            if indicator in response_lower:
                logger.warning(f"Hallucination indicator: '{indicator}'")
                return True

        # Check for specific numeric claims without source
        has_numbers = bool(re.search(r'\d+(\.\d+)?%|\$\d+|\d+ (days|weeks|months)', response))

        if has_numbers and not sources:
            logger.warning("Specific numeric claims without sources")
            return True

        return False


class SelfReflectiveRAGPluginWrapper(Plugin):
    """Plugin wrapper for Self-Reflective RAG"""

    def __init__(self):
        self.metadata = PluginMetadata(
            name="self_reflective_rag",
            version="1.0.0",
            author="ARGO Team",
            description="Self-Reflective RAG - evaluates response quality and detects hallucinations",
            capabilities=[PluginCapability.INTELLIGENCE],
            dependencies=[],  # Uses existing
            enabled=True
        )
        self.self_rag = None
        self.system = None

    def initialize(self, system):
        """Initialize Self-Reflective RAG plugin"""
        self.system = system

        # Get config
        config = {}
        if hasattr(system, 'config'):
            config = system.config.get('self_reflective_rag', {})

        # Create instance
        self.self_rag = SelfReflectiveRAGPlugin(config)

        # Initialize
        if hasattr(system, 'model_router') and hasattr(system, 'active_project'):
            self.self_rag.initialize(system.model_router, system.active_project.get('id', 'default'))

        # Register
        system.plugins.register_intelligence_plugin(self.self_rag)

        # Register hook - evaluates AFTER LLM generates response
        system.plugins.hooks.register(
            HookPoint.POST_LLM_CALL,
            self.evaluate_response,
            priority=10
        )

        logger.info("✅ Self-Reflective RAG plugin initialized")
        logger.info(f"   - Quality threshold: {self.self_rag.quality_threshold}")
        logger.info(f"   - Hallucination check: {'enabled' if self.self_rag.check_hallucinations else 'disabled'}")

    def evaluate_response(self, data: Dict, context: Dict) -> Dict:
        """
        Hook function called after LLM response

        Evaluates response quality WITHOUT modifying LLM provider
        """
        query = context.get('query', '')

        if not query:
            return data

        logger.debug("🔍 Self-Reflection evaluating response")

        # Run evaluation
        try:
            import asyncio
            enhanced = asyncio.run(self.self_rag.enhance(query, data))

            # Log results
            if 'self_reflection' in enhanced:
                ref = enhanced['self_reflection']
                logger.info(
                    f"Self-Reflection: Q={ref['overall_quality']:.2f} "
                    f"Confidence={ref['confidence']:.2f}"
                )

            return enhanced

        except Exception as e:
            logger.error(f"Self-Reflection error: {e}")
            return data

    def shutdown(self):
        """Cleanup"""
        logger.info("Self-Reflective RAG plugin shutdown")

    def health_check(self) -> bool:
        """Health check"""
        return self.self_rag is not None
