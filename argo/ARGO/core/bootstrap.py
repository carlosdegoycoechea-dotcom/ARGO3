"""
ARGO - Unified Bootstrap System
Single initialization path for the entire system
Consolidates v8.0 base + F1 extensions into one clean architecture
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from core.config import get_config
from core.logger import get_logger, initialize_logging, LogMessages
from core.unified_database import UnifiedDatabase
from core.model_router import ModelRouter
from core.llm_provider import LLMProviderManager
from core.plugins.manager import PluginManager

logger = get_logger("Bootstrap")


class ARGOBootstrap:
    """
    Unified ARGO bootstrap system
    
    Initializes:
    - Configuration
    - Logging
    - Unified Database
    - Model Router (GPT + Claude)
    - Project components (vectorstore, RAG)
    - Library Manager
    - Watchers and monitors
    """
    
    def __init__(self):
        self.config = None
        self.unified_db = None
        self.model_router = None
        self.library_manager = None
        self.plugins = None
        self.active_project = None
        self.initialized = False
    
    def initialize(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize complete ARGO system
        
        Args:
            project_name: Project to activate (None = use default)
        
        Returns:
            Dict with all initialized components
        """
        start_time = datetime.now()
        
        # Phase 1: Configuration
        logger.info("=" * 70)
        logger.info("ARGO Enterprise Platform - Initialization")
        logger.info("=" * 70)
        
        self.config = get_config()
        logger.info(LogMessages.system_ready("Configuration"))
        logger.info(f"Version: {self.config.version_display}")
        
        # Phase 2: Logging system
        log_dir = Path(self.config.get("paths.logs_dir"))
        log_level = self.config.get("logging.level", "INFO")
        initialize_logging(log_dir, log_level)
        logger.info(LogMessages.system_ready("Logging"))
        
        # Phase 3: Unified Database
        logger.info(LogMessages.system_init("Unified Database"))
        self.unified_db = self._init_unified_database()
        logger.info(LogMessages.system_ready("Unified Database"))
        
        # Phase 4: Model Router
        logger.info(LogMessages.system_init("Model Router"))
        self.model_router = self._init_model_router()
        logger.info(LogMessages.system_ready("Model Router"))
        
        # Phase 5: Library Manager
        logger.info(LogMessages.system_init("Library Manager"))
        self.library_manager = self._init_library_manager()
        logger.info(LogMessages.system_ready("Library Manager"))
        
        # Phase 6: Ensure project exists
        if not project_name:
            project_name = os.getenv("PROJECT_NAME", "DEFAULT_PROJECT")
        
        logger.info(LogMessages.system_init(f"Project: {project_name}"))
        project = self._ensure_project_exists(project_name)
        self.active_project = project  # Store for plugins
        logger.info(f"Active project: {project['name']} ({project['project_type']})")

        # Phase 7: Initialize project components
        logger.info(LogMessages.system_init("Project Components"))
        project_components = self._init_project_components(project)
        logger.info(LogMessages.system_ready("Project Components"))

        # Phase 7.5: Initialize Plugin System
        logger.info(LogMessages.system_init("Plugin System"))
        self.plugins = self._init_plugins()
        logger.info(LogMessages.system_ready("Plugin System"))

        # Phase 8: Watchers (optional)
        watchers = None
        if self.config.get("monitoring.enabled", True):
            logger.info(LogMessages.system_init("Monitoring"))
            watchers = self._init_watchers(project)
            logger.info(LogMessages.system_ready("Monitoring"))
        
        self.initialized = True
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 70)
        logger.info(f"ARGO initialized successfully in {duration:.2f}s")
        logger.info("=" * 70)
        
        return {
            'config': self.config,
            'unified_db': self.unified_db,
            'model_router': self.model_router,
            'library_manager': self.library_manager,
            'plugins': self.plugins,
            'project': project,
            'project_components': project_components,
            'watchers': watchers,
            'version': self.config.version,
            'initialized_at': datetime.now().isoformat()
        }
    
    def _init_unified_database(self) -> UnifiedDatabase:
        """Initialize unified database"""
        db_path = Path(self.config.get("database.unified_db"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        unified_db = UnifiedDatabase(db_path)
        logger.debug(f"Database location: {db_path}")
        
        return unified_db
    
    def _init_model_router(self) -> ModelRouter:
        """
        Initialize Model Router
        This is the ONLY way to call LLMs - no direct instantiation allowed
        """
        # Get API keys (verificar que existan en .env)
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        if not openai_key:
            raise ValueError("OPENAI_API_KEY required in .env")

        # Initialize provider manager
        provider_manager = LLMProviderManager(config=self.config)

        # Create RouterConfig from settings
        from core.model_router import RouterConfig
        router_config = RouterConfig(
            pricing=self.config.get('pricing', {}),
            budget=self.config.get('budget', {}),
            defaults=self.config.get('router_defaults', {})
        )

        # Create router - ModelRouter expects providers dict, not provider_manager
        router = ModelRouter(
            providers=provider_manager.providers,  # Pass the providers dict
            config=router_config,                   # Pass RouterConfig, not general config
            db_manager=self.unified_db
        )

        logger.debug(
            f"Model Router: OpenAI={'enabled' if openai_key else 'disabled'}, "
            f"Anthropic={'enabled' if anthropic_key else 'disabled'}"
        )

        return router
    
    def _init_library_manager(self):
        """Initialize Library Manager"""
        from core.library_manager import LibraryManager
        
        base_path = Path(self.config.get("paths.data_dir"))
        
        lib_manager = LibraryManager(
            db_manager=self.unified_db,
            base_path=base_path
        )
        
        logger.debug(f"Library path: {lib_manager.library_path}")
        
        # Initialize Drive sync if enabled
        if self.config.get("apis.google_drive.enabled", False):
            try:
                from tools.google_drive_sync import create_drive_sync
                
                drive_sync = create_drive_sync(self.unified_db, self.config)
                
                if drive_sync and drive_sync.is_available():
                    logger.info("Google Drive sync initialized and available")
                    lib_manager.drive_sync = drive_sync
                else:
                    logger.info("Google Drive sync not available")
            except Exception as e:
                logger.warning(f"Could not initialize Drive sync: {e}")
        
        return lib_manager
    
    def _ensure_project_exists(self, project_name: str) -> Dict[str, Any]:
        """
        Ensure project exists in database
        
        Args:
            project_name: Name of project
        
        Returns:
            Project dict
        """
        # Check if exists
        existing = self.unified_db.get_project(name=project_name)
        
        if existing:
            # Update last accessed
            self.unified_db.update_project(
                existing['id'],
                last_accessed=datetime.now().isoformat()
            )
            return existing
        
        # Create new project
        project_path = Path(self.config.get("paths.projects_dir")) / project_name
        project_path.mkdir(parents=True, exist_ok=True)
        
        project_id = self.unified_db.create_project(
            name=project_name,
            base_path=f"projects/{project_name}",
            description=f"Project {project_name}",
            project_type="standard",
            metadata={
                "created_via": "bootstrap",
                "full_path": str(project_path)
            }
        )
        
        logger.info(f"Created new project: {project_name}")
        
        return self.unified_db.get_project(project_id=project_id)
    
    def _init_project_components(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize project-specific components
        
        Args:
            project: Project dict from database
        
        Returns:
            Dict with project components
        """
        project_path = Path(self.config.root_path) / project['base_path']
        
        # Create directories
        (project_path / "vectors").mkdir(parents=True, exist_ok=True)
        (project_path / "cache").mkdir(parents=True, exist_ok=True)
        (project_path / "reports").mkdir(parents=True, exist_ok=True)
        
        # Initialize vectorstore
        vectorstore = self._init_vectorstore(project_path, "project")
        
        # Initialize library vectorstore
        library_path = Path(self.config.get("paths.library_cache"))
        library_vectorstore = self._init_vectorstore(library_path, "library")
        
        # Initialize RAG engine
        rag_engine = self._init_rag_engine(
            project_vectorstore=vectorstore,
            library_vectorstore=library_vectorstore,
            project=project
        )
        
        return {
            'project_path': project_path,
            'vectorstore': vectorstore,
            'library_vectorstore': library_vectorstore,
            'rag_engine': rag_engine
        }
    
    def _init_vectorstore(self, base_path: Path, collection_name: str):
        """
        Initialize Chroma vectorstore
        
        Args:
            base_path: Base path for vectors
            collection_name: Name of collection
        
        Returns:
            Chroma vectorstore
        """
        from langchain_chroma import Chroma
        from langchain_openai import OpenAIEmbeddings
        
        embeddings_model = self.config.get("apis.openai.models.embeddings", "text-embedding-3-small")
        
        embeddings = OpenAIEmbeddings(
            model=embeddings_model,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        vectors_path = base_path / "vectors"
        vectors_path.mkdir(parents=True, exist_ok=True)
        
        vectorstore = Chroma(
            persist_directory=str(vectors_path),
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        return vectorstore
    
    def _init_rag_engine(self, project_vectorstore, library_vectorstore, project: Dict):
        """
        Initialize unified RAG engine
        
        Args:
            project_vectorstore: Vectorstore for project documents
            library_vectorstore: Vectorstore for library documents
            project: Project dict
        
        Returns:
            RAG engine instance
        """
        from core.rag_engine import UnifiedRAGEngine
        
        # Get embeddings
        from langchain_openai import OpenAIEmbeddings
        embeddings_model = self.config.get("apis.openai.models.embeddings")
        
        embeddings = OpenAIEmbeddings(
            model=embeddings_model,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        rag_engine = UnifiedRAGEngine(
            project_vectorstore=project_vectorstore,
            library_vectorstore=library_vectorstore,
            embeddings=embeddings,
            model_router=self.model_router,
            config=self.config,
            project_id=project['id']
        )
        
        return rag_engine
    
    def _init_watchers(self, project: Dict):
        """Initialize monitoring watchers"""
        try:
            from monitoring.watchers import WatcherManager

            watchers = WatcherManager(
                unified_db=self.unified_db,
                config=self.config,
                project_id=project['id']
            )

            return watchers
        except ImportError:
            logger.warning("Watchers module not found, monitoring disabled")
            return None

    def _init_plugins(self) -> PluginManager:
        """
        Initialize Plugin System

        Loads all plugins from the plugins directory.
        Plugins are auto-discovered based on *_plugin.py naming pattern.

        Returns:
            PluginManager instance with all plugins loaded
        """
        try:
            # Create plugin manager
            plugin_manager = PluginManager(self)

            # Get plugins directory from config or use default
            plugins_dir = self.config.get("plugins.directory")
            if plugins_dir:
                plugins_path = Path(plugins_dir)
            else:
                # Default: ARGO/plugins
                base_dir = Path(__file__).parent.parent
                plugins_path = base_dir / "plugins"

            # Load plugins if directory exists
            if plugins_path.exists():
                logger.info(f"Loading plugins from: {plugins_path}")
                plugin_manager.load_from_directory(plugins_path)

                # Log loaded plugins
                plugins_list = plugin_manager.list_plugins()
                if plugins_list:
                    logger.info(f"Loaded {len(plugins_list)} plugins:")
                    for plugin in plugins_list:
                        logger.info(f"  - {plugin['name']} v{plugin['version']}")
                else:
                    logger.info("No plugins loaded")
            else:
                logger.info(f"Plugins directory not found: {plugins_path}")
                logger.info("Plugin system initialized but no plugins loaded")

            return plugin_manager

        except Exception as e:
            logger.error(f"Plugin system initialization failed: {e}")
            logger.warning("Continuing without plugins")
            # Return empty plugin manager so system doesn't break
            return PluginManager(self)


# Singleton instance
_bootstrap_instance = None


def get_bootstrap() -> ARGOBootstrap:
    """Get singleton bootstrap instance"""
    global _bootstrap_instance
    if _bootstrap_instance is None:
        _bootstrap_instance = ARGOBootstrap()
    return _bootstrap_instance


def initialize_argo(project_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize ARGO system
    
    This is the ONLY initialization function.
    No initialize_argo_f1, no initialize_argo_v8, etc.
    
    Args:
        project_name: Name of project to activate
    
    Returns:
        Dict with all system components
    
    Example:
        argo = initialize_argo("MY_PROJECT")
        model_router = argo['model_router']
        rag_engine = argo['project_components']['rag_engine']
        unified_db = argo['unified_db']
    """
    bootstrap = get_bootstrap()
    return bootstrap.initialize(project_name)


# Validation: No other initialization functions should exist
def _validate_single_initialization_path():
    """
    RULE ENFORCEMENT:
    
    This is the ONLY initialization function for ARGO.
    No other modules should have initialize_argo_xxx() functions.
    
    All initialization MUST go through initialize_argo().
    
    Benefits:
    1. Single source of truth
    2. Predictable initialization order
    3. Easy to debug
    4. No confusion about which init to call
    5. Clean architecture
    """
    pass
