"""
Test script for text extractors.
Tests extraction from the uploaded Drive files.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from search_service.cloud.drive_client import DriveClient
from search_service.extractor.extractor_factory import ExtractorFactory
from search_service.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Test extractors with real Drive files"""
    logger.info("=" * 60)
    logger.info("Testing Text Extractors")
    logger.info("=" * 60)
    
    # Initialize Drive client
    client = DriveClient()
    
    # Authenticate
    logger.info("\n[1] Authenticating with Google Drive...")
    if not client.authenticate():
        logger.error("Authentication failed!")
        return
    
    # List files
    logger.info(f"\n[2] Listing files in folder: {settings.google_drive_folder_id}")
    files = client.list_files()
    logger.info(f"Found {len(files)} files\n")
    
    # Initialize extractor factory
    extractor_factory = ExtractorFactory(include_ocr=False)
    
    # Test extraction on each file
    logger.info("[3] Testing text extraction...\n")
    
    for i, file in enumerate(files, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"File {i}/{len(files)}: {file.name}")
        logger.info(f"{'='*60}")
        logger.info(f"Type: {file.mime_type}")
        logger.info(f"Size: {file.size:,} bytes")
        
        # Check if supported
        if not extractor_factory.is_supported(file.mime_type, file.name):
            logger.warning(f"File type not supported, skipping")
            continue
        
        try:
            # Download file
            logger.info("Downloading...")
            content = client.download_file(file.file_id)
            
            # Extract text
            logger.info("Extracting text...")
            text = extractor_factory.extract_text(content, file.mime_type, file.name)
            
            if text:
                logger.info(f"Extracted {len(text)} characters")
                logger.info(f"\nFirst 200 chars:\n{'-'*60}")
                logger.info(text[:200])
                if len(text) > 200:
                    logger.info("...")
                logger.info(f"{'-'*60}")
            else:
                logger.warning("No text extracted")
                
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Extraction tests complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
