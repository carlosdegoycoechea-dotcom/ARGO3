"""
ARGO Core Modules
Unified architecture without version suffixes
"""

__version__ = "9.0.0"
__codename__ = "Clean"

from .config import get_config, Config
from .logger import get_logger, initialize_logging

__all__ = [
    'get_config',
    'Config',
    'get_logger',
    'initialize_logging',
]
