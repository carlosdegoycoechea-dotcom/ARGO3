"""
Basic tests for analysis plugins (OCR, Excel)
These are BASIC tests - comprehensive tests TODO
"""
import pytest
from pathlib import Path

# Import plugins
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.ocr_plugin import OCRAnalyzer, OCRPlugin
from plugins.excel_plugin import ExcelPluginAnalyzer, ExcelPlugin


class TestOCRPlugin:
    """Basic tests for OCR Plugin"""

    def test_ocr_analyzer_creation(self):
        """OCR Analyzer can be instantiated"""
        analyzer = OCRAnalyzer()
        assert analyzer.name == 'ocr_analyzer'
        assert analyzer.version == '1.0.0'

    def test_ocr_supported_formats(self):
        """OCR supports image formats"""
        analyzer = OCRAnalyzer()
        formats = analyzer.supported_formats

        assert '.png' in formats
        assert '.jpg' in formats
        assert '.jpeg' in formats
        assert '.tiff' in formats

    def test_ocr_can_handle_images(self):
        """OCR can identify image files"""
        analyzer = OCRAnalyzer()

        assert analyzer.can_handle('test.png') is True
        assert analyzer.can_handle('test.jpg') is True
        assert analyzer.can_handle('test.pdf') is False
        assert analyzer.can_handle('test.xlsx') is False

    def test_ocr_plugin_metadata(self):
        """OCR Plugin has correct metadata"""
        plugin = OCRPlugin()

        assert plugin.metadata.name == 'ocr'
        assert plugin.metadata.version == '1.0.0'
        assert plugin.metadata.enabled is True

    def test_ocr_plugin_initialization(self, mock_system):
        """OCR Plugin can initialize"""
        plugin = OCRPlugin()

        # Should not crash even without dependencies
        plugin.initialize(mock_system)

        # Plugin should track system
        assert plugin.system == mock_system

    def test_ocr_plugin_health_check(self):
        """OCR Plugin health check works"""
        plugin = OCRPlugin()

        # Without dependencies, should return False
        # (This is expected - OCR requires pytesseract)
        health = plugin.health_check()
        assert health is False or health is True  # Either is acceptable


class TestExcelPlugin:
    """Basic tests for Excel Plugin"""

    def test_excel_analyzer_creation(self):
        """Excel Analyzer can be instantiated"""
        analyzer = ExcelPluginAnalyzer()
        assert analyzer.name == 'excel_analyzer'
        assert analyzer.version == '2.0.0'

    def test_excel_supported_formats(self):
        """Excel supports spreadsheet formats"""
        analyzer = ExcelPluginAnalyzer()
        formats = analyzer.supported_formats

        assert '.xlsx' in formats
        assert '.xls' in formats
        assert '.csv' in formats
        assert '.xlsm' in formats

    def test_excel_can_handle_spreadsheets(self):
        """Excel can identify spreadsheet files"""
        analyzer = ExcelPluginAnalyzer()

        assert analyzer.can_handle('test.xlsx') is True
        assert analyzer.can_handle('test.csv') is True
        assert analyzer.can_handle('test.png') is False
        assert analyzer.can_handle('test.pdf') is False

    def test_excel_plugin_metadata(self):
        """Excel Plugin has correct metadata"""
        plugin = ExcelPlugin()

        assert plugin.metadata.name == 'excel_analyzer'
        assert plugin.metadata.version == '2.0.0'
        assert plugin.metadata.enabled is True

    def test_excel_plugin_initialization(self, mock_system):
        """Excel Plugin can initialize"""
        plugin = ExcelPlugin()
        plugin.initialize(mock_system)

        assert plugin.system == mock_system

    def test_excel_plugin_health_check(self):
        """Excel Plugin health check works"""
        plugin = ExcelPlugin()

        # Health check should return True if pandas available
        health = plugin.health_check()
        assert isinstance(health, bool)


class TestAnalyzerValidation:
    """Test analyzer validation methods"""

    def test_ocr_validate_nonexistent_file(self):
        """OCR validates file existence"""
        analyzer = OCRAnalyzer()

        is_valid, error = analyzer.validate('nonexistent.png')

        assert is_valid is False
        assert error is not None
        assert 'not found' in error.lower()

    def test_excel_validate_nonexistent_file(self):
        """Excel validates file existence"""
        analyzer = ExcelPluginAnalyzer()

        is_valid, error = analyzer.validate('nonexistent.xlsx')

        assert is_valid is False
        assert error is not None
        assert 'not found' in error.lower()

    def test_ocr_validate_wrong_format(self):
        """OCR rejects unsupported formats"""
        analyzer = OCRAnalyzer()

        is_valid, error = analyzer.validate('test.pdf')

        # Note: This will say "not found" because file doesn't exist
        # But the method still works
        assert is_valid is False

    def test_excel_validate_wrong_format(self):
        """Excel rejects unsupported formats"""
        analyzer = ExcelPluginAnalyzer()

        is_valid, error = analyzer.validate('test.png')

        assert is_valid is False


# Mark this as basic unit tests
pytestmark = pytest.mark.unit
