"""
Google Drive client implementation with OAuth 2.0 authentication.
Handles file listing, downloading, and metadata retrieval.
"""
import os
import json
import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

from .base_client import BaseCloudClient, CloudFile
from ..config import settings

logger = logging.getLogger(__name__)

# Scopes required for Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class DriveClient(BaseCloudClient):
    """Google Drive client with OAuth authentication"""
    
    def __init__(self):
        self.service = None
        self.creds = None
        self.folder_id = settings.google_drive_folder_id
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive using OAuth 2.0.
        Uses token.json if exists, otherwise initiates OAuth flow.
        """
        try:
            token_path = Path(settings.token_file)
            
            # Load existing token if available
            if token_path.exists():
                logger.info(f"Loading credentials from {token_path}")
                self.creds = Credentials.from_authorized_user_file(
                    str(token_path), SCOPES
                )
            
            # Refresh or get new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing expired credentials")
                    self.creds.refresh(Request())
                else:
                    logger.info("Starting OAuth flow - browser will open")
                    # Create credentials dict for OAuth flow
                    client_config = {
                        "installed": {
                            "client_id": settings.google_client_id,
                            "client_secret": settings.google_client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost"]
                        }
                    }
                    
                    flow = InstalledAppFlow.from_client_config(
                        client_config, SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(token_path, 'w') as token:
                    token.write(self.creds.to_json())
                logger.info(f"Credentials saved to {token_path}")
            
            # Build Drive service
            self.service = build('drive', 'v3', credentials=self.creds)
            logger.info("Successfully authenticated with Google Drive")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def list_files(self, folder_id: Optional[str] = None) -> List[CloudFile]:
        """
        List all files in a folder (recursively includes subfolders).
        
        Args:
            folder_id: Drive folder ID. If None, uses configured folder.
            
        Returns:
            List of CloudFile objects
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        target_folder = folder_id or self.folder_id
        logger.info(f"Listing files in folder: {target_folder}")
        
        files = []
        folders_to_process = [(target_folder, "")]
        
        while folders_to_process:
            current_folder_id, current_path = folders_to_process.pop(0)
            
            # Query files and folders in current folder
            query = f"'{current_folder_id}' in parents and trashed=false"
            page_token = None
            
            while True:
                try:
                    results = self.service.files().list(
                        q=query,
                        pageSize=100,
                        fields="nextPageToken, files(id, name, mimeType, size, "
                               "webViewLink, modifiedTime, createdTime)",
                        pageToken=page_token
                    ).execute()
                    
                    items = results.get('files', [])
                    
                    for item in items:
                        mime_type = item['mimeType']
                        item_name = item['name']
                        item_path = f"{current_path}/{item_name}" if current_path else item_name
                        
                        # If it's a folder, add to queue for processing
                        if mime_type == 'application/vnd.google-apps.folder':
                            folders_to_process.append((item['id'], item_path))
                            logger.debug(f"Found subfolder: {item_path}")
                        else:
                            # It's a file - add to results
                            cloud_file = self._item_to_cloudfile(item, item_path)
                            files.append(cloud_file)
                            logger.debug(f"Found file: {item_path}")
                    
                    page_token = results.get('nextPageToken')
                    if not page_token:
                        break
                        
                except Exception as e:
                    logger.error(f"Error listing folder {current_folder_id}: {e}")
                    break
        
        logger.info(f"Found {len(files)} files")
        return files
    
    def download_file(self, file_id: str) -> bytes:
        """
        Download file content as bytes.
        Handles both regular files and Google Workspace files (exports as PDF).
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            # Get file metadata to check type
            file_meta = self.service.files().get(
                fileId=file_id,
                fields='mimeType'
            ).execute()
            
            mime_type = file_meta['mimeType']
            
            # Handle Google Workspace files (export as PDF)
            if mime_type.startswith('application/vnd.google-apps'):
                logger.debug(f"Exporting Google Workspace file {file_id} as PDF")
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='application/pdf'
                )
            else:
                # Regular file download
                request = self.service.files().get_media(fileId=file_id)
            
            # Download file content
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download progress: {int(status.progress() * 100)}%")
            
            content = file_buffer.getvalue()
            logger.debug(f"Downloaded {len(content)} bytes")
            return content
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            raise
    
    def get_file_metadata(self, file_id: str) -> CloudFile:
        """Get metadata for a specific file"""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            item = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, webViewLink, "
                       "modifiedTime, createdTime"
            ).execute()
            
            return self._item_to_cloudfile(item, item['name'])
            
        except Exception as e:
            logger.error(f"Error getting metadata for {file_id}: {e}")
            raise
    
    def _item_to_cloudfile(self, item: dict, path: str) -> CloudFile:
        """Convert Drive API item to CloudFile object"""
        return CloudFile(
            file_id=item['id'],
            name=item['name'],
            path=path,
            url=item.get('webViewLink', ''),
            mime_type=item['mimeType'],
            size=int(item.get('size', 0)),
            modified_time=datetime.fromisoformat(
                item['modifiedTime'].replace('Z', '+00:00')
            ),
            created_time=datetime.fromisoformat(
                item['createdTime'].replace('Z', '+00:00')
            )
        )
