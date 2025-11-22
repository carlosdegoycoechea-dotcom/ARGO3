"""
Excel Analyzer Plugin for ARGO
Advanced analysis of Excel spreadsheets

Capabilities:
- Detect headers automatically
- Analyze data types
- Generate summary statistics
- Detect formulas
- Identify empty cells
- Advanced PMO metrics (optional)

Dependencies:
- pandas
- openpyxl
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

try:
    import pandas as pd
    import numpy as np
    HAS_EXCEL = True
except ImportError:
    HAS_EXCEL = False

from core.plugins import (
    Plugin,
    BaseAnalyzer,
    AnalysisResult,
    PluginMetadata,
    PluginCapability
)

logger = logging.getLogger(__name__)


class ExcelPluginAnalyzer(BaseAnalyzer):
    """
    Excel analyzer with advanced capabilities
    Refactored from core/tools/analyzers/excel_analyzer.py
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.pmo_mode = self.config.get('pmo_mode', False)

    @property
    def name(self) -> str:
        return "excel_analyzer"

    @property
    def supported_formats(self) -> List[str]:
        return ['.xlsx', '.xls', '.xlsm', '.csv']

    @property
    def version(self) -> str:
        return "2.0.0"  # Plugin version

    @property
    def description(self) -> str:
        return "Advanced Excel spreadsheet analysis with optional PMO metrics"

    def validate(self, file_path: str) -> tuple[bool, Optional[str]]:
        """Validate Excel file"""
        is_valid, error = super().validate(file_path)

        if not is_valid:
            return False, error

        if not HAS_EXCEL:
            return False, "Excel dependencies not installed (pandas, openpyxl)"

        return True, None

    def analyze(self, file_path: str, options: Optional[Dict] = None) -> AnalysisResult:
        """
        Analyze Excel file

        Options:
            - sheet: Specific sheet name to analyze
            - all_sheets: Analyze all sheets (default: True)
            - pmo_mode: Enable PMO-specific analysis
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

        options = options or {}
        sheet_name = options.get('sheet')
        all_sheets = options.get('all_sheets', True)
        pmo_mode = options.get('pmo_mode', self.pmo_mode)

        try:
            path = Path(file_path)

            # Load Excel file
            if path.suffix.lower() == '.csv':
                analysis = self._analyze_csv(file_path)
            else:
                analysis = self._analyze_excel(file_path, sheet_name, all_sheets, pmo_mode)

            execution_time = (time.time() - start_time) * 1000

            return AnalysisResult(
                status='success',
                data=analysis,
                metadata={
                    'analyzer': self.name,
                    'version': self.version,
                    'pmo_mode': pmo_mode,
                    'file_name': path.name
                },
                execution_time_ms=execution_time
            )

        except Exception as e:
            return AnalysisResult(
                status='error',
                data={},
                errors=[f"Excel analysis failed: {str(e)}"],
                execution_time_ms=(time.time() - start_time) * 1000
            )

    def _analyze_csv(self, file_path: str) -> Dict[str, Any]:
        """Analyze CSV file"""
        df = pd.read_csv(file_path)

        return {
            'file_type': 'CSV',
            'sheets': {
                'main': self._analyze_dataframe(df, 'main')
            }
        }

    def _analyze_excel(self, file_path: str, sheet_name: Optional[str], all_sheets: bool, pmo_mode: bool) -> Dict[str, Any]:
        """Analyze Excel workbook"""
        excel_file = pd.ExcelFile(file_path)

        analysis = {
            'file_type': 'Excel',
            'sheet_names': excel_file.sheet_names,
            'sheet_count': len(excel_file.sheet_names),
            'sheets': {}
        }

        # Determine which sheets to analyze
        if sheet_name:
            sheets_to_analyze = [sheet_name] if sheet_name in excel_file.sheet_names else []
        elif all_sheets:
            sheets_to_analyze = excel_file.sheet_names
        else:
            sheets_to_analyze = [excel_file.sheet_names[0]] if excel_file.sheet_names else []

        # Analyze each sheet
        for sheet in sheets_to_analyze:
            df = pd.read_excel(file_path, sheet_name=sheet, header=None)
            analysis['sheets'][sheet] = self._analyze_dataframe(df, sheet, pmo_mode)

        return analysis

    def _analyze_dataframe(self, df: pd.DataFrame, sheet_name: str, pmo_mode: bool = False) -> Dict[str, Any]:
        """Analyze a single DataFrame"""
        # Detect headers
        header_row = self._detect_headers(df)

        if header_row is not None:
            df.columns = df.iloc[header_row]
            df = df[header_row + 1:].reset_index(drop=True)

        analysis = {
            'dimensions': {
                'rows': len(df),
                'columns': len(df.columns)
            },
            'columns': list(df.columns),
            'header_row': header_row,
            'data_types': self._analyze_data_types(df),
            'summary_stats': self._get_summary_stats(df),
            'empty_cells': self._count_empty_cells(df),
            'formulas_detected': False  # Would need openpyxl for this
        }

        # Add PMO-specific analysis if enabled
        if pmo_mode:
            analysis['pmo_metrics'] = self._analyze_pmo_metrics(df)

        return analysis

    def _detect_headers(self, df: pd.DataFrame) -> Optional[int]:
        """Detect header row"""
        if df.empty:
            return None

        # Check first few rows for header patterns
        for i in range(min(5, len(df))):
            row = df.iloc[i]

            # Count non-null string values
            string_count = sum(1 for val in row if isinstance(val, str) and val.strip())

            # If most values are strings, likely a header
            if string_count / len(row) > 0.7:
                return i

        return None

    def _analyze_data_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """Analyze data types of columns"""
        types = {}

        for col in df.columns:
            dtype = df[col].dtype

            if pd.api.types.is_numeric_dtype(dtype):
                types[str(col)] = 'numeric'
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                types[str(col)] = 'datetime'
            elif pd.api.types.is_bool_dtype(dtype):
                types[str(col)] = 'boolean'
            else:
                types[str(col)] = 'text'

        return types

    def _get_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics for numeric columns"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) == 0:
            return {}

        stats = df[numeric_cols].describe().to_dict()

        # Convert to serializable format
        return {
            str(col): {str(k): float(v) if not pd.isna(v) else None for k, v in vals.items()}
            for col, vals in stats.items()
        }

    def _count_empty_cells(self, df: pd.DataFrame) -> Dict[str, int]:
        """Count empty cells per column"""
        return {
            str(col): int(df[col].isna().sum())
            for col in df.columns
        }

    def _analyze_pmo_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze PMO-specific metrics (if columns detected)

        Looks for standard PMO columns like:
        - Activity ID, Activity Name
        - Start Date, Finish Date
        - Duration, % Complete
        - Baseline Start, Baseline Finish
        - Total Float, Free Float
        """
        pmo_metrics = {
            'schedule_detected': False,
            'metrics': {}
        }

        # Normalize column names for detection
        cols_lower = {str(col).lower(): col for col in df.columns}

        # Check for schedule-related columns
        schedule_indicators = [
            'activity', 'task', 'wbs',
            'start', 'finish', 'duration',
            'baseline', 'float', 'complete'
        ]

        has_schedule = any(
            any(ind in col for ind in schedule_indicators)
            for col in cols_lower.keys()
        )

        if has_schedule:
            pmo_metrics['schedule_detected'] = True

            # Try to calculate basic metrics
            if 'duration' in cols_lower:
                dur_col = cols_lower['duration']
                if pd.api.types.is_numeric_dtype(df[dur_col]):
                    pmo_metrics['metrics']['total_duration'] = float(df[dur_col].sum())
                    pmo_metrics['metrics']['avg_duration'] = float(df[dur_col].mean())

            # Count activities
            pmo_metrics['metrics']['activity_count'] = len(df)

            # Check for completion tracking
            for key in cols_lower.keys():
                if 'complete' in key or 'progress' in key:
                    col = cols_lower[key]
                    if pd.api.types.is_numeric_dtype(df[col]):
                        pmo_metrics['metrics']['avg_complete'] = float(df[col].mean())
                        break

        return pmo_metrics


class ExcelPlugin(Plugin):
    """
    Excel Analysis Plugin for ARGO

    Provides advanced Excel spreadsheet analysis capabilities
    """

    def __init__(self):
        self.metadata = PluginMetadata(
            name="excel_analyzer",
            version="2.0.0",
            author="ARGO Team",
            description="Advanced Excel spreadsheet analysis with PMO metrics",
            capabilities=[PluginCapability.ANALYZER],
            dependencies=["pandas", "openpyxl", "numpy"],
            enabled=True
        )
        self.analyzer = None
        self.system = None

    def initialize(self, system):
        """Initialize Excel plugin"""
        self.system = system

        if not HAS_EXCEL:
            logger.warning(
                "⚠️ Excel plugin dependencies not installed. "
                "Install with: pip install pandas openpyxl numpy"
            )
            return

        # Get config
        config = {}
        if hasattr(system, 'config'):
            config = system.config.get('excel', {})

        # Create analyzer
        self.analyzer = ExcelPluginAnalyzer(config)

        # Register analyzer
        system.plugins.register_analyzer(self.analyzer)

        # Register event handlers
        system.plugins.events.on('document_uploaded', self.on_document_uploaded)

        logger.info("✅ Excel analyzer plugin initialized successfully")

    def on_document_uploaded(self, data: Dict):
        """Auto-analyze Excel files when uploaded"""
        file_path = data.get('file_path')

        if not file_path or not self.analyzer:
            return

        if self.analyzer.can_handle(file_path):
            logger.info(f"📊 Auto-Excel analysis triggered for: {file_path}")

            try:
                result = self.analyzer.analyze(file_path)

                if result.is_success:
                    logger.info(f"✅ Excel analysis completed")

                    # Emit event
                    self.system.plugins.events.emit_sync(
                        'excel_analyzed',
                        {
                            'file_path': file_path,
                            'analysis': result.data
                        }
                    )
                else:
                    logger.error(f"❌ Excel analysis failed: {result.errors}")

            except Exception as e:
                logger.error(f"❌ Auto-Excel analysis error: {e}")

    def shutdown(self):
        """Cleanup"""
        logger.info("Excel analyzer plugin shutdown")

    def health_check(self) -> bool:
        """Health check"""
        return HAS_EXCEL
