"""
Basic tests for intelligence plugins (4 advanced RAG blocks)
These are BASIC tests - comprehensive tests TODO
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.corrective_rag_plugin import CorrectiveRAGPlugin, CorrectiveRAGPluginWrapper
from plugins.self_reflective_rag_plugin import SelfReflectiveRAGPlugin, SelfReflectiveRAGPluginWrapper
from plugins.query_planning_plugin import QueryPlanningPlugin, QueryPlanningPluginWrapper
from plugins.agentic_retrieval_plugin import AgenticRetrievalPlugin, AgenticRetrievalPluginWrapper, QueryType


class TestCorrectiveRAGPlugin:
    """Basic tests for Corrective RAG Plugin"""

    def test_crag_creation(self):
        """CRAG can be instantiated"""
        crag = CorrectiveRAGPlugin()
        assert crag.name == 'corrective_rag'
        assert crag.capability == 'corrective_rag'
        assert crag.version == '1.0.0'

    def test_crag_plugin_wrapper_metadata(self):
        """CRAG Plugin wrapper has metadata"""
        plugin = CorrectiveRAGPluginWrapper()
        assert plugin.metadata.name == 'corrective_rag'
        assert plugin.metadata.version == '1.0.0'
        assert plugin.metadata.enabled is True

    def test_crag_initialization(self, mock_system):
        """CRAG can initialize"""
        plugin = CorrectiveRAGPluginWrapper()
        plugin.initialize(mock_system)

        assert plugin.system == mock_system
        assert plugin.crag is not None

    def test_crag_health_check(self):
        """CRAG health check works"""
        plugin = CorrectiveRAGPluginWrapper()
        # Before initialization, should have no model_router
        health = plugin.health_check()
        assert health is False


class TestSelfReflectiveRAGPlugin:
    """Basic tests for Self-Reflective RAG Plugin"""

    def test_self_rag_creation(self):
        """Self-RAG can be instantiated"""
        self_rag = SelfReflectiveRAGPlugin()
        assert self_rag.name == 'self_reflective_rag'
        assert self_rag.capability == 'self_reflection'
        assert self_rag.version == '1.0.0'

    def test_self_rag_plugin_wrapper_metadata(self):
        """Self-RAG Plugin wrapper has metadata"""
        plugin = SelfReflectiveRAGPluginWrapper()
        assert plugin.metadata.name == 'self_reflective_rag'
        assert plugin.metadata.version == '1.0.0'

    def test_self_rag_initialization(self, mock_system):
        """Self-RAG can initialize"""
        plugin = SelfReflectiveRAGPluginWrapper()
        plugin.initialize(mock_system)

        assert plugin.system == mock_system
        assert plugin.self_rag is not None

    def test_self_rag_quality_threshold(self):
        """Self-RAG has configurable threshold"""
        self_rag = SelfReflectiveRAGPlugin({'quality_threshold': 0.7})
        assert self_rag.quality_threshold == 0.7


class TestQueryPlanningPlugin:
    """Basic tests for Query Planning Plugin"""

    def test_query_planning_creation(self):
        """Query Planning can be instantiated"""
        planner = QueryPlanningPlugin()
        assert planner.name == 'query_planning'
        assert planner.capability == 'query_planning'
        assert planner.version == '1.0.0'

    def test_query_planning_plugin_wrapper_metadata(self):
        """Query Planning Plugin wrapper has metadata"""
        plugin = QueryPlanningPluginWrapper()
        assert plugin.metadata.name == 'query_planning'
        assert plugin.metadata.version == '1.0.0'

    def test_query_planning_complexity_measurement(self):
        """Can measure query complexity"""
        planner = QueryPlanningPlugin()

        simple = "What is ARGO?"
        assert planner._measure_complexity(simple) < 15

        complex_query = "Compare the DCMA assessment with GAO standards and also explain the differences in detail"
        assert planner._measure_complexity(complex_query) > 15

    def test_query_planning_simple_decompose(self):
        """Can do simple decomposition"""
        planner = QueryPlanningPlugin()

        query = "What is schedule analysis and also what is DCMA"
        subqueries = planner._simple_decompose(query)

        assert len(subqueries) >= 1

    def test_query_planning_initialization(self, mock_system):
        """Query Planning can initialize"""
        plugin = QueryPlanningPluginWrapper()
        plugin.initialize(mock_system)

        assert plugin.system == mock_system
        assert plugin.planner is not None


class TestAgenticRetrievalPlugin:
    """Basic tests for Agentic Retrieval Plugin"""

    def test_agentic_creation(self):
        """Agentic Retrieval can be instantiated"""
        agentic = AgenticRetrievalPlugin()
        assert agentic.name == 'agentic_retrieval'
        assert agentic.capability == 'agentic_retrieval'
        assert agentic.version == '1.0.0'

    def test_agentic_has_agents(self):
        """Agentic Retrieval has multiple agents"""
        agentic = AgenticRetrievalPlugin()

        assert 'factual' in agentic.agents
        assert 'analytical' in agentic.agents
        assert 'comparison' in agentic.agents
        assert 'exploratory' in agentic.agents

    def test_agentic_plugin_wrapper_metadata(self):
        """Agentic Plugin wrapper has metadata"""
        plugin = AgenticRetrievalPluginWrapper()
        assert plugin.metadata.name == 'agentic_retrieval'
        assert plugin.metadata.version == '1.0.0'

    def test_agentic_initialization(self, mock_system):
        """Agentic Retrieval can initialize"""
        plugin = AgenticRetrievalPluginWrapper()
        plugin.initialize(mock_system)

        assert plugin.system == mock_system
        assert plugin.agentic is not None

    def test_agentic_health_check(self):
        """Agentic health check works"""
        plugin = AgenticRetrievalPluginWrapper()
        plugin.initialize(type('obj', (object,), {
            'config': type('obj', (object,), {'get': lambda k,d=None: d})(),
            'model_router': None,
            'active_project': {'id': 'test'},
            'plugins': type('obj', (object,), {
                'register_intelligence_plugin': lambda x: None,
                'hooks': type('obj', (object,), {
                    'register': lambda *args, **kwargs: None
                })()
            })()
        })())

        health = plugin.health_check()
        assert health is True  # Has agents


class TestQueryTypeClassification:
    """Test query type classification"""

    def test_factual_query_classification(self):
        """Factual queries are classified correctly"""
        agentic = AgenticRetrievalPlugin()

        # Run sync version (mocked)
        import asyncio
        query_type = asyncio.run(agentic._classify_query("What is ARGO?"))

        assert query_type == QueryType.FACTUAL

    def test_comparison_query_classification(self):
        """Comparison queries are classified correctly"""
        agentic = AgenticRetrievalPlugin()

        import asyncio
        query_type = asyncio.run(agentic._classify_query("Compare XER and MPP"))

        assert query_type == QueryType.COMPARISON

    def test_analytical_query_classification(self):
        """Analytical queries are classified correctly"""
        agentic = AgenticRetrievalPlugin()

        import asyncio
        query_type = asyncio.run(agentic._classify_query("Why is the schedule delayed?"))

        assert query_type == QueryType.ANALYTICAL


class TestIntelligencePluginsConfiguration:
    """Test configuration options"""

    def test_crag_custom_threshold(self):
        """CRAG accepts custom threshold"""
        crag = CorrectiveRAGPlugin({'relevance_threshold': 0.8})
        assert crag.relevance_threshold == 0.8

    def test_self_rag_hallucination_check_toggle(self):
        """Self-RAG can toggle hallucination check"""
        self_rag = SelfReflectiveRAGPlugin({'check_hallucinations': False})
        assert self_rag.check_hallucinations is False

    def test_query_planning_max_subqueries(self):
        """Query Planning accepts max subqueries"""
        planner = QueryPlanningPlugin({'max_subqueries': 3})
        assert planner.max_subqueries == 3


# Mark this as basic unit tests
pytestmark = pytest.mark.unit
