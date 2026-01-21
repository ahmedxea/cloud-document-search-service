"""
Abstract base class for text extractors.
Defines the interface that all extractors must implement.
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseExtractor(ABC):
    """Abstract base class for text extractors"""
    
    @abstractmethod
    def can_extract(self, mime_type: str, filename: str) -> bool:
        """
        Check if this extractor can handle the given file type.
        
        Args:
            mime_type: MIME type of the file
            filename: Name of the file (to check extension)
            
        Returns:
            True if this extractor can handle the file, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_text(self, content: bytes, filename: str) -> str:
        """
        Extract text content from file bytes.
        
        Args:
            content: Raw file content as bytes
            filename: Name of the file (for context/extension checking)
            
        Returns:
            Extracted text content as string
            
        Raises:
            Exception: If extraction fails
        """
        pass
    
    def get_supported_mime_types(self) -> list[str]:
        """
        Get list of MIME types supported by this extractor.
        
        Returns:
            List of supported MIME types
        """
        return []
    
    def get_supported_extensions(self) -> list[str]:
        """
        Get list of file extensions supported by this extractor.
        
        Returns:
            List of supported extensions (e.g., ['.txt', '.text'])
        """
        return []
