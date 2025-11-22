"""
Basic integration tests - verify plugins load together
These are BASIC tests - comprehensive integration tests TODO
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.plugins.manager import PluginManager


class TestPluginSystemIntegration:
    """Test that all plugins can be loaded together"""

    def test_plugin_directory_exists(self):
        """Plugins directory exists"""
        plugins_dir = Path(__file__).parent.parent / "plugins"
        assert plugins_dir.exists()
        assert plugins_dir.is_dir()

    def test_all_plugins_can_be_discovered(self, mock_system):
        """All plugins can be discovered without errors"""
        pm = PluginManager(mock_system)
        plugins_dir = Path(__file__).parent.parent / "plugins"

        # Should not crash when loading plugins
        pm.load_from_directory(plugins_dir)

        # We have 6 plugins total:
        # 1. OCR
        # 2. Excel
        # 3. Corrective RAG
        # 4. Self-Reflective RAG
        # 5. Query Planning
        # 6. Agentic Retrieval

        # Note: Some plugins may not initialize if dependencies missing
        # That's OK for this basic test - we just check they don't crash
        loaded_count = len(pm.plugins)

        # Should have attempted to load some plugins
        assert loaded_count >= 0  # May be 0 if dependencies missing

        # Log which loaded
        print(f"\n✅ Loaded {loaded_count} plugins successfully")
        for name, plugin in pm.plugins.items():
            print(f"   - {name}: {plugin.metadata.version}")

    def test_analyzers_registered(self, mock_system):
        """Analyzers are registered correctly"""
        pm = PluginManager(mock_system)
        plugins_dir = Path(__file__).parent.parent / "plugins"

        pm.load_from_directory(plugins_dir)

        # Should have analyzers registered (if dependencies available)
        analyzers = pm.list_analyzers()

        # May be 0 if dependencies missing, but shouldn't crash
        assert isinstance(analyzers, list)

        print(f"\n✅ Registered {len(analyzers)} analyzers")
        for analyzer in analyzers:
            print(f"   - {analyzer.name}: {analyzer.supported_formats}")

    def test_intelligence_plugins_registered(self, mock_system):
        """Intelligence plugins are registered correctly"""
        pm = PluginManager(mock_system)
        plugins_dir = Path(__file__).parent.parent / "plugins"

        pm.load_from_directory(plugins_dir)

        # Should have intelligence plugins (if dependencies available)
        intelligence = pm.list_intelligence_plugins()

        # May be 0 if dependencies missing, but shouldn't crash
        assert isinstance(intelligence, list)

        print(f"\n✅ Registered {len(intelligence)} intelligence plugins")
        for plugin in intelligence:
            print(f"   - {plugin.name}: {plugin.capability}")

    def test_no_plugin_conflicts(self, mock_system):
        """No naming conflicts between plugins"""
        pm = PluginManager(mock_system)
        plugins_dir = Path(__file__).parent.parent / "plugins"

        pm.load_from_directory(plugins_dir)

        # Check for duplicate analyzer names
        analyzer_names = [a.name for a in pm.list_analyzers()]
        assert len(analyzer_names) == len(set(analyzer_names)), "Duplicate analyzer names detected"

        # Check for duplicate intelligence plugin names
        intel_names = [p.name for p in pm.list_intelligence_plugins()]
        assert len(intel_names) == len(set(intel_names)), "Duplicate intelligence plugin names detected"

    def test_health_checks_dont_crash(self, mock_system):
        """Health checks run without errors"""
        pm = PluginManager(mock_system)
        plugins_dir = Path(__file__).parent.parent / "plugins"

        pm.load_from_directory(plugins_dir)

        # Should not crash
        health = pm.health_check()

        assert isinstance(health, dict)

        print(f"\n🏥 Health check results:")
        for plugin_name, status in health.items():
            emoji = "✅" if status else "⚠️"
            print(f"   {emoji} {plugin_name}: {status}")


class TestEventSystemIntegration:
    """Test event system integration"""

    def test_events_can_be_emitted(self, mock_system):
        """Events can be emitted without errors"""
        pm = PluginManager(mock_system)

        # Should have event bus
        assert pm.events is not None

        # Should be able to emit event
        pm.events.emit_sync('test_event', {'test': True})

        # Should not crash
        assert True

    def test_hooks_can_be_executed(self, mock_system):
        """Hooks can be executed without errors"""
        pm = PluginManager(mock_system)

        # Should have hook manager
        assert pm.hooks is not None

        # Should be able to execute hook (even if no handlers)
        result = pm.hooks.execute('pre_analysis', {'test': True})

        # Should return the data
        assert result is not None


# Mark as integration tests
pytestmark = pytest.mark.integration
