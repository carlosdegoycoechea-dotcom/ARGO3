"""
OCR Plugin for ARGO
Extracts text from images using Tesseract OCR

Capabilities:
- Extract text from PNG, JPG, JPEG, TIF, TIFF images
- Support for multiple languages
- Confidence scoring
- Layout preservation options

Dependencies:
- pytesseract
- Pillow
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

# Note: These imports are optional - plugin will check if available
try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

from core.plugins import (
    Plugin,
    BaseAnalyzer,
    AnalysisResult,
    PluginMetadata,
    PluginCapability
)

logger = logging.getLogger(__name__)


class OCRAnalyzer(BaseAnalyzer):
    """
    OCR analyzer for extracting text from images
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.lang = self.config.get('language', 'eng')
        self.psm = self.config.get('psm', 3)  # Page segmentation mode

    @property
    def name(self) -> str:
        return "ocr_analyzer"

    @property
    def supported_formats(self) -> List[str]:
        return ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif']

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Extracts text from images using Tesseract OCR"

    def validate(self, file_path: str) -> tuple[bool, Optional[str]]:
        """Validate that OCR dependencies are available"""
        is_valid, error = super().validate(file_path)

        if not is_valid:
            return False, error

        if not HAS_OCR:
            return False, "OCR dependencies not installed (pytesseract, Pillow)"

        return True, None

    def analyze(self, file_path: str, options: Optional[Dict] = None) -> AnalysisResult:
        """
        Extract text from image

        Options:
            - language: OCR language (default: eng)
            - psm: Page segmentation mode (default: 3)
            - get_data: Extract detailed data including boxes
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
        lang = options.get('language', self.lang)
        psm = options.get('psm', self.psm)
        get_data = options.get('get_data', False)

        try:
            # Open image
            image = Image.open(file_path)

            # Get image info
            image_info = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height
            }

            # Configure tesseract
            config = f'--psm {psm}'

            # Extract text
            text = pytesseract.image_to_string(image, lang=lang, config=config)

            # Extract detailed data if requested
            data_dict = {}
            if get_data:
                data_dict = pytesseract.image_to_data(
                    image,
                    lang=lang,
                    config=config,
                    output_type=pytesseract.Output.DICT
                )

            # Calculate some statistics
            words = text.split()
            lines = text.split('\n')
            char_count = len(text)
            word_count = len(words)
            line_count = len([l for l in lines if l.strip()])

            execution_time = (time.time() - start_time) * 1000

            return AnalysisResult(
                status='success',
                data={
                    'text': text,
                    'statistics': {
                        'characters': char_count,
                        'words': word_count,
                        'lines': line_count
                    },
                    'image_info': image_info,
                    'ocr_data': data_dict if get_data else None
                },
                metadata={
                    'analyzer': self.name,
                    'version': self.version,
                    'language': lang,
                    'psm': psm
                },
                execution_time_ms=execution_time
            )

        except Exception as e:
            return AnalysisResult(
                status='error',
                data={},
                errors=[f"OCR failed: {str(e)}"],
                execution_time_ms=(time.time() - start_time) * 1000
            )


class OCRPlugin(Plugin):
    """
    OCR Plugin for ARGO

    Adds capability to extract text from images
    """

    def __init__(self):
        self.metadata = PluginMetadata(
            name="ocr",
            version="1.0.0",
            author="ARGO Team",
            description="Extract text from images using Tesseract OCR",
            capabilities=[PluginCapability.ANALYZER],
            dependencies=["pytesseract", "Pillow"],
            enabled=True
        )
        self.analyzer = None
        self.system = None

    def initialize(self, system):
        """Initialize OCR plugin"""
        self.system = system

        # Check if dependencies are available
        if not HAS_OCR:
            logger.warning(
                "⚠️ OCR plugin dependencies not installed. "
                "Install with: pip install pytesseract Pillow"
            )
            logger.warning(
                "⚠️ Also install Tesseract: "
                "https://github.com/tesseract-ocr/tesseract"
            )
            return

        # Get config from system if available
        config = {}
        if hasattr(system, 'config'):
            config = system.config.get('ocr', {})

        # Create analyzer
        self.analyzer = OCRAnalyzer(config)

        # Register analyzer
        system.plugins.register_analyzer(self.analyzer)

        # Register event handlers
        system.plugins.events.on('document_uploaded', self.on_document_uploaded)

        # Register hooks
        system.plugins.hooks.register(
            'post_extraction',
            self.enhance_extraction,
            priority=10
        )

        logger.info("✅ OCR plugin initialized successfully")

    def on_document_uploaded(self, data: Dict):
        """Auto-OCR when image uploaded"""
        file_path = data.get('file_path')

        if not file_path:
            return

        # Check if it's an image we can handle
        if self.analyzer and self.analyzer.can_handle(file_path):
            logger.info(f"🔍 Auto-OCR triggered for: {file_path}")

            try:
                result = self.analyzer.analyze(file_path)

                if result.is_success:
                    logger.info(
                        f"✅ OCR completed: {result.data['statistics']['words']} words extracted"
                    )

                    # Emit event with OCR results
                    self.system.plugins.events.emit_sync(
                        'ocr_completed',
                        {
                            'file_path': file_path,
                            'text': result.data['text'],
                            'statistics': result.data['statistics']
                        }
                    )
                else:
                    logger.error(f"❌ OCR failed: {result.errors}")

            except Exception as e:
                logger.error(f"❌ Auto-OCR error: {e}")

    def enhance_extraction(self, data: Dict, context: Dict) -> Dict:
        """Enhance extraction with OCR for images"""
        file_path = context.get('file_path')

        if not file_path or not self.analyzer:
            return data

        # If it's an image, add OCR text
        if self.analyzer.can_handle(file_path):
            try:
                result = self.analyzer.analyze(file_path)

                if result.is_success:
                    # Add OCR text to extraction
                    if 'text' not in data or not data['text']:
                        data['text'] = result.data['text']
                    else:
                        data['text'] += f"\n\n[OCR Extracted Text]\n{result.data['text']}"

                    data['ocr_statistics'] = result.data['statistics']

            except Exception as e:
                logger.error(f"OCR enhancement error: {e}")

        return data

    def shutdown(self):
        """Cleanup on shutdown"""
        logger.info("OCR plugin shutdown")

    def health_check(self) -> bool:
        """Check if OCR is working"""
        if not HAS_OCR:
            return False

        try:
            # Try to get tesseract version
            version = pytesseract.get_tesseract_version()
            return version is not None
        except:
            return False
