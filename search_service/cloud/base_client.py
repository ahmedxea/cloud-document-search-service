"""
Abstract base class for cloud storage clients.
Defines the interface that all storage providers must implement.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CloudFile:
    """Represents a file in cloud storage"""
    file_id: str
    name: str
    path: str  # Full path including parent folders
    url: str  # Direct link to file
    mime_type: str
    size: int  # Size in bytes
    modified_time: datetime
    created_time: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for indexing"""
        return {
            'file_id': self.file_id,
            'file_name': self.name,
            'file_path': self.path,
            'url': self.url,
            'mime_type': self.mime_type,
            'size': self.size,
            'modified_time': self.modified_time.isoformat(),
            'created_time': self.created_time.isoformat()
        }


class BaseCloudClient(ABC):
    """Abstract base class for cloud storage clients"""
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the cloud provider.
        Returns True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def list_files(self, folder_id: Optional[str] = None) -> List[CloudFile]:
        """
        List all files in a folder (recursively).
        
        Args:
            folder_id: ID of folder to list. If None, uses configured folder.
            
        Returns:
            List of CloudFile objects
        """
        pass
    
    @abstractmethod
    def download_file(self, file_id: str) -> bytes:
        """
        Download file content as bytes.
        
        Args:
            file_id: ID of file to download
            
        Returns:
            File content as bytes
        """
        pass
    
    @abstractmethod
    def get_file_metadata(self, file_id: str) -> CloudFile:
        """
        Get metadata for a specific file.
        
        Args:
            file_id: ID of file
            
        Returns:
            CloudFile object with metadata
        """
        pass
