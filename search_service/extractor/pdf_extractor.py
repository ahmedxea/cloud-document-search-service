"""
PDF file extractor using pdfminer.six.
Extracts text content from PDF documents.
"""
import logging
from io import BytesIO
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError
from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractor):
    """Extractor for PDF files"""
    
    def can_extract(self, mime_type: str, filename: str) -> bool:
        """Check if file is a PDF"""
        # Check MIME type
        if mime_type in self.get_supported_mime_types():
            return True
        
        # Check file extension
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in self.get_supported_extensions())
    
    def extract_text(self, content: bytes, filename: str) -> str:
        """
        Extract text from PDF using pdfminer.six.
        """
        try:
            # Create BytesIO object from content
            pdf_file = BytesIO(content)
            
            # Extract text using pdfminer
            text = extract_text(pdf_file)
            
            if not text or not text.strip():
                logger.warning(f"No text extracted from PDF {filename} (might be image-based)")
                return ""
            
            # Clean up the text
            # Remove excessive whitespace and normalize line breaks
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            extracted_text = "\n".join(lines)
            
            logger.debug(f"Extracted {len(extracted_text)} chars from PDF {filename}")
            return extracted_text.strip()
            
        except PDFSyntaxError as e:
            logger.error(f"Invalid PDF format for {filename}: {e}")
            raise ValueError(f"Invalid PDF file {filename}: {e}")
        
        except Exception as e:
            logger.error(f"Error extracting from PDF {filename}: {e}")
            raise ValueError(f"Could not extract text from PDF {filename}: {e}")
    
    def get_supported_mime_types(self) -> list[str]:
        """Return supported MIME types for PDF files"""
        return [
            'application/pdf',
            'application/x-pdf',
        ]
    
    def get_supported_extensions(self) -> list[str]:
        """Return supported file extensions"""
        return ['.pdf']
