"""
Agentic Retrieval Plugin
Intelligent retrieval using specialized agents

Based on: "ReAct" and "Toolformer" approaches
https://arxiv.org/abs/2210.03629

Capabilities:
- Multiple specialized retrieval agents
- Dynamic agent selection based on query type
- Multi-step retrieval with reasoning
- Tool use for enhanced retrieval

INTEGRATION: Uses PRE_RAG_SEARCH hook, does NOT modify core
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from core.plugins import (
    Plugin,
    BaseIntelligencePlugin,
    PluginMetadata,
    PluginCapability
)
from core.plugins.hooks import HookPoint

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries for agent routing"""
    FACTUAL = "factual"  # Simple fact lookup
    ANALYTICAL = "analytical"  # Requires analysis
    COMPARISON = "comparison"  # Comparing items
    PROCEDURAL = "procedural"  # How-to questions
    EXPLORATORY = "exploratory"  # Open-ended research
    TEMPORAL = "temporal"  # Time-based queries


@dataclass
class RetrievalPlan:
    """Plan for agentic retrieval"""
    query_type: QueryType
    agent: str
    strategy: str
    parameters: Dict[str, Any]
    reasoning: str


class BaseRetrievalAgent:
    """Base class for retrieval agents"""

    def __init__(self, name: str):
        self.name = name

    def can_handle(self, query: str, query_type: QueryType) -> bool:
        """Check if this agent can handle the query"""
        raise NotImplementedError

    def create_plan(self, query: str, context: Dict) -> RetrievalPlan:
        """Create retrieval plan"""
        raise NotImplementedError


class FactualAgent(BaseRetrievalAgent):
    """Agent for factual queries"""

    def __init__(self):
        super().__init__("factual_agent")

    def can_handle(self, query: str, query_type: QueryType) -> bool:
        return query_type == QueryType.FACTUAL

    def create_plan(self, query: str, context: Dict) -> RetrievalPlan:
        return RetrievalPlan(
            query_type=QueryType.FACTUAL,
            agent=self.name,
            strategy="direct_lookup",
            parameters={
                'top_k': 3,
                'use_hyde': False,  # Direct lookup, no HyDE
                'use_reranker': False
            },
            reasoning="Simple factual query - direct retrieval is most efficient"
        )


class AnalyticalAgent(BaseRetrievalAgent):
    """Agent for analytical queries"""

    def __init__(self):
        super().__init__("analytical_agent")

    def can_handle(self, query: str, query_type: QueryType) -> bool:
        return query_type == QueryType.ANALYTICAL

    def create_plan(self, query: str, context: Dict) -> RetrievalPlan:
        return RetrievalPlan(
            query_type=QueryType.ANALYTICAL,
            agent=self.name,
            strategy="hyde_enhanced",
            parameters={
                'top_k': 5,
                'use_hyde': True,  # Use HyDE for better retrieval
                'use_reranker': True,
                'include_library': True  # Include library docs
            },
            reasoning="Analytical query - use HyDE and reranking for comprehensive results"
        )


class ComparisonAgent(BaseRetrievalAgent):
    """Agent for comparison queries"""

    def __init__(self):
        super().__init__("comparison_agent")

    def can_handle(self, query: str, query_type: QueryType) -> bool:
        return query_type == QueryType.COMPARISON

    def create_plan(self, query: str, context: Dict) -> RetrievalPlan:
        # For comparisons, we need info about both items
        return RetrievalPlan(
            query_type=QueryType.COMPARISON,
            agent=self.name,
            strategy="multi_aspect_retrieval",
            parameters={
                'top_k': 8,  # More results to cover both items
                'use_hyde': True,
                'use_reranker': True,
                'diversity_boost': True
            },
            reasoning="Comparison query - retrieve diverse results covering multiple aspects"
        )


class ExploratoryAgent(BaseRetrievalAgent):
    """Agent for exploratory queries"""

    def __init__(self):
        super().__init__("exploratory_agent")

    def can_handle(self, query: str, query_type: QueryType) -> bool:
        return query_type == QueryType.EXPLORATORY

    def create_plan(self, query: str, context: Dict) -> RetrievalPlan:
        return RetrievalPlan(
            query_type=QueryType.EXPLORATORY,
            agent=self.name,
            strategy="broad_retrieval",
            parameters={
                'top_k': 10,  # Cast a wide net
                'use_hyde': True,
                'use_reranker': True,
                'include_library': True,
                'diversity_boost': True
            },
            reasoning="Exploratory query - maximize breadth and diversity of results"
        )


class AgenticRetrievalPlugin(BaseIntelligencePlugin):
    """
    Agentic Retrieval implementation

    Flow:
    1. PRE_RAG_SEARCH: Intercept search request
    2. Classify query type
    3. Select appropriate agent
    4. Agent creates retrieval plan
    5. Modify search parameters accordingly
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.model_router = None
        self.project_id = None

        # Initialize agents
        self.agents = {
            'factual': FactualAgent(),
            'analytical': AnalyticalAgent(),
            'comparison': ComparisonAgent(),
            'exploratory': ExploratoryAgent()
        }

    @property
    def name(self) -> str:
        return "agentic_retrieval"

    @property
    def capability(self) -> str:
        return "agentic_retrieval"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, model_router, project_id: str):
        """Initialize with model router"""
        self.model_router = model_router
        self.project_id = project_id
        logger.info(f"✅ Agentic Retrieval initialized with {len(self.agents)} agents")

    async def enhance(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance retrieval with agentic approach

        Args:
            query: User query
            context: Search context

        Returns:
            Enhanced context with retrieval plan
        """
        # Step 1: Classify query type
        query_type = await self._classify_query(query)

        logger.debug(f"Query classified as: {query_type.value}")

        # Step 2: Select agent
        agent = self._select_agent(query, query_type)

        if not agent:
            logger.warning(f"No agent found for query type: {query_type}")
            return context

        # Step 3: Create retrieval plan
        plan = agent.create_plan(query, context)

        logger.info(f"🤖 Agent: {plan.agent} | Strategy: {plan.strategy}")

        # Step 4: Apply plan to search parameters
        context['agentic_plan'] = {
            'query_type': plan.query_type.value,
            'agent': plan.agent,
            'strategy': plan.strategy,
            'reasoning': plan.reasoning
        }

        # Modify search parameters based on plan
        context.update(plan.parameters)

        return context

    async def _classify_query(self, query: str) -> QueryType:
        """
        Classify query type

        Returns:
            QueryType enum
        """
        query_lower = query.lower()

        # Rule-based classification (fast)
        if any(word in query_lower for word in ['what is', 'who is', 'when is', 'where is']):
            return QueryType.FACTUAL

        if any(word in query_lower for word in ['compare', 'difference', 'versus', 'vs', 'better']):
            return QueryType.COMPARISON

        if any(word in query_lower for word in ['how to', 'how do', 'steps to', 'procedure']):
            return QueryType.PROCEDURAL

        if any(word in query_lower for word in ['why', 'explain', 'analyze', 'assess', 'evaluate']):
            return QueryType.ANALYTICAL

        if any(word in query_lower for word in ['explore', 'research', 'investigate', 'tell me about']):
            return QueryType.EXPLORATORY

        # Default
        return QueryType.ANALYTICAL

    def _select_agent(self, query: str, query_type: QueryType) -> Optional[BaseRetrievalAgent]:
        """Select appropriate agent for query"""
        for agent in self.agents.values():
            if agent.can_handle(query, query_type):
                return agent

        # Fallback to analytical agent
        return self.agents.get('analytical')


class AgenticRetrievalPluginWrapper(Plugin):
    """Plugin wrapper for Agentic Retrieval"""

    def __init__(self):
        self.metadata = PluginMetadata(
            name="agentic_retrieval",
            version="1.0.0",
            author="ARGO Team",
            description="Agentic Retrieval - intelligent multi-agent retrieval system",
            capabilities=[PluginCapability.INTELLIGENCE],
            dependencies=[],  # Uses existing
            enabled=True
        )
        self.agentic = None
        self.system = None

    def initialize(self, system):
        """Initialize Agentic Retrieval plugin"""
        self.system = system

        # Get config
        config = {}
        if hasattr(system, 'config'):
            config = system.config.get('agentic_retrieval', {})

        # Create instance
        self.agentic = AgenticRetrievalPlugin(config)

        # Initialize
        if hasattr(system, 'model_router') and hasattr(system, 'active_project'):
            self.agentic.initialize(system.model_router, system.active_project.get('id', 'default'))

        # Register
        system.plugins.register_intelligence_plugin(self.agentic)

        # Register hook - plans BEFORE RAG search
        system.plugins.hooks.register(
            HookPoint.PRE_RAG_SEARCH,
            self.plan_retrieval,
            priority=15  # High priority
        )

        logger.info("✅ Agentic Retrieval plugin initialized")
        logger.info(f"   - Agents available: {list(self.agentic.agents.keys())}")

    def plan_retrieval(self, data: Dict, context: Dict) -> Dict:
        """
        Hook function called before RAG search

        Plans retrieval strategy WITHOUT modifying RAG engine
        """
        query = data.get('query', context.get('query', ''))

        if not query:
            return data

        # Run agentic planning
        try:
            import asyncio
            enhanced = asyncio.run(self.agentic.enhance(query, data))

            # Log results
            if 'agentic_plan' in enhanced:
                plan = enhanced['agentic_plan']
                logger.info(f"🤖 Agentic plan: {plan['agent']} - {plan['strategy']}")

            return enhanced

        except Exception as e:
            logger.error(f"Agentic retrieval error: {e}")
            return data

    def shutdown(self):
        """Cleanup"""
        logger.info("Agentic Retrieval plugin shutdown")

    def health_check(self) -> bool:
        """Health check"""
        return self.agentic is not None and len(self.agentic.agents) > 0
