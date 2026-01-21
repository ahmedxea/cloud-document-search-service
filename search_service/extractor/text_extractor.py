"""
Text file extractor for .txt files.
Handles plain text files with UTF-8 encoding.
"""
import logging
from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class TextExtractor(BaseExtractor):
    """Extractor for plain text files"""
    
    def can_extract(self, mime_type: str, filename: str) -> bool:
        """Check if file is a text file"""
        # Check MIME type
        if mime_type in self.get_supported_mime_types():
            return True
        
        # Check file extension
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in self.get_supported_extensions())
    
    def extract_text(self, content: bytes, filename: str) -> str:
        """
        Extract text from plain text file.
        Tries UTF-8 first, falls back to latin-1 if needed.
        """
        try:
            # Try UTF-8 first
            text = content.decode('utf-8')
            logger.debug(f"Extracted {len(text)} chars from {filename} using UTF-8")
            return text.strip()
        except UnicodeDecodeError:
            # Fallback to latin-1 (works for most Western text)
            try:
                text = content.decode('latin-1')
                logger.warning(f"Used latin-1 fallback for {filename}")
                return text.strip()
            except Exception as e:
                logger.error(f"Failed to decode {filename}: {e}")
                raise ValueError(f"Could not decode text file {filename}: {e}")
    
    def get_supported_mime_types(self) -> list[str]:
        """Return supported MIME types for text files"""
        return [
            'text/plain',
            'text/txt',
            'application/txt',
        ]
    
    def get_supported_extensions(self) -> list[str]:
        """Return supported file extensions"""
        return ['.txt', '.text']
