"""
Extractor factory and manager.
Selects the appropriate extractor based on file type.
"""
import logging
from typing import Optional
from .base_extractor import BaseExtractor
from .text_extractor import TextExtractor
from .csv_extractor import CSVExtractor
from .pdf_extractor import PDFExtractor
from .image_extractor import ImageExtractor

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """Factory for getting the right extractor for a file type"""
    
    def __init__(self, include_ocr: bool = False):
        """
        Initialize factory with all available extractors.
        
        Args:
            include_ocr: Whether to include image OCR extractor (requires tesseract)
        """
        self.extractors: list[BaseExtractor] = [
            TextExtractor(),
            CSVExtractor(),
            PDFExtractor(),
        ]
        
        # Add image extractor if requested
        if include_ocr:
            image_extractor = ImageExtractor()
            if image_extractor.available:
                self.extractors.append(image_extractor)
                logger.info("Image OCR extractor enabled")
            else:
                logger.warning("Image OCR requested but tesseract not available")
    
    def get_extractor(self, mime_type: str, filename: str) -> Optional[BaseExtractor]:
        """
        Get the appropriate extractor for a file.
        
        Args:
            mime_type: MIME type of the file
            filename: Name of the file
            
        Returns:
            Extractor instance if supported, None otherwise
        """
        for extractor in self.extractors:
            if extractor.can_extract(mime_type, filename):
                logger.debug(f"Selected {extractor.__class__.__name__} for {filename}")
                return extractor
        
        logger.warning(f"No extractor found for {filename} (MIME: {mime_type})")
        return None
    
    def extract_text(self, content: bytes, mime_type: str, filename: str) -> Optional[str]:
        """
        Extract text from file content.
        
        Args:
            content: Raw file content
            mime_type: MIME type of the file
            filename: Name of the file
            
        Returns:
            Extracted text or None if extraction failed/not supported
        """
        extractor = self.get_extractor(mime_type, filename)
        if not extractor:
            return None
        
        try:
            text = extractor.extract_text(content, filename)
            return text
        except Exception as e:
            logger.error(f"Extraction failed for {filename}: {e}")
            return None
    
    def is_supported(self, mime_type: str, filename: str) -> bool:
        """Check if a file type is supported"""
        return self.get_extractor(mime_type, filename) is not None
