"""
Abstract base class for search indexers.
Defines the interface for indexing and searching documents.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class BaseIndexer(ABC):
    """Abstract base class for search indexers"""
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the search backend.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def create_index(self) -> bool:
        """
        Create the search index with proper schema/mapping.
        
        Returns:
            True if index created successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def index_document(self, document: Dict[str, Any]) -> bool:
        """
        Index a single document.
        
        Args:
            document: Document dict with fields:
                - file_id: Unique file identifier
                - file_name: Name of the file
                - file_path: Full path in storage
                - url: Link to file
                - mime_type: File MIME type
                - extracted_text: Searchable text content
                - updated_time: Last modified time
                - indexed_time: When indexed
                
        Returns:
            True if indexed successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def bulk_index(self, documents: List[Dict[str, Any]]) -> int:
        """
        Index multiple documents in batch.
        
        Args:
            documents: List of document dicts
            
        Returns:
            Number of successfully indexed documents
        """
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents matching query.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching documents with scores
        """
        pass
    
    @abstractmethod
    def delete_document(self, file_id: str) -> bool:
        """
        Delete a document from the index.
        
        Args:
            file_id: ID of document to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def document_exists(self, file_id: str) -> bool:
        """
        Check if a document exists in the index.
        
        Args:
            file_id: ID of document to check
            
        Returns:
            True if document exists, False otherwise
        """
        pass
    
    @abstractmethod
    def get_document(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            file_id: ID of document to retrieve
            
        Returns:
            Document dict if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_all_document_ids(self) -> List[str]:
        """
        Get all document IDs in the index.
        
        Returns:
            List of file IDs
        """
        pass
    
    @abstractmethod
    def delete_index(self) -> bool:
        """
        Delete the entire index.
        
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
