"""
ARGO Plugin System
Arquitectura extensible para módulos plug & play
"""

from .base import (
    Plugin,
    BaseAnalyzer,
    AnalysisResult,
    PluginMetadata,
    PluginCapability
)
from .manager import PluginManager
from .events import EventBus, Event
from .hooks import HookManager, HookPoint

__all__ = [
    'Plugin',
    'BaseAnalyzer',
    'AnalysisResult',
    'PluginMetadata',
    'PluginCapability',
    'PluginManager',
    'EventBus',
    'Event',
    'HookManager',
    'HookPoint'
]

__version__ = '1.0.0'
