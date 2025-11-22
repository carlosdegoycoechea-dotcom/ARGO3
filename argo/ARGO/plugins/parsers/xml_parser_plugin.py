"""
XML Parser Plugin for ARGO
Parses Microsoft Project XML files (MSPDI format)
100% Python native using ElementTree (built-in)

Capabilities:
- Parse MS Project XML (MSPDI - Microsoft Project Data Interchange)
- Extract projects, tasks, resources, relationships, calendars
- Normalize data to pandas DataFrames (compatible with XER parser)
- Support MS Project 2007-2021 XML format

Dependencies:
- pandas (already installed)
- xml.etree.ElementTree (built-in Python)
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
import xml.etree.ElementTree as ET

try:
    import pandas as pd
    import numpy as np
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


class XMLParserAnalyzer(BaseAnalyzer):
    """
    XML Parser Analyzer for MS Project files

    Parses MS Project XML (MSPDI format) and extracts:
    - Projects and metadata
    - Tasks with durations, dates, progress
    - Resources and assignments
    - Relationships between tasks (predecessors/successors)
    - WBS (Work Breakdown Structure)
    - Calendars

    Supported format: MS Project 2007-2021 XML
    """

    # Namespace for MS Project XML
    NS = {'ms': 'http://schemas.microsoft.com/project'}

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.tree = None
        self.root = None

    @property
    def name(self) -> str:
        return "xml_parser"

    @property
    def supported_formats(self) -> List[str]:
        return ['.xml']

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Parser para MS Project XML usando ElementTree nativo"

    def validate(self, file_path: str) -> tuple[bool, Optional[str]]:
        """Validate MS Project XML file"""
        is_valid, error = super().validate(file_path)

        if not is_valid:
            return False, error

        if not HAS_PANDAS:
            return False, "pandas not installed. Install with: pip install pandas"

        # Check if file is MS Project XML
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Verify it's MS Project XML
            if 'microsoft.com/project' not in root.tag:
                return False, "XML is not MS Project format (MSPDI)"

            return True, None

        except ET.ParseError as e:
            return False, f"Malformed XML: {str(e)}"
        except Exception as e:
            return False, f"Cannot read file: {str(e)}"

    def analyze(self, file_path: str, options: Optional[Dict] = None) -> AnalysisResult:
        """
        Parse and analyze MS Project XML file

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

        options = options or {}
        extract_all = options.get('extract_all', True)
        projects_only = options.get('projects_only', False)
        calculate_metrics = options.get('calculate_metrics', True)

        try:
            path = Path(file_path)
            logger.info(f"Parsing XML file: {path.name}")

            # Parse XML
            self.tree = ET.parse(file_path)
            self.root = self.tree.getroot()

            # Structure base result
            result = {
                "format": "MS Project XML",
                "file_path": str(file_path),
                "file_name": path.name,
                "file_info": self._extract_file_info()
            }

            # If only projects requested
            if projects_only:
                result["projects"] = self._extract_projects()
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
                result["projects"] = self._extract_projects()
                result["activities"] = self._extract_activities()
                result["relationships"] = self._extract_relationships()
                result["resources"] = self._extract_resources()
                result["calendars"] = self._extract_calendars()

                if calculate_metrics:
                    result["stats"] = self._calculate_stats(result)

            activities_count = len(result.get('activities', []))
            logger.info(f"✅ XML parsed successfully: {activities_count} tasks")

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

        except Exception as e:
            logger.error(f"XML parsing failed: {e}", exc_info=True)
            return AnalysisResult(
                status='error',
                data={},
                errors=[f"XML parsing failed: {str(e)}"],
                execution_time_ms=(time.time() - start_time) * 1000
            )

    # ==================== EXTRACTORS ====================

    def _extract_file_info(self) -> Dict[str, Any]:
        """Extract XML file metadata"""
        return {
            "creation_date": self._get_text('.//ms:CreationDate'),
            "last_saved": self._get_text('.//ms:LastSaved'),
            "author": self._get_text('.//ms:Author'),
            "company": self._get_text('.//ms:Company'),
            "save_version": self._get_text('.//ms:SaveVersion'),
            "file_type": "Microsoft Project XML (MSPDI)"
        }

    def _extract_projects(self) -> List[Dict[str, Any]]:
        """Extract project information"""
        projects = [{
            "project_id": 1,  # MS Project XML typically has 1 project per file
            "project_code": self._get_text('.//ms:Title') or "Untitled",
            "project_name": self._get_text('.//ms:Title') or "Untitled Project",
            "start_date": self._get_text('.//ms:StartDate'),
            "finish_date": self._get_text('.//ms:FinishDate'),
            "data_date": self._get_text('.//ms:StatusDate'),
            "total_activities": len(self.root.findall('.//ms:Task', self.NS)),
            "status": self._get_text('.//ms:Status')
        }]

        return projects

    def _extract_activities(self) -> pd.DataFrame:
        """
        Extract all tasks as normalized DataFrame

        Structure compatible with XER parser
        """
        activities_data = []

        for task in self.root.findall('.//ms:Task', self.NS):
            # IDs and names
            task_id = self._get_text_from_element(task, 'ms:UID')
            task_name = self._get_text_from_element(task, 'ms:Name')

            # Duration (MS Project uses PT...H format - ISO 8601 duration)
            duration_text = self._get_text_from_element(task, 'ms:Duration')
            duration_days = self._parse_duration(duration_text)

            # Dates
            start_date = self._get_text_from_element(task, 'ms:Start')
            finish_date = self._get_text_from_element(task, 'ms:Finish')

            # Progress
            percent_complete = self._get_float_from_element(task, 'ms:PercentComplete')

            # WBS
            wbs = self._get_text_from_element(task, 'ms:WBS')
            outline_level = self._get_int_from_element(task, 'ms:OutlineLevel')

            # Constraint
            constraint_type = self._get_text_from_element(task, 'ms:ConstraintType')
            constraint_date = self._get_text_from_element(task, 'ms:ConstraintDate')

            # Milestone
            is_milestone = self._get_text_from_element(task, 'ms:Milestone') == '1'

            # Critical (in MS Project)
            is_critical = self._get_text_from_element(task, 'ms:Critical') == '1'

            activity_dict = {
                # Identification
                "activity_id": task_id,
                "activity_code": wbs or task_id,
                "activity_name": task_name,

                # Duration and dates
                "duration_days": duration_days,
                "start_date": start_date,
                "finish_date": finish_date,
                "early_start": None,  # MS Project doesn't expose directly
                "early_finish": None,
                "late_start": None,
                "late_finish": None,

                # Progress and status
                "percent_complete": percent_complete,
                "status": "Active" if percent_complete < 100 else "Complete",

                # Float and criticality
                "total_float_days": None,  # Could calculate if needed
                "free_float_days": None,
                "is_critical": is_critical,

                # References
                "wbs_id": wbs,
                "calendar_id": None,
                "project_id": 1,

                # Type
                "task_type": "Milestone" if is_milestone else "Task",

                # Constraint
                "constraint_type": self._map_constraint_type(constraint_type),
                "constraint_date": constraint_date,

                # Outline level
                "outline_level": outline_level
            }
            activities_data.append(activity_dict)

        df = pd.DataFrame(activities_data)

        # Convert dates to datetime
        date_columns = ['start_date', 'finish_date', 'constraint_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        return df

    def _extract_relationships(self) -> pd.DataFrame:
        """Extract relationships (predecessors) between tasks"""
        relationships_data = []

        for task in self.root.findall('.//ms:Task', self.NS):
            successor_id = self._get_text_from_element(task, 'ms:UID')

            # PredecessorLink can be multiple
            pred_links = task.findall('ms:PredecessorLink', self.NS)

            for pred_link in pred_links:
                predecessor_id = self._get_text_from_element(pred_link, 'ms:PredecessorUID')
                relationship_type = self._get_text_from_element(pred_link, 'ms:Type')

                # Lag in MS Project is in ISO 8601 duration format
                lag_text = self._get_text_from_element(pred_link, 'ms:LinkLag')
                lag_days = self._parse_duration(lag_text)

                rel_dict = {
                    "predecessor_id": predecessor_id,
                    "successor_id": successor_id,
                    "relationship_type": self._map_relationship_type(relationship_type),
                    "lag_days": lag_days
                }
                relationships_data.append(rel_dict)

        return pd.DataFrame(relationships_data)

    def _extract_resources(self) -> pd.DataFrame:
        """Extract resources"""
        resources_data = []

        for resource in self.root.findall('.//ms:Resource', self.NS):
            res_dict = {
                "resource_id": self._get_text_from_element(resource, 'ms:UID'),
                "resource_name": self._get_text_from_element(resource, 'ms:Name'),
                "resource_type": self._get_text_from_element(resource, 'ms:Type'),
                "parent_id": None
            }
            resources_data.append(res_dict)

        return pd.DataFrame(resources_data)

    def _extract_calendars(self) -> List[Dict[str, Any]]:
        """Extract calendar information"""
        calendars = []

        for calendar in self.root.findall('.//ms:Calendar', self.NS):
            cal_dict = {
                "calendar_id": self._get_text_from_element(calendar, 'ms:UID'),
                "calendar_name": self._get_text_from_element(calendar, 'ms:Name'),
                "is_default": self._get_text_from_element(calendar, 'ms:IsBaseCalendar') == '1',
                "hours_per_day": 8.0  # Default
            }
            calendars.append(cal_dict)

        return calendars

    def _calculate_stats(self, result: Dict) -> Dict[str, Any]:
        """Calculate schedule statistics"""
        activities_df = result.get('activities')

        if activities_df is None or len(activities_df) == 0:
            return {}

        active_activities = activities_df[activities_df['status'] != 'Complete']

        stats = {
            "total_projects": 1,
            "total_activities": len(activities_df),
            "active_activities": len(active_activities),
            "completed_activities": len(activities_df[activities_df['status'] == 'Complete']),
            "total_resources": len(result.get('resources', [])),
            "total_calendars": len(result.get('calendars', [])),
            "total_relationships": len(result.get('relationships', [])),

            # Criticality
            "critical_activities": int(activities_df['is_critical'].sum()),

            # Progress
            "average_completion": float(activities_df['percent_complete'].mean()),

            # Milestones
            "total_milestones": len(activities_df[activities_df['task_type'] == 'Milestone'])
        }

        return stats

    # ==================== HELPERS ====================

    def _get_text(self, xpath: str) -> str:
        """Helper to extract text via XPath"""
        element = self.root.find(xpath, self.NS)
        return element.text if element is not None else None

    def _get_text_from_element(self, element: ET.Element, tag: str) -> str:
        """Helper to extract text from sub-element"""
        sub_element = element.find(tag, self.NS)
        return sub_element.text if sub_element is not None else None

    def _get_float_from_element(self, element: ET.Element, tag: str) -> float:
        """Helper to extract float"""
        text = self._get_text_from_element(element, tag)
        try:
            return float(text) if text else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _get_int_from_element(self, element: ET.Element, tag: str) -> int:
        """Helper to extract int"""
        text = self._get_text_from_element(element, tag)
        try:
            return int(text) if text else 0
        except (ValueError, TypeError):
            return 0

    def _parse_duration(self, duration_text: str) -> float:
        """
        Parse ISO 8601 duration (PT...H) to days

        Example: PT80H0M0S = 80 hours = 10 days (8h/day)
        """
        if not duration_text:
            return 0.0

        try:
            # Typical format: PT80H0M0S
            if duration_text.startswith('PT') and 'H' in duration_text:
                hours_str = duration_text.split('PT')[1].split('H')[0]
                hours = float(hours_str)
                return hours / 8.0  # Convert to days (8h/day)
        except Exception as e:
            logger.warning(f"Could not parse duration: {duration_text}")

        return 0.0

    def _map_relationship_type(self, ms_type: str) -> str:
        """
        Map MS Project relationship type to P6 format

        MS Project: 0=FF, 1=FS, 2=SF, 3=SS
        P6: PR_FF, PR_FS, PR_SF, PR_SS
        """
        mapping = {
            '0': 'PR_FF',
            '1': 'PR_FS',
            '2': 'PR_SF',
            '3': 'PR_SS'
        }
        return mapping.get(ms_type, 'PR_FS')  # Default FS

    def _map_constraint_type(self, ms_constraint: str) -> str:
        """
        Map MS Project constraint type to generic format

        MS Project: 0=As Soon As Possible, 1=As Late As Possible,
                    2=Must Start On, 3=Must Finish On, etc.
        """
        mapping = {
            '0': 'ASAP',
            '1': 'ALAP',
            '2': 'MSO',   # Must Start On
            '3': 'MFO',   # Must Finish On
            '4': 'SNET',  # Start No Earlier Than
            '5': 'SNLT',  # Start No Later Than
            '6': 'FNET',  # Finish No Earlier Than
            '7': 'FNLT'   # Finish No Later Than
        }
        return mapping.get(ms_constraint, 'ASAP')


class XMLParserPlugin(Plugin):
    """
    XML Parser Plugin for ARGO

    Provides MS Project XML (MSPDI) file parsing capabilities
    """

    def __init__(self):
        self.metadata = PluginMetadata(
            name="xml_parser",
            version="1.0.0",
            author="ARGO Development Team",
            description="Parser para MS Project XML usando ElementTree nativo",
            capabilities=[PluginCapability.ANALYZER],
            dependencies=["pandas"],  # ElementTree is built-in
            enabled=True
        )
        self.analyzer = None
        self.system = None

    def initialize(self, system):
        """Initialize XML parser plugin"""
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
            config = system.config.get('xml_parser', {})

        # Create analyzer
        self.analyzer = XMLParserAnalyzer(config)

        # Register analyzer
        system.plugins.register_analyzer(self.analyzer)

        # Register event handlers
        system.plugins.events.on('document_uploaded', self.on_document_uploaded)

        logger.info("✅ XML parser plugin initialized successfully")

    def on_document_uploaded(self, data: Dict):
        """Auto-analyze XML files when uploaded"""
        file_path = data.get('file_path')

        if not file_path or not self.analyzer:
            return

        if self.analyzer.can_handle(file_path):
            logger.info(f"📊 Auto-XML analysis triggered for: {file_path}")

            try:
                result = self.analyzer.analyze(file_path)

                if result.is_success:
                    logger.info(f"✅ XML analysis completed")

                    # Emit event
                    self.system.plugins.events.emit_sync(
                        'xml_analyzed',
                        {
                            'file_path': file_path,
                            'analysis': result.data
                        }
                    )
                else:
                    logger.error(f"❌ XML analysis failed: {result.errors}")

            except Exception as e:
                logger.error(f"❌ Auto-XML analysis error: {e}")

    def shutdown(self):
        """Cleanup"""
        logger.info("XML parser plugin shutdown")

    def health_check(self) -> bool:
        """Health check"""
        return HAS_PANDAS
