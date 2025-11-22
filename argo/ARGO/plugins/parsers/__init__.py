"""
ARGO Schedule Parsers Package

This package contains parsers for project management schedule files:
- XER Parser: Primavera P6 XER files
- XML Parser: Microsoft Project XML (MSPDI) files
- Schedule Parser: Universal parser with auto-detection

Usage:
    from plugins.parsers.xer_parser_plugin import XERParserPlugin
    from plugins.parsers.xml_parser_plugin import XMLParserPlugin
    from plugins.parsers.schedule_parser_plugin import ScheduleParserPlugin
"""

__all__ = [
    'XERParserPlugin',
    'XMLParserPlugin',
    'ScheduleParserPlugin'
]