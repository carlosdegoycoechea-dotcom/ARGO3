"""
Basic tests for plugin system core components
These are BASIC tests - comprehensive tests TODO
"""
import pytest
from pathlib import Path

from core.plugins.base import (
    BaseAnalyzer,
    AnalysisResult,
    PluginMetadata,
    PluginCapability
)
from core.plugins.manager import PluginManager
from core.plugins.events import EventBus, EventPriority
from core.plugins.hooks import HookManager, HookPoint


class TestBaseClasses:
    """Test base classes and protocols"""

    def test_analysis_result_creation(self):
        """AnalysisResult can be created"""
        result = AnalysisResult(
            status='success',
            data={'key': 'value'},
            metadata={'test': True}
        )
        assert result.status == 'success'
        assert result.is_success
        assert not result.has_errors

    def test_analysis_result_with_errors(self):
        """AnalysisResult handles errors"""
        result = AnalysisResult(
            status='error',
            data={},
            errors=['Error 1', 'Error 2']
        )
        assert not result.is_success
        assert result.has_errors
        assert len(result.errors) == 2

    def test_plugin_metadata_creation(self):
        """PluginMetadata can be created"""
        metadata = PluginMetadata(
            name='test_plugin',
            version='1.0.0',
            capabilities=[PluginCapability.ANALYZER]
        )
        assert metadata.name == 'test_plugin'
        assert metadata.version == '1.0.0'
        assert metadata.enabled


class TestPluginManager:
    """Test PluginManager basic functionality"""

    def test_plugin_manager_creation(self, mock_system):
        """PluginManager can be instantiated"""
        pm = PluginManager(mock_system)
        assert pm is not None
        assert pm.system == mock_system
        assert len(pm.plugins) == 0

    def test_list_plugins_empty(self, mock_system):
        """list_plugins returns empty list initially"""
        pm = PluginManager(mock_system)
        plugins = pm.list_plugins()
        assert plugins == []

    def test_list_analyzers_empty(self, mock_system):
        """list_analyzers returns empty list initially"""
        pm = PluginManager(mock_system)
        analyzers = pm.list_analyzers()
        assert analyzers == []

    def test_register_analyzer(self, mock_system):
        """Can register an analyzer"""
        pm = PluginManager(mock_system)

        # Create simple analyzer
        class TestAnalyzer(BaseAnalyzer):
            @property
            def name(self):
                return 'test_analyzer'

            @property
            def supported_formats(self):
                return ['.test']

            def analyze(self, file_path, options=None):
                return AnalysisResult(
                    status='success',
                    data={'analyzed': True}
                )

        analyzer = TestAnalyzer()
        pm.register_analyzer(analyzer)

        assert 'test_analyzer' in pm.analyzers
        assert len(pm.list_analyzers()) == 1

    def test_get_analyzer_for_file(self, mock_system):
        """Can get appropriate analyzer for file"""
        pm = PluginManager(mock_system)

        class TestAnalyzer(BaseAnalyzer):
            @property
            def name(self):
                return 'test_analyzer'

            @property
            def supported_formats(self):
                return ['.test']

            def analyze(self, file_path, options=None):
                return AnalysisResult(status='success', data={})

        pm.register_analyzer(TestAnalyzer())

        # Should find analyzer
        analyzer = pm.get_analyzer('file.test')
        assert analyzer is not None
        assert analyzer.name == 'test_analyzer'

        # Should not find analyzer
        analyzer = pm.get_analyzer('file.unknown')
        assert analyzer is None


class TestEventBus:
    """Test EventBus basic functionality"""

    def test_event_bus_creation(self):
        """EventBus can be instantiated"""
        bus = EventBus()
        assert bus is not None
        assert len(bus.handlers) == 0

    def test_register_event_handler(self):
        """Can register event handler"""
        bus = EventBus()
        called = []

        def handler(data):
            called.append(data)

        bus.on('test_event', handler)
        assert 'test_event' in bus.handlers
        assert bus.count_handlers('test_event') == 1

    def test_emit_event_sync(self):
        """Can emit event synchronously"""
        bus = EventBus()
        results = []

        def handler(data):
            results.append(data['value'])

        bus.on('test_event', handler)
        bus.emit_sync('test_event', {'value': 42})

        assert len(results) == 1
        assert results[0] == 42

    def test_multiple_handlers(self):
        """Multiple handlers can be registered"""
        bus = EventBus()
        results = []

        def handler1(data):
            results.append('handler1')

        def handler2(data):
            results.append('handler2')

        bus.on('test_event', handler1)
        bus.on('test_event', handler2)

        bus.emit_sync('test_event', {})

        assert len(results) == 2
        assert 'handler1' in results
        assert 'handler2' in results

    def test_event_priority(self):
        """Handlers execute in priority order"""
        bus = EventBus()
        results = []

        def low_priority(data):
            results.append('low')

        def high_priority(data):
            results.append('high')

        bus.on('test_event', low_priority, EventPriority.LOW)
        bus.on('test_event', high_priority, EventPriority.HIGH)

        bus.emit_sync('test_event', {})

        # High priority should execute first
        assert results[0] == 'high'
        assert results[1] == 'low'


class TestHookManager:
    """Test HookManager basic functionality"""

    def test_hook_manager_creation(self):
        """HookManager can be instantiated"""
        hm = HookManager()
        assert hm is not None
        assert len(hm.hooks) == 0

    def test_register_hook(self):
        """Can register a hook"""
        hm = HookManager()

        def hook_func(data, context):
            return data

        hm.register(HookPoint.PRE_ANALYSIS, hook_func)
        assert hm.has_hooks(HookPoint.PRE_ANALYSIS)
        assert hm.count_hooks(HookPoint.PRE_ANALYSIS) == 1

    def test_execute_hook(self):
        """Can execute hooks"""
        hm = HookManager()

        def modify_hook(data, context):
            data['modified'] = True
            return data

        hm.register(HookPoint.PRE_ANALYSIS, modify_hook)

        result = hm.execute(HookPoint.PRE_ANALYSIS, {'original': True})

        assert result['original'] is True
        assert result['modified'] is True

    def test_hook_chain(self):
        """Multiple hooks chain together"""
        hm = HookManager()

        def hook1(data, context):
            data['step1'] = True
            return data

        def hook2(data, context):
            data['step2'] = True
            return data

        hm.register(HookPoint.PRE_ANALYSIS, hook1)
        hm.register(HookPoint.PRE_ANALYSIS, hook2)

        result = hm.execute(HookPoint.PRE_ANALYSIS, {})

        assert result['step1'] is True
        assert result['step2'] is True

    def test_hook_with_no_return(self):
        """Hooks that don't return still work"""
        hm = HookManager()

        def side_effect_hook(data, context):
            # Modifies in place, doesn't return
            data['modified'] = True

        hm.register(HookPoint.PRE_ANALYSIS, side_effect_hook)

        result = hm.execute(HookPoint.PRE_ANALYSIS, {})
        assert result['modified'] is True


class TestPluginLoadingBasic:
    """Basic tests for plugin loading"""

    def test_plugin_manager_loads_from_directory(self, mock_system, tmp_path):
        """PluginManager can scan directory"""
        pm = PluginManager(mock_system)

        # Directory doesn't exist - should handle gracefully
        pm.load_from_directory(tmp_path / "nonexistent")

        # Should not crash
        assert len(pm.plugins) == 0

    def test_health_check_empty(self, mock_system):
        """Health check works with no plugins"""
        pm = PluginManager(mock_system)
        health = pm.health_check()
        assert health == {}


# Mark this as basic unit tests
pytestmark = pytest.mark.unit
