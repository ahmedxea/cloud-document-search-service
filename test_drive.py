"""
Test script for Google Drive client.
Run this to verify OAuth and file listing works.
"""
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from search_service.cloud.drive_client import DriveClient
from search_service.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Test Drive client"""
    logger.info("=" * 60)
    logger.info("Testing Google Drive Client")
    logger.info("=" * 60)
    
    # Initialize client
    client = DriveClient()
    
    # Step 1: Authenticate
    logger.info("\n[1] Authenticating with Google Drive...")
    if not client.authenticate():
        logger.error("Authentication failed!")
        return
    
    # Step 2: List files
    logger.info(f"\n[2] Listing files in folder: {settings.google_drive_folder_id}")
    try:
        files = client.list_files()
        
        logger.info(f"\nFound {len(files)} files:\n")
        
        for i, file in enumerate(files, 1):
            logger.info(f"{i}. {file.name}")
            logger.info(f"   Path: {file.path}")
            logger.info(f"   Type: {file.mime_type}")
            logger.info(f"   Size: {file.size:,} bytes")
            logger.info(f"   Modified: {file.modified_time}")
            logger.info(f"   URL: {file.url}")
            logger.info("")
        
        # Step 3: Download first file (if any)
        if files:
            logger.info("[3] Testing download of first file...")
            first_file = files[0]
            try:
                content = client.download_file(first_file.file_id)
                logger.info(f"Downloaded {len(content):,} bytes from {first_file.name}")
                logger.info(f"First 100 chars: {content[:100]}")
            except Exception as e:
                logger.error(f"Download failed: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("All tests passed!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
