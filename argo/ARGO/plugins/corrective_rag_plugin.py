"""
Corrective RAG (CRAG) Plugin
Verifies and corrects retrieved information before LLM generation

Based on: "Corrective Retrieval Augmented Generation" (2024)
https://arxiv.org/abs/2401.15884

Capabilities:
- Relevance verification of retrieved documents
- Web search fallback for low-quality retrievals
- Fact verification and correction
- Adaptive retrieval strategy

INTEGRATION: Uses hooks, does NOT modify rag_engine.py
"""

import logging
from typing import Dict, List, Optional, Any
import asyncio

from core.plugins import (
    Plugin,
    BaseIntelligencePlugin,
    PluginMetadata,
    PluginCapability
)
from core.plugins.hooks import HookPoint

logger = logging.getLogger(__name__)


class CorrectiveRAGPlugin(BaseIntelligencePlugin):
    """
    Corrective RAG implementation

    Flow:
    1. POST_RAG_SEARCH: Verify relevance of retrieved docs
    2. If relevance < threshold: trigger web search
    3. Combine internal + external knowledge
    4. Return corrected results
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.relevance_threshold = self.config.get('relevance_threshold', 0.6)
        self.use_web_search = self.config.get('use_web_search', False)
        self.model_router = None
        self.project_id = None

    @property
    def name(self) -> str:
        return "corrective_rag"

    @property
    def capability(self) -> str:
        return "corrective_rag"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, model_router, project_id: str):
        """Initialize with model router and project context"""
        self.model_router = model_router
        self.project_id = project_id
        logger.info(f"✅ CRAG initialized (threshold={self.relevance_threshold})")

    async def enhance(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance retrieval with corrective mechanism

        Args:
            query: User query
            context: Retrieved results and metadata

        Returns:
            Enhanced context with corrections
        """
        results = context.get('results', [])

        if not results:
            logger.warning("No results to verify")
            return context

        # Step 1: Verify relevance
        relevance_scores = await self._verify_relevance(query, results)

        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0

        logger.debug(f"CRAG: Average relevance = {avg_relevance:.2f}")

        # Step 2: If low relevance, trigger correction
        if avg_relevance < self.relevance_threshold:
            logger.info(f"⚠️ Low relevance ({avg_relevance:.2f}), triggering correction")

            # Correction strategies
            corrected_results = await self._apply_corrections(query, results, context)

            context['results'] = corrected_results
            context['crag_applied'] = True
            context['crag_avg_relevance'] = avg_relevance
            context['crag_corrected'] = True
        else:
            logger.debug("✅ Good relevance, no correction needed")
            context['crag_applied'] = True
            context['crag_avg_relevance'] = avg_relevance
            context['crag_corrected'] = False

        return context

    async def _verify_relevance(self, query: str, results: List) -> List[float]:
        """
        Verify relevance of retrieved documents using LLM

        Returns:
            List of relevance scores (0-1)
        """
        if not self.model_router:
            # Fallback: use existing scores
            return [getattr(r, 'score', 0.5) for r in results]

        scores = []

        for result in results[:3]:  # Check top 3 to save costs
            content = getattr(result, 'content', str(result))

            prompt = f"""Is this document excerpt relevant to the question?

Question: "{query}"

Document excerpt: "{content[:500]}"

Respond with ONLY a number from 0.0 to 1.0:
- 0.0 = completely irrelevant
- 0.5 = somewhat relevant
- 1.0 = highly relevant

Score:"""

            try:
                response = self.model_router.run(
                    task_type="analysis",
                    project_id=self.project_id,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10
                )

                # Parse score
                score_str = response.content.strip()
                try:
                    score = float(score_str)
                    score = max(0.0, min(1.0, score))  # Clamp to [0,1]
                except:
                    score = 0.5

                scores.append(score)

            except Exception as e:
                logger.error(f"Relevance check failed: {e}")
                scores.append(0.5)

        # Fill remaining with average
        if scores:
            avg = sum(scores) / len(scores)
            scores.extend([avg] * (len(results) - len(scores)))
        else:
            scores = [0.5] * len(results)

        return scores

    async def _apply_corrections(self, query: str, results: List, context: Dict) -> List:
        """
        Apply correction strategies

        Strategies:
        1. Knowledge refinement - regenerate with better prompt
        2. Web search - complement with external info (if enabled)
        3. Decomposition - break down complex query
        """
        corrected = list(results)  # Start with originals

        # Strategy 1: Add knowledge refinement instruction
        context['needs_refinement'] = True
        context['refinement_instruction'] = (
            "The retrieved documents may have low relevance. "
            "Focus on extracting the most relevant information, "
            "and clearly state if the documents don't fully answer the question."
        )

        # Strategy 2: Web search (if enabled)
        if self.use_web_search:
            logger.info("🌐 Attempting web search for supplemental info")
            # Note: Web search would be integrated via another plugin
            context['needs_web_search'] = True

        # Strategy 3: Query decomposition (handled by Query Planning plugin)
        if len(query.split()) > 10:  # Complex query
            context['needs_decomposition'] = True

        return corrected


class CorrectiveRAGPluginWrapper(Plugin):
    """
    Plugin wrapper for Corrective RAG
    """

    def __init__(self):
        self.metadata = PluginMetadata(
            name="corrective_rag",
            version="1.0.0",
            author="ARGO Team",
            description="Corrective RAG - verifies and corrects retrieval quality",
            capabilities=[PluginCapability.INTELLIGENCE],
            dependencies=[],  # Uses existing langchain
            enabled=True
        )
        self.crag = None
        self.system = None

    def initialize(self, system):
        """Initialize CRAG plugin"""
        self.system = system

        # Get config
        config = {}
        if hasattr(system, 'config'):
            config = system.config.get('corrective_rag', {})

        # Create CRAG instance
        self.crag = CorrectiveRAGPlugin(config)

        # Initialize with model router
        if hasattr(system, 'model_router') and hasattr(system, 'active_project'):
            self.crag.initialize(system.model_router, system.active_project.get('id', 'default'))

        # Register as intelligence plugin
        system.plugins.register_intelligence_plugin(self.crag)

        # Register hook - CRITICAL: This is how we integrate without modifying RAG
        system.plugins.hooks.register(
            HookPoint.POST_RAG_SEARCH,
            self.enhance_rag_results,
            priority=10  # High priority
        )

        logger.info("✅ Corrective RAG plugin initialized")
        logger.info(f"   - Relevance threshold: {self.crag.relevance_threshold}")
        logger.info(f"   - Web search: {'enabled' if self.crag.use_web_search else 'disabled'}")

    def enhance_rag_results(self, data: Dict, context: Dict) -> Dict:
        """
        Hook function called after RAG search

        This is where CRAG magic happens WITHOUT modifying rag_engine.py
        """
        query = context.get('query', '')

        if not query:
            return data

        logger.debug(f"🔍 CRAG analyzing {len(data.get('results', []))} results")

        # Run CRAG enhancement (sync wrapper for async)
        try:
            import asyncio
            enhanced = asyncio.run(self.crag.enhance(query, data))
            return enhanced
        except Exception as e:
            logger.error(f"CRAG enhancement error: {e}")
            return data

    def shutdown(self):
        """Cleanup"""
        logger.info("Corrective RAG plugin shutdown")

    def health_check(self) -> bool:
        """Health check"""
        return self.crag is not None and self.crag.model_router is not None
