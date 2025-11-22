"""
ARGO Plugin System - Base Classes
Defines abstract base classes and protocols for plugins
"""

from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class PluginCapability(Enum):
    """Plugin capabilities"""
    ANALYZER = "analyzer"
    EXTRACTOR = "extractor"
    EVALUATOR = "evaluator"
    TRANSFORMER = "transformer"
    EXPORTER = "exporter"
    INTELLIGENCE = "intelligence"  # For advanced RAG features


@dataclass
class PluginMetadata:
    """Metadata for plugins"""
    name: str
    version: str
    author: str = "ARGO Team"
    description: str = ""
    capabilities: List[PluginCapability] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True
    loaded_at: Optional[datetime] = None


@dataclass
class AnalysisResult:
    """Standard result from any analyzer"""
    status: str  # 'success', 'error', 'partial'
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0

    @property
    def is_success(self) -> bool:
        return self.status == 'success'

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


class Plugin(Protocol):
    """
    Protocol for ARGO plugins
    All plugins must implement this interface
    """
    metadata: PluginMetadata

    def initialize(self, system: Any) -> None:
        """
        Initialize plugin with ARGO system

        Args:
            system: ARGOBootstrap instance
        """
        ...

    def shutdown(self) -> None:
        """Cleanup on plugin shutdown"""
        ...

    def health_check(self) -> bool:
        """Check if plugin is healthy"""
        ...


class BaseAnalyzer(ABC):
    """
    Base class for all analyzers

    This provides the common interface that all analyzer plugins must implement.
    Examples: Excel analyzer, XER analyzer, Image OCR analyzer, etc.
    """

    def __init__(self):
        self._initialized = False
        self._metadata = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique analyzer name (e.g., 'excel_analyzer', 'ocr_analyzer')"""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """File extensions supported (e.g., ['.xlsx', '.xls', '.csv'])"""
        pass

    @property
    def version(self) -> str:
        """Analyzer version"""
        return "1.0.0"

    @property
    def description(self) -> str:
        """Human-readable description"""
        return f"{self.name} analyzer"

    def can_handle(self, file_path: str) -> bool:
        """
        Check if this analyzer can handle the given file

        Args:
            file_path: Path to file

        Returns:
            True if this analyzer supports the file type
        """
        path = Path(file_path)
        return path.suffix.lower() in self.supported_formats

    def validate(self, file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate file before analysis

        Args:
            file_path: Path to file

        Returns:
            (is_valid, error_message)
        """
        path = Path(file_path)

        if not path.exists():
            return False, f"File not found: {file_path}"

        if not path.is_file():
            return False, f"Not a file: {file_path}"

        if not self.can_handle(file_path):
            return False, f"Unsupported format: {path.suffix}"

        return True, None

    @abstractmethod
    def analyze(self, file_path: str, options: Optional[Dict] = None) -> AnalysisResult:
        """
        Perform analysis on file

        Args:
            file_path: Path to file to analyze
            options: Optional analysis options

        Returns:
            AnalysisResult with analysis data
        """
        pass

    def pre_analyze(self, file_path: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Hook called before analysis
        Override to perform pre-processing

        Returns:
            Preprocessed data or empty dict
        """
        return {}

    def post_analyze(self, result: AnalysisResult) -> AnalysisResult:
        """
        Hook called after analysis
        Override to perform post-processing

        Args:
            result: Analysis result

        Returns:
            Modified or original result
        """
        return result


class BaseExtractor(ABC):
    """Base class for extractors"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        pass

    @abstractmethod
    def extract(self, file_path: str) -> str:
        """Extract text content from file"""
        pass


class BaseEvaluator(ABC):
    """Base class for evaluators (e.g., DCMA, GAO)"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def metrics(self) -> List[str]:
        """List of metrics this evaluator assesses"""
        pass

    @abstractmethod
    def evaluate(self, data: Dict[str, Any]) -> AnalysisResult:
        """Evaluate data against metrics"""
        pass


class BaseIntelligencePlugin(ABC):
    """Base class for intelligence enhancement plugins"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def capability(self) -> str:
        """e.g., 'corrective_rag', 'query_planning', 'self_reflection'"""
        pass

    @abstractmethod
    async def enhance(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance query or results"""
        pass
