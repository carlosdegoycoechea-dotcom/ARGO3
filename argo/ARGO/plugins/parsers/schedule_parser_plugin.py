"""
Universal Schedule Parser Plugin for ARGO
Automatically detects and routes to appropriate parser (XER or XML)

This is the main entry point for schedule parsing - it intelligently
detects the file format and delegates to the correct specialized parser.

Supported formats:
- Primavera P6 XER files (.xer)
- Microsoft Project XML files (.xml)

Usage:
    # The plugin manager will automatically route based on file extension
    result = analyzer.analyze("schedule.xer")  # Routes to XER parser
    result = analyzer.analyze("project.xml")   # Routes to XML parser
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from core.plugins import (
    Plugin,
    BaseAnalyzer,
    AnalysisResult,
    PluginMetadata,
    PluginCapability
)

logger = logging.getLogger(__name__)


class ScheduleParserAnalyzer(BaseAnalyzer):
    """
    Universal Schedule Parser - Auto-detects format and routes to correct parser

    This analyzer acts as a facade/router for schedule parsing,
    automatically detecting whether a file is XER or XML and
    delegating to the appropriate specialized parser.
    """

    def __init__(self, system, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.system = system
        self.xer_parser = None
        self.xml_parser = None

    @property
    def name(self) -> str:
        return "schedule_parser"

    @property
    def supported_formats(self) -> List[str]:
        return ['.xer', '.xml']

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Universal schedule parser - auto-detects XER or XML format"

    def validate(self, file_path: str) -> tuple[bool, Optional[str]]:
        """Validate schedule file"""
        is_valid, error = super().validate(file_path)

        if not is_valid:
            return False, error

        if not HAS_PANDAS:
            return False, "pandas not installed. Install with: pip install pandas"

        # Get appropriate parser
        parser = self._get_parser_for_file(file_path)

        if parser is None:
            return False, f"No parser available for file: {Path(file_path).suffix}"

        # Delegate validation to specialized parser
        return parser.validate(file_path)

    def analyze(self, file_path: str, options: Optional[Dict] = None) -> AnalysisResult:
        """
        Parse and analyze schedule file (auto-detect format)

        Options:
            - extract_all: Extract all data (default: True)
            - projects_only: Only extract project info (default: False)
            - calculate_metrics: Calculate schedule metrics (default: True)
        """
        start_time = time.time()

        # Validate
        is_valid, error = self.validate(file_path)
        if not is_valid:
            return AnalysisResult(
                status='error',
                data={},
                errors=[error]
            )

        try:
            path = Path(file_path)
            logger.info(f"Universal schedule parser analyzing: {path.name}")

            # Get appropriate parser
            parser = self._get_parser_for_file(file_path)

            if parser is None:
                return AnalysisResult(
                    status='error',
                    data={},
                    errors=[f"No parser available for {path.suffix} files"]
                )

            # Delegate to specialized parser
            logger.info(f"Routing to {parser.name} for {path.suffix} file")
            result = parser.analyze(file_path, options)

            # Add routing metadata
            if result.is_success:
                result.metadata['routed_to'] = parser.name
                result.metadata['universal_parser_version'] = self.version

            return result

        except Exception as e:
            logger.error(f"Universal schedule parser failed: {e}", exc_info=True)
            return AnalysisResult(
                status='error',
                data={},
                errors=[f"Schedule parsing failed: {str(e)}"],
                execution_time_ms=(time.time() - start_time) * 1000
            )

    def _get_parser_for_file(self, file_path: str) -> Optional[BaseAnalyzer]:
        """
        Get appropriate parser based on file extension

        Returns:
            XER or XML parser, or None if not available
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        # Get parsers from plugin manager
        if self.xer_parser is None and hasattr(self.system, 'plugins'):
            self.xer_parser = self.system.plugins.analyzers.get('xer_parser')

        if self.xml_parser is None and hasattr(self.system, 'plugins'):
            self.xml_parser = self.system.plugins.analyzers.get('xml_parser')

        # Route based on extension
        if ext == '.xer':
            return self.xer_parser
        elif ext == '.xml':
            return self.xml_parser

        return None

    def get_available_parsers(self) -> List[str]:
        """Get list of available schedule parsers"""
        parsers = []

        if self.xer_parser is not None:
            parsers.append('xer_parser')

        if self.xml_parser is not None:
            parsers.append('xml_parser')

        return parsers


class ScheduleParserPlugin(Plugin):
    """
    Universal Schedule Parser Plugin for ARGO

    Provides automatic schedule parsing with format detection
    """

    def __init__(self):
        self.metadata = PluginMetadata(
            name="schedule_parser",
            version="1.0.0",
            author="ARGO Development Team",
            description="Universal schedule parser with auto-detection (XER/XML)",
            capabilities=[PluginCapability.ANALYZER],
            dependencies=["pandas"],
            enabled=True
        )
        self.analyzer = None
        self.system = None

    def initialize(self, system):
        """Initialize universal schedule parser plugin"""
        self.system = system

        if not HAS_PANDAS:
            logger.warning(
                "⚠️ pandas not installed. "
                "Install with: pip install pandas"
            )
            return

        # Get config
        config = {}
        if hasattr(system, 'config'):
            config = system.config.get('schedule_parser', {})

        # Create analyzer (pass system for accessing other parsers)
        self.analyzer = ScheduleParserAnalyzer(system, config)

        # Register analyzer
        system.plugins.register_analyzer(self.analyzer)

        # Register event handlers
        system.plugins.events.on('document_uploaded', self.on_document_uploaded)

        logger.info("✅ Universal schedule parser plugin initialized successfully")

    def on_document_uploaded(self, data: Dict):
        """Auto-analyze schedule files when uploaded"""
        file_path = data.get('file_path')

        if not file_path or not self.analyzer:
            return

        if self.analyzer.can_handle(file_path):
            logger.info(f"📊 Auto-schedule analysis triggered for: {file_path}")

            try:
                result = self.analyzer.analyze(file_path)

                if result.is_success:
                    logger.info(f"✅ Schedule analysis completed")

                    # Emit event
                    self.system.plugins.events.emit_sync(
                        'schedule_analyzed',
                        {
                            'file_path': file_path,
                            'analysis': result.data,
                            'parser_used': result.metadata.get('routed_to')
                        }
                    )
                else:
                    logger.error(f"❌ Schedule analysis failed: {result.errors}")

            except Exception as e:
                logger.error(f"❌ Auto-schedule analysis error: {e}")

    def shutdown(self):
        """Cleanup"""
        logger.info("Universal schedule parser plugin shutdown")

    def health_check(self) -> bool:
        """Health check"""
        return HAS_PANDAS and self.analyzer is not None
