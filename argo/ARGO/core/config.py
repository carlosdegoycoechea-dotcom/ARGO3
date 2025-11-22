"""
ARGO - Configuration Manager
Unified configuration loading from settings.yaml and .env
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass


class Config:
    """
    Unified configuration manager
    
    Loads from:
    1. config/settings.yaml (structure and defaults)
    2. .env (secrets and API keys)
    3. Environment variables (override)
    """
    
    _instance = None
    _config: Dict[str, Any] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """Load configuration from all sources"""
        # 1. Find root directory
        current = Path(__file__).resolve()
        root = current.parent.parent
        
        # 2. Load .env
        env_file = root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        
        # 3. Load settings.yaml
        settings_file = root / "config" / "settings.yaml"
        if not settings_file.exists():
            raise ConfigurationError(f"settings.yaml not found at {settings_file}")
        
        with open(settings_file, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        # 4. Inject API keys from environment
        self._inject_api_keys()
        
        # 5. Expand paths to absolute
        self._expand_paths(root)
        
        # 6. Validate required configuration
        self._validate()
    
    def _inject_api_keys(self):
        """Inject API keys from environment variables"""
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self._config["apis"]["openai"]["api_key"] = openai_key
            self._config["apis"]["openai"]["enabled"] = True
        else:
            self._config["apis"]["openai"]["api_key"] = None
            self._config["apis"]["openai"]["enabled"] = False
        
        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self._config["apis"]["anthropic"]["api_key"] = anthropic_key
            self._config["apis"]["anthropic"]["enabled"] = True
        else:
            self._config["apis"]["anthropic"]["api_key"] = None
            self._config["apis"]["anthropic"]["enabled"] = False
        
        # Google Drive folder ID
        drive_folder = os.getenv("LIBRARY_DRIVE_FOLDER_ID")
        if drive_folder:
            self._config["apis"]["google_drive"]["library_folder_id"] = drive_folder
    
    def _expand_paths(self, root: Path):
        """Convert relative paths to absolute"""
        for key in ["data_dir", "projects_dir", "library_cache", "logs_dir", "temp_dir"]:
            if key in self._config["paths"]:
                rel_path = self._config["paths"][key]
                self._config["paths"][key] = str(root / rel_path)
        
        # Database path
        db_path = self._config["database"]["unified_db"]
        self._config["database"]["unified_db"] = str(root / db_path)
        
        # Credentials file
        creds_file = self._config["apis"]["google_drive"]["credentials_file"]
        creds_path = root / creds_file
        if creds_path.exists():
            self._config["apis"]["google_drive"]["credentials_file"] = str(creds_path)
            self._config["apis"]["google_drive"]["enabled"] = True
    
    def _validate(self):
        """Validate required configuration"""
        # At least one LLM provider must be enabled
        if not self._config["apis"]["openai"]["enabled"] and \
           not self._config["apis"]["anthropic"]["enabled"]:
            raise ConfigurationError(
                "No LLM provider enabled. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env"
            )
        
        # OpenAI is required for embeddings (for now)
        if not self._config["apis"]["openai"]["enabled"]:
            raise ConfigurationError(
                "OpenAI is required for embeddings. Set OPENAI_API_KEY in .env"
            )
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Example:
            config.get("apis.openai.api_key")
            config.get("rag.chunking.default_chunk_size", 1000)
        """
        keys = key_path.split(".")
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self._config.get(section, {})
    
    @property
    def all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self._config.copy()
    
    @property
    def version(self) -> str:
        """Get version string"""
        v = self._config["version"]
        return f"{v['major']}.{v['minor']}.{v['patch']}"
    
    @property
    def version_display(self) -> str:
        """Get display version string"""
        return self._config["version"]["display_name"]
    
    @property
    def root_path(self) -> Path:
        """Get project root path"""
        return Path(__file__).resolve().parent.parent
    
    def is_openai_enabled(self) -> bool:
        """Check if OpenAI is configured"""
        return self._config["apis"]["openai"]["enabled"]
    
    def is_anthropic_enabled(self) -> bool:
        """Check if Anthropic is configured"""
        return self._config["apis"]["anthropic"]["enabled"]
    
    def is_drive_enabled(self) -> bool:
        """Check if Google Drive is configured"""
        return self._config["apis"]["google_drive"]["enabled"]
    
    def get_model_for_task(self, task_type: str, prefer_provider: Optional[str] = None) -> Dict[str, str]:
        """
        Get model configuration for a task type
        
        Args:
            task_type: Type of task (chat, analysis, summary, etc.)
            prefer_provider: Preferred provider (openai, anthropic)
        
        Returns:
            Dict with provider, model, temperature
        """
        routing = self._config["model_router"]["task_routing"]
        
        if task_type not in routing:
            # Fallback to chat
            task_type = "chat"
        
        task_config = routing[task_type].copy()
        
        # Override with preferred provider if specified and available
        if prefer_provider:
            if prefer_provider == "anthropic" and self.is_anthropic_enabled():
                task_config["provider"] = "anthropic"
                task_config["model"] = self._config["apis"]["anthropic"]["default_model"]
            elif prefer_provider == "openai" and self.is_openai_enabled():
                task_config["provider"] = "openai"
                # Keep model from task routing
        
        return task_config
    
    def get_pricing(self, provider: str, model: str) -> Dict[str, float]:
        """
        Get pricing for a model
        
        Returns:
            Dict with 'input' and 'output' prices per 1K tokens
        """
        pricing = self._config["budget"]["pricing"]
        
        if provider in pricing and model in pricing[provider]:
            return pricing[provider][model]
        
        # Default fallback
        return {"input": 0.0, "output": 0.0}
    
    def reload(self):
        """Reload configuration from disk"""
        self._config = None
        self._load_config()


# Global singleton instance
_config_instance = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reload_config():
    """Reload configuration from disk"""
    global _config_instance
    if _config_instance:
        _config_instance.reload()
