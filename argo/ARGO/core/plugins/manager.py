"""
ARGO Plugin Manager
Handles plugin discovery, loading, and lifecycle management
"""

import importlib.util
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from datetime import datetime

from .base import (
    Plugin,
    BaseAnalyzer,
    BaseExtractor,
    BaseEvaluator,
    BaseIntelligencePlugin,
    PluginMetadata,
    PluginCapability
)
from .events import EventBus
from .hooks import HookManager

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages ARGO plugins

    Responsibilities:
    - Auto-discover plugins from directories
    - Load and initialize plugins
    - Manage plugin lifecycle
    - Route requests to appropriate plugins
    - Handle plugin dependencies
    """

    def __init__(self, system: Any):
        """
        Initialize plugin manager

        Args:
            system: ARGOBootstrap instance
        """
        self.system = system
        self.plugins: Dict[str, Plugin] = {}
        self.analyzers: Dict[str, BaseAnalyzer] = {}
        self.extractors: Dict[str, BaseExtractor] = {}
        self.evaluators: Dict[str, BaseEvaluator] = {}
        self.intelligence_plugins: Dict[str, BaseIntelligencePlugin] = {}

        # Event and hook systems
        self.events = EventBus()
        self.hooks = HookManager()

        # Plugin metadata
        self.metadata: Dict[str, PluginMetadata] = {}

        logger.info("✅ PluginManager initialized")

    def load_from_directory(self, plugin_dir: Path, pattern: str = "*_plugin.py"):
        """
        Auto-discover and load plugins from directory

        Args:
            plugin_dir: Directory to search for plugins
            pattern: Glob pattern for plugin files

        Example:
            plugins/
            ├── ocr_plugin.py
            ├── excel_plugin.py
            └── schedule_plugin.py
        """
        plugin_dir = Path(plugin_dir)

        if not plugin_dir.exists():
            logger.warning(f"Plugin directory does not exist: {plugin_dir}")
            return

        logger.info(f"🔍 Searching for plugins in: {plugin_dir}")

        for plugin_file in plugin_dir.glob(pattern):
            try:
                self._load_plugin_from_file(plugin_file)
            except Exception as e:
                logger.error(f"❌ Failed to load plugin {plugin_file.name}: {e}")

    def _load_plugin_from_file(self, plugin_file: Path):
        """Load a plugin from a Python file"""
        logger.debug(f"Loading plugin from: {plugin_file}")

        # Import module
        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load spec for {plugin_file}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find plugin class (should have 'Plugin' suffix)
        plugin_classes = [
            obj for name, obj in inspect.getmembers(module, inspect.isclass)
            if name.endswith('Plugin') and hasattr(obj, 'metadata')
        ]

        if not plugin_classes:
            logger.warning(f"No plugin class found in {plugin_file.name}")
            return

        # Instantiate and register plugin
        for plugin_class in plugin_classes:
            try:
                plugin = plugin_class()
                self.register_plugin(plugin)
            except Exception as e:
                logger.error(f"Failed to instantiate {plugin_class.__name__}: {e}")

    def register_plugin(self, plugin: Plugin):
        """
        Register a plugin

        Args:
            plugin: Plugin instance
        """
        name = plugin.metadata.name

        if name in self.plugins:
            logger.warning(f"Plugin {name} already registered, skipping")
            return

        try:
            # Initialize plugin
            plugin.initialize(self.system)

            # Store plugin
            self.plugins[name] = plugin
            self.metadata[name] = plugin.metadata
            self.metadata[name].loaded_at = datetime.now()

            logger.info(
                f"✅ Plugin registered: {name} v{plugin.metadata.version} "
                f"[{', '.join([c.value for c in plugin.metadata.capabilities])}]"
            )

            # Emit event
            self.events.emit_sync('plugin_loaded', {'plugin': name})

        except Exception as e:
            logger.error(f"❌ Failed to initialize plugin {name}: {e}")
            raise

    def register_analyzer(self, analyzer: BaseAnalyzer):
        """
        Register an analyzer plugin

        Args:
            analyzer: BaseAnalyzer instance
        """
        name = analyzer.name

        if name in self.analyzers:
            logger.warning(f"Analyzer {name} already registered, replacing")

        self.analyzers[name] = analyzer
        logger.info(
            f"✅ Analyzer registered: {name} "
            f"[formats: {', '.join(analyzer.supported_formats)}]"
        )

    def register_extractor(self, extractor: BaseExtractor):
        """Register an extractor"""
        self.extractors[extractor.name] = extractor
        logger.info(f"✅ Extractor registered: {extractor.name}")

    def register_evaluator(self, evaluator: BaseEvaluator):
        """Register an evaluator"""
        self.evaluators[evaluator.name] = evaluator
        logger.info(f"✅ Evaluator registered: {evaluator.name}")

    def register_intelligence_plugin(self, plugin: BaseIntelligencePlugin):
        """Register an intelligence enhancement plugin"""
        self.intelligence_plugins[plugin.name] = plugin
        logger.info(f"✅ Intelligence plugin registered: {plugin.name} [{plugin.capability}]")

    def get_analyzer(self, file_path: str) -> Optional[BaseAnalyzer]:
        """
        Get appropriate analyzer for a file

        Args:
            file_path: Path to file

        Returns:
            Analyzer that can handle the file, or None
        """
        for analyzer in self.analyzers.values():
            if analyzer.can_handle(file_path):
                logger.debug(f"Found analyzer {analyzer.name} for {file_path}")
                return analyzer

        logger.debug(f"No analyzer found for {file_path}")
        return None

    def get_extractor(self, file_path: str) -> Optional[BaseExtractor]:
        """Get appropriate extractor for a file"""
        path = Path(file_path)
        ext = path.suffix.lower()

        for extractor in self.extractors.values():
            if ext in extractor.supported_formats:
                return extractor

        return None

    def get_evaluator(self, name: str) -> Optional[BaseEvaluator]:
        """Get evaluator by name"""
        return self.evaluators.get(name)

    def get_intelligence_plugin(self, capability: str) -> Optional[BaseIntelligencePlugin]:
        """Get intelligence plugin by capability"""
        for plugin in self.intelligence_plugins.values():
            if plugin.capability == capability:
                return plugin
        return None

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all loaded plugins

        Returns:
            List of plugin info dicts
        """
        return [
            {
                'name': meta.name,
                'version': meta.version,
                'author': meta.author,
                'description': meta.description,
                'capabilities': [c.value for c in meta.capabilities],
                'enabled': meta.enabled,
                'loaded_at': meta.loaded_at.isoformat() if meta.loaded_at else None
            }
            for meta in self.metadata.values()
        ]

    def list_analyzers(self) -> List[Dict[str, Any]]:
        """List all registered analyzers"""
        return [
            {
                'name': analyzer.name,
                'version': analyzer.version,
                'description': analyzer.description,
                'formats': analyzer.supported_formats
            }
            for analyzer in self.analyzers.values()
        ]

    def enable_plugin(self, name: str):
        """Enable a plugin"""
        if name in self.metadata:
            self.metadata[name].enabled = True
            logger.info(f"✅ Plugin enabled: {name}")

    def disable_plugin(self, name: str):
        """Disable a plugin"""
        if name in self.metadata:
            self.metadata[name].enabled = False
            logger.info(f"⏸️ Plugin disabled: {name}")

    def shutdown_all(self):
        """Shutdown all plugins"""
        logger.info("Shutting down all plugins...")

        for name, plugin in self.plugins.items():
            try:
                plugin.shutdown()
                logger.debug(f"Plugin {name} shutdown successfully")
            except Exception as e:
                logger.error(f"Error shutting down plugin {name}: {e}")

        logger.info("All plugins shutdown")

    def health_check(self) -> Dict[str, bool]:
        """
        Check health of all plugins

        Returns:
            Dict mapping plugin names to health status
        """
        health = {}

        for name, plugin in self.plugins.items():
            try:
                health[name] = plugin.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                health[name] = False

        return health
