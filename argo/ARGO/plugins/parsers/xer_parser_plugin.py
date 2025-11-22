"""
XER Parser Plugin for ARGO
Parses Primavera P6 XER files using PyP6Xer (100% Python native)

Capabilities:
- Parse XER files from Primavera P6
- Extract projects, activities, relationships, resources, calendars
- Calculate critical path and float
- Generate comprehensive schedule metrics
- Normalize data to pandas DataFrames

Dependencies:
- PyP6XER (xerparser)
- pandas
- python-dateutil
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
from datetime import datetime

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from xerparser import Xer
    HAS_XERPARSER = True
except ImportError:
    HAS_XERPARSER = False

from core.plugins import (
    Plugin,
    BaseAnalyzer,
    AnalysisResult,
    PluginMetadata,
    PluginCapability
)

logger = logging.getLogger(__name__)


class XERParserAnalyzer(BaseAnalyzer):
    """
    XER Parser Analyzer for Primavera P6 files

    Parses XER files and extracts:
    - Projects and metadata
    - Activities/Tasks with durations, dates, progress
    - Resources and assignments
    - Calendars
    - Relationships (predecessors/successors) with lags
    - WBS codes
    - Float calculations
    - Critical path identification

    Supported XER versions: 15.2, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.encoding = self.config.get('encoding', 'cp1252')  # Default Windows encoding for XER
        self.xer_data = None

    @property
    def name(self) -> str:
        return "xer_parser"

    @property
    def supported_formats(self) -> List[str]:
        return ['.xer']

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Parser para archivos Primavera P6 XER usando PyP6Xer"

    def validate(self, file_path: str) -> tuple[bool, Optional[str]]:
        """Validate XER file"""
        is_valid, error = super().validate(file_path)

        if not is_valid:
            return False, error

        if not HAS_XERPARSER:
            return False, "PyP6XER not installed. Install with: pip install PyP6XER"

        if not HAS_PANDAS:
            return False, "pandas not installed. Install with: pip install pandas"

        # Check if file has XER format signature
        try:
            with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
                first_line = f.readline()
                if not first_line.startswith('ERMHDR'):
                    return False, "File is not a valid XER format (missing ERMHDR header)"
        except Exception as e:
            return False, f"Cannot read file: {str(e)}"

        return True, None

    def analyze(self, file_path: str, options: Optional[Dict] = None) -> AnalysisResult:
        """
        Parse and analyze XER file

        Options:
            - extract_all: Extract all data (default: True)
            - projects_only: Only extract project info (default: False)
            - include_baseline: Include baseline data (default: False)
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

        options = options or {}
        extract_all = options.get('extract_all', True)
        projects_only = options.get('projects_only', False)
        calculate_metrics = options.get('calculate_metrics', True)

        try:
            path = Path(file_path)
            logger.info(f"Parsing XER file: {path.name}")

            # Parse XER file
            xer = Xer(str(file_path))
            self.xer_data = xer

            # Structure base result
            result = {
                "format": "XER",
                "file_path": str(file_path),
                "file_name": path.name,
                "file_info": self._extract_file_info(xer)
            }

            # If only projects requested
            if projects_only:
                result["projects"] = self._extract_projects(xer)
                execution_time = (time.time() - start_time) * 1000

                return AnalysisResult(
                    status='success',
                    data=result,
                    metadata={
                        'analyzer': self.name,
                        'version': self.version,
                        'file_name': path.name
                    },
                    execution_time_ms=execution_time
                )

            # Full extraction
            if extract_all:
                result["projects"] = self._extract_projects(xer)
                result["activities"] = self._extract_activities(xer)
                result["relationships"] = self._extract_relationships(xer)
                result["resources"] = self._extract_resources(xer)
                result["calendars"] = self._extract_calendars(xer)

                if calculate_metrics:
                    result["stats"] = self._calculate_stats(xer, result)

            activities_count = len(result.get('activities', []))
            logger.info(f"✅ XER parsed successfully: {activities_count} activities")

            execution_time = (time.time() - start_time) * 1000

            return AnalysisResult(
                status='success',
                data=result,
                metadata={
                    'analyzer': self.name,
                    'version': self.version,
                    'file_name': path.name,
                    'encoding': self.encoding
                },
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"XER parsing failed: {e}", exc_info=True)
            return AnalysisResult(
                status='error',
                data={},
                errors=[f"XER parsing failed: {str(e)}"],
                execution_time_ms=(time.time() - start_time) * 1000
            )

    # ==================== EXTRACTORS ====================

    def _extract_file_info(self, xer: Xer) -> Dict[str, Any]:
        """Extract XER file metadata"""
        return {
            "export_date": xer.export_date.isoformat() if xer.export_date else None,
            "export_user": xer.export_user if hasattr(xer, 'export_user') else None,
            "export_version": xer.export_version if hasattr(xer, 'export_version') else None,
            "encoding": self.encoding,
            "file_type": "Primavera P6 XER"
        }

    def _extract_projects(self, xer: Xer) -> List[Dict[str, Any]]:
        """Extract project information"""
        projects = []

        for project in xer.projects:
            proj_dict = {
                "project_id": project.proj_id if hasattr(project, 'proj_id') else None,
                "project_code": project.proj_short_name if hasattr(project, 'proj_short_name') else None,
                "project_name": project.proj_name if hasattr(project, 'proj_name') else None,
                "start_date": project.plan_start_date.isoformat() if hasattr(project, 'plan_start_date') and project.plan_start_date else None,
                "finish_date": project.plan_end_date.isoformat() if hasattr(project, 'plan_end_date') and project.plan_end_date else None,
                "data_date": project.last_recalc_date.isoformat() if hasattr(project, 'last_recalc_date') and project.last_recalc_date else None,
                "total_activities": len(project.activities) if hasattr(project, 'activities') else 0,
                "status": project.proj_status if hasattr(project, 'proj_status') else None
            }
            projects.append(proj_dict)

        return projects

    def _extract_activities(self, xer: Xer) -> pd.DataFrame:
        """
        Extract all activities as normalized DataFrame

        Columns:
        - activity_id, activity_code, activity_name
        - duration_days, start_date, finish_date
        - percent_complete, status
        - total_float_days, free_float_days
        - is_critical, wbs_id, calendar_id
        - project_id
        """
        activities_data = []

        for project in xer.projects:
            if not hasattr(project, 'activities'):
                continue

            for activity in project.activities:
                # Convert hours to days (P6 uses hours internally)
                duration_days = (activity.target_drtn_hr_cnt / 8.0) if hasattr(activity, 'target_drtn_hr_cnt') and activity.target_drtn_hr_cnt else 0.0
                total_float_days = (activity.total_float_hr_cnt / 8.0) if hasattr(activity, 'total_float_hr_cnt') and activity.total_float_hr_cnt else None
                free_float_days = (activity.free_float_hr_cnt / 8.0) if hasattr(activity, 'free_float_hr_cnt') and activity.free_float_hr_cnt else None

                # Determine if critical (float <= 0)
                is_critical = total_float_days is not None and total_float_days <= 0

                activity_dict = {
                    # Identification
                    "activity_id": activity.task_id if hasattr(activity, 'task_id') else None,
                    "activity_code": activity.task_code if hasattr(activity, 'task_code') else None,
                    "activity_name": activity.task_name if hasattr(activity, 'task_name') else None,

                    # Duration and dates
                    "duration_days": duration_days,
                    "start_date": activity.act_start_date.isoformat() if hasattr(activity, 'act_start_date') and activity.act_start_date else None,
                    "finish_date": activity.act_end_date.isoformat() if hasattr(activity, 'act_end_date') and activity.act_end_date else None,
                    "early_start": activity.early_start_date.isoformat() if hasattr(activity, 'early_start_date') and activity.early_start_date else None,
                    "early_finish": activity.early_end_date.isoformat() if hasattr(activity, 'early_end_date') and activity.early_end_date else None,
                    "late_start": activity.late_start_date.isoformat() if hasattr(activity, 'late_start_date') and activity.late_start_date else None,
                    "late_finish": activity.late_end_date.isoformat() if hasattr(activity, 'late_end_date') and activity.late_end_date else None,

                    # Progress and status
                    "percent_complete": activity.phys_complete_pct if hasattr(activity, 'phys_complete_pct') and activity.phys_complete_pct else 0.0,
                    "status": activity.status_code if hasattr(activity, 'status_code') else None,

                    # Float and criticality
                    "total_float_days": total_float_days,
                    "free_float_days": free_float_days,
                    "is_critical": is_critical,

                    # References
                    "wbs_id": activity.wbs_id if hasattr(activity, 'wbs_id') else None,
                    "calendar_id": activity.clndr_id if hasattr(activity, 'clndr_id') else None,
                    "project_id": project.proj_id if hasattr(project, 'proj_id') else None,

                    # Type
                    "task_type": activity.task_type if hasattr(activity, 'task_type') else None,

                    # Constraint
                    "constraint_type": activity.cstr_type if hasattr(activity, 'cstr_type') else None,
                    "constraint_date": activity.cstr_date.isoformat() if hasattr(activity, 'cstr_date') and activity.cstr_date else None
                }
                activities_data.append(activity_dict)

        df = pd.DataFrame(activities_data)

        # Convert dates to datetime
        date_columns = ['start_date', 'finish_date', 'early_start', 'early_finish',
                       'late_start', 'late_finish', 'constraint_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        return df

    def _extract_relationships(self, xer: Xer) -> pd.DataFrame:
        """
        Extract relationships between activities

        Columns:
        - predecessor_id, successor_id
        - relationship_type (PR_FS, PR_SS, PR_FF, PR_SF)
        - lag_days
        """
        relationships_data = []

        if hasattr(xer, 'taskpreds'):
            for relationship in xer.taskpreds:
                # Convert lag from hours to days
                lag_days = (relationship.lag_hr_cnt / 8.0) if hasattr(relationship, 'lag_hr_cnt') and relationship.lag_hr_cnt else 0.0

                rel_dict = {
                    "predecessor_id": relationship.pred_task_id if hasattr(relationship, 'pred_task_id') else None,
                    "successor_id": relationship.task_id if hasattr(relationship, 'task_id') else None,
                    "relationship_type": relationship.pred_type if hasattr(relationship, 'pred_type') else None,
                    "lag_days": lag_days
                }
                relationships_data.append(rel_dict)

        return pd.DataFrame(relationships_data)

    def _extract_resources(self, xer: Xer) -> pd.DataFrame:
        """Extract resources"""
        resources_data = []

        if hasattr(xer, 'resources'):
            for resource in xer.resources:
                res_dict = {
                    "resource_id": resource.rsrc_id if hasattr(resource, 'rsrc_id') else None,
                    "resource_name": resource.rsrc_name if hasattr(resource, 'rsrc_name') else None,
                    "resource_type": resource.rsrc_type if hasattr(resource, 'rsrc_type') else None,
                    "parent_id": resource.parent_rsrc_id if hasattr(resource, 'parent_rsrc_id') else None
                }
                resources_data.append(res_dict)

        return pd.DataFrame(resources_data)

    def _extract_calendars(self, xer: Xer) -> List[Dict[str, Any]]:
        """Extract calendar information"""
        calendars = []

        if hasattr(xer, 'calendars'):
            for calendar in xer.calendars:
                cal_dict = {
                    "calendar_id": calendar.clndr_id if hasattr(calendar, 'clndr_id') else None,
                    "calendar_name": calendar.clndr_name if hasattr(calendar, 'clndr_name') else None,
                    "is_default": calendar.default_flag if hasattr(calendar, 'default_flag') else False,
                    "hours_per_day": calendar.day_hr_cnt if hasattr(calendar, 'day_hr_cnt') else 8.0
                }
                calendars.append(cal_dict)

        return calendars

    def _calculate_stats(self, xer: Xer, result: Dict) -> Dict[str, Any]:
        """Calculate schedule statistics"""
        activities_df = result.get('activities')

        if activities_df is None or len(activities_df) == 0:
            return {}

        # Filter active activities (not completed)
        active_activities = activities_df[activities_df['status'] != 'TK_Complete']

        stats = {
            "total_projects": len(xer.projects) if hasattr(xer, 'projects') else 0,
            "total_activities": len(activities_df),
            "active_activities": len(active_activities),
            "completed_activities": len(activities_df[activities_df['status'] == 'TK_Complete']),
            "total_resources": len(xer.resources) if hasattr(xer, 'resources') else 0,
            "total_calendars": len(xer.calendars) if hasattr(xer, 'calendars') else 0,
            "total_relationships": len(result.get('relationships', [])),

            # Criticality
            "critical_activities": int(activities_df['is_critical'].sum()),
            "critical_path_length": float(activities_df[activities_df['is_critical'] == True]['duration_days'].sum()),

            # Progress
            "average_completion": float(activities_df['percent_complete'].mean()),

            # Float
            "activities_with_negative_float": len(active_activities[active_activities['total_float_days'] < 0]),
            "activities_with_high_float": len(active_activities[active_activities['total_float_days'] > 44]),
        }

        return stats

    def get_critical_path_activities(self) -> pd.DataFrame:
        """
        Get only critical path activities

        Requires having executed analyze() first
        """
        if self.xer_data is None:
            raise RuntimeError("No XER data loaded. Execute analyze() first.")

        activities_df = self._extract_activities(self.xer_data)
        critical = activities_df[activities_df['is_critical'] == True]

        return critical.sort_values('start_date')


class XERParserPlugin(Plugin):
    """
    XER Parser Plugin for ARGO

    Provides Primavera P6 XER file parsing capabilities
    """

    def __init__(self):
        self.metadata = PluginMetadata(
            name="xer_parser",
            version="1.0.0",
            author="ARGO Development Team",
            description="Parser para archivos Primavera P6 XER usando PyP6Xer",
            capabilities=[PluginCapability.ANALYZER],
            dependencies=["xerparser", "pandas", "python-dateutil"],
            enabled=True
        )
        self.analyzer = None
        self.system = None

    def initialize(self, system):
        """Initialize XER parser plugin"""
        self.system = system

        if not HAS_XERPARSER:
            logger.warning(
                "⚠️ PyP6XER not installed. "
                "Install with: pip install PyP6XER"
            )
            return

        if not HAS_PANDAS:
            logger.warning(
                "⚠️ pandas not installed. "
                "Install with: pip install pandas"
            )
            return

        # Get config
        config = {}
        if hasattr(system, 'config'):
            config = system.config.get('xer_parser', {})

        # Create analyzer
        self.analyzer = XERParserAnalyzer(config)

        # Register analyzer
        system.plugins.register_analyzer(self.analyzer)

        # Register event handlers
        system.plugins.events.on('document_uploaded', self.on_document_uploaded)

        logger.info("✅ XER parser plugin initialized successfully")

    def on_document_uploaded(self, data: Dict):
        """Auto-analyze XER files when uploaded"""
        file_path = data.get('file_path')

        if not file_path or not self.analyzer:
            return

        if self.analyzer.can_handle(file_path):
            logger.info(f"📊 Auto-XER analysis triggered for: {file_path}")

            try:
                result = self.analyzer.analyze(file_path)

                if result.is_success:
                    logger.info(f"✅ XER analysis completed")

                    # Emit event
                    self.system.plugins.events.emit_sync(
                        'xer_analyzed',
                        {
                            'file_path': file_path,
                            'analysis': result.data
                        }
                    )
                else:
                    logger.error(f"❌ XER analysis failed: {result.errors}")

            except Exception as e:
                logger.error(f"❌ Auto-XER analysis error: {e}")

    def shutdown(self):
        """Cleanup"""
        logger.info("XER parser plugin shutdown")

    def health_check(self) -> bool:
        """Health check"""
        return HAS_XERPARSER and HAS_PANDAS
