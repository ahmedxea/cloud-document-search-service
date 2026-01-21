"""
Image file extractor using pytesseract (OCR).
Optional extractor for extracting text from images.
Requires tesseract-ocr to be installed on the system.
"""
import logging
from io import BytesIO
from PIL import Image
import pytesseract
from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class ImageExtractor(BaseExtractor):
    """Extractor for image files using OCR"""
    
    def __init__(self):
        """Initialize and check if tesseract is available"""
        self.available = self._check_tesseract()
        if not self.available:
            logger.warning("Tesseract OCR not found. Image extraction will be disabled.")
            logger.warning("Install with: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)")
    
    def _check_tesseract(self) -> bool:
        """Check if tesseract is installed"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    def can_extract(self, mime_type: str, filename: str) -> bool:
        """Check if file is an image and tesseract is available"""
        if not self.available:
            return False
        
        # Check MIME type
        if mime_type in self.get_supported_mime_types():
            return True
        
        # Check file extension
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in self.get_supported_extensions())
    
    def extract_text(self, content: bytes, filename: str) -> str:
        """
        Extract text from image using OCR (pytesseract).
        """
        if not self.available:
            raise ValueError("Tesseract OCR is not installed. Cannot extract text from images.")
        
        try:
            # Open image from bytes
            image = Image.open(BytesIO(content))
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            if not text or not text.strip():
                logger.warning(f"No text extracted from image {filename}")
                return ""
            
            # Clean up the text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            extracted_text = "\n".join(lines)
            
            logger.debug(f"Extracted {len(extracted_text)} chars from image {filename}")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting from image {filename}: {e}")
            raise ValueError(f"Could not extract text from image {filename}: {e}")
    
    def get_supported_mime_types(self) -> list[str]:
        """Return supported MIME types for image files"""
        return [
            'image/png',
            'image/jpeg',
            'image/jpg',
            'image/tiff',
            'image/bmp',
        ]
    
    def get_supported_extensions(self) -> list[str]:
        """Return supported file extensions"""
        return ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
