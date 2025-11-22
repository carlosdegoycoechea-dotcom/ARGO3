"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
from pathlib import Path

# Add ARGO to path
argo_root = Path(__file__).parent.parent
sys.path.insert(0, str(argo_root))


@pytest.fixture
def mock_system():
    """Mock ARGO system for plugin testing"""
    class MockSystem:
        def __init__(self):
            self.config = MockConfig()
            self.model_router = None
            self.active_project = {'id': 'test_project', 'name': 'Test Project'}
            self.plugins = None

    return MockSystem()


@pytest.fixture
def mock_config():
    """Mock configuration"""
    class MockConfig:
        def get(self, key, default=None):
            # Return reasonable defaults
            config_map = {
                'corrective_rag.relevance_threshold': 0.6,
                'self_reflective_rag.quality_threshold': 0.6,
                'query_planning.complexity_threshold': 15,
                'ocr.language': 'eng',
                'excel.pmo_mode': False,
                'plugins.directory': None
            }
            return config_map.get(key, default)

    return MockConfig()


@pytest.fixture
def sample_analysis_result():
    """Sample AnalysisResult for testing"""
    from core.plugins.base import AnalysisResult

    return AnalysisResult(
        status='success',
        data={'test': 'data'},
        metadata={'analyzer': 'test'},
        errors=[],
        warnings=[],
        execution_time_ms=10.0
    )
