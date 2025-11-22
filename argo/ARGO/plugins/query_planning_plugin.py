"""
Query Planning Plugin
Decomposes complex queries into sub-queries for better retrieval

Based on: "Decomposed Prompting" and "Least-to-Most Prompting"
https://arxiv.org/abs/2210.02406

Capabilities:
- Detects complex multi-part queries
- Decomposes into sequential sub-queries
- Plans execution order
- Synthesizes final answer from sub-results

INTEGRATION: Uses PRE_QUERY_PROCESSING hook, does NOT modify core
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re

from core.plugins import (
    Plugin,
    BaseIntelligencePlugin,
    PluginMetadata,
    PluginCapability
)
from core.plugins.hooks import HookPoint

logger = logging.getLogger(__name__)


@dataclass
class SubQuery:
    """Represents a decomposed sub-query"""
    text: str
    order: int
    depends_on: List[int] = None
    result: Optional[Dict] = None

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


class QueryPlanningPlugin(BaseIntelligencePlugin):
    """
    Query Planning implementation

    Flow:
    1. PRE_QUERY_PROCESSING: Intercept user query
    2. Analyze complexity
    3. If complex: decompose into sub-queries
    4. Plan execution order
    5. Return query plan
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.complexity_threshold = self.config.get('complexity_threshold', 15)  # words
        self.max_subqueries = self.config.get('max_subqueries', 5)
        self.model_router = None
        self.project_id = None

    @property
    def name(self) -> str:
        return "query_planning"

    @property
    def capability(self) -> str:
        return "query_planning"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, model_router, project_id: str):
        """Initialize with model router"""
        self.model_router = model_router
        self.project_id = project_id
        logger.info(f"✅ Query Planning initialized (threshold={self.complexity_threshold} words)")

    async def enhance(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance query with planning

        Args:
            query: User query
            context: Request context

        Returns:
            Enhanced context with query plan
        """
        # Step 1: Check complexity
        complexity = self._measure_complexity(query)

        logger.debug(f"Query complexity: {complexity} (threshold={self.complexity_threshold})")

        if complexity < self.complexity_threshold:
            # Simple query, no planning needed
            context['query_plan'] = None
            context['planned'] = False
            return context

        # Step 2: Decompose query
        logger.info(f"🧠 Complex query detected, decomposing...")
        subqueries = await self._decompose_query(query)

        if not subqueries or len(subqueries) == 1:
            context['query_plan'] = None
            context['planned'] = False
            return context

        # Step 3: Create execution plan
        context['query_plan'] = {
            'original_query': query,
            'subqueries': [
                {
                    'text': sq.text,
                    'order': sq.order,
                    'depends_on': sq.depends_on
                }
                for sq in subqueries
            ],
            'planned': True
        }

        logger.info(f"✅ Query plan created: {len(subqueries)} sub-queries")

        return context

    def _measure_complexity(self, query: str) -> int:
        """
        Measure query complexity

        Returns:
            Complexity score (higher = more complex)
        """
        # Multiple dimensions
        word_count = len(query.split())

        # Check for complexity indicators
        complexity_markers = [
            ('and', 2),
            ('or', 2),
            ('also', 1),
            ('additionally', 2),
            ('furthermore', 2),
            ('compare', 3),
            ('difference', 3),
            ('versus', 3),
            ('both', 2),
            ('as well as', 2)
        ]

        score = word_count

        query_lower = query.lower()
        for marker, weight in complexity_markers:
            if marker in query_lower:
                score += weight

        # Check for multiple questions
        question_marks = query.count('?')
        if question_marks > 1:
            score += question_marks * 3

        return score

    async def _decompose_query(self, query: str) -> List[SubQuery]:
        """
        Decompose complex query into sub-queries

        Returns:
            List of SubQuery objects
        """
        if not self.model_router:
            # Fallback: simple split on 'and'
            return self._simple_decompose(query)

        prompt = f"""Decompose this complex question into simpler sub-questions that can be answered sequentially.

Complex question: "{query}"

Decompose into 2-{self.max_subqueries} simpler questions. Each question should:
1. Be self-contained
2. Build on previous answers if needed
3. Be answerable from project documents

Format:
1. [First sub-question]
2. [Second sub-question]
...

Sub-questions:"""

        try:
            response = self.model_router.run(
                task_type="analysis",
                project_id=self.project_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )

            # Parse response
            subqueries = self._parse_subqueries(response.content)

            if not subqueries:
                return self._simple_decompose(query)

            return subqueries

        except Exception as e:
            logger.error(f"Query decomposition failed: {e}")
            return self._simple_decompose(query)

    def _parse_subqueries(self, text: str) -> List[SubQuery]:
        """Parse LLM response into SubQuery objects"""
        lines = text.strip().split('\n')
        subqueries = []

        for i, line in enumerate(lines):
            # Look for numbered items
            match = re.match(r'^\s*\d+[\.)]\s*(.+)$', line)
            if match:
                question = match.group(1).strip()
                subqueries.append(SubQuery(text=question, order=i+1))

        return subqueries[:self.max_subqueries]

    def _simple_decompose(self, query: str) -> List[SubQuery]:
        """Simple fallback decomposition"""
        # Split on conjunctions
        parts = re.split(r'\s+and\s+|\s+also\s+', query, flags=re.IGNORECASE)

        if len(parts) <= 1:
            return []

        return [
            SubQuery(text=part.strip(), order=i+1)
            for i, part in enumerate(parts)
            if part.strip()
        ][:self.max_subqueries]


class QueryPlanningPluginWrapper(Plugin):
    """Plugin wrapper for Query Planning"""

    def __init__(self):
        self.metadata = PluginMetadata(
            name="query_planning",
            version="1.0.0",
            author="ARGO Team",
            description="Query Planning - decomposes complex queries into sub-queries",
            capabilities=[PluginCapability.INTELLIGENCE],
            dependencies=[],  # Uses existing
            enabled=True
        )
        self.planner = None
        self.system = None

    def initialize(self, system):
        """Initialize Query Planning plugin"""
        self.system = system

        # Get config
        config = {}
        if hasattr(system, 'config'):
            config = system.config.get('query_planning', {})

        # Create instance
        self.planner = QueryPlanningPlugin(config)

        # Initialize
        if hasattr(system, 'model_router') and hasattr(system, 'active_project'):
            self.planner.initialize(system.model_router, system.active_project.get('id', 'default'))

        # Register
        system.plugins.register_intelligence_plugin(self.planner)

        # Register hook - analyzes BEFORE query processing
        system.plugins.hooks.register(
            HookPoint.PRE_QUERY_PROCESSING,
            self.plan_query,
            priority=20  # Very high priority - run first
        )

        logger.info("✅ Query Planning plugin initialized")
        logger.info(f"   - Complexity threshold: {self.planner.complexity_threshold} words")
        logger.info(f"   - Max sub-queries: {self.planner.max_subqueries}")

    def plan_query(self, data: Dict, context: Dict) -> Dict:
        """
        Hook function called before query processing

        Plans complex queries WITHOUT modifying core query logic
        """
        query = data.get('query', '')

        if not query:
            return data

        # Run planning
        try:
            import asyncio
            enhanced = asyncio.run(self.planner.enhance(query, data))

            # Log results
            if enhanced.get('query_plan'):
                plan = enhanced['query_plan']
                logger.info(f"🧠 Query decomposed into {len(plan['subqueries'])} sub-queries")

            return enhanced

        except Exception as e:
            logger.error(f"Query planning error: {e}")
            return data

    def shutdown(self):
        """Cleanup"""
        logger.info("Query Planning plugin shutdown")

    def health_check(self) -> bool:
        """Health check"""
        return self.planner is not None
