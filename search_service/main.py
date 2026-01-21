"""
Main orchestration script for document search service.
Syncs Google Drive files to Elasticsearch index.

Features:
- Downloads files from Google Drive
- Extracts text from supported formats
- Indexes in Elasticsearch
- Incremental indexing (only re-index if modified)
- Deletion sync (removes deleted files from index)

Usage:
    python -m search_service.main                    # Run full sync
    python -m search_service.main --incremental      # Only index new/modified
    python -m search_service.main --clean            # Delete index and re-index all
"""
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from search_service.config import settings
from search_service.cloud.drive_client import DriveClient
from search_service.extractor.extractor_factory import ExtractorFactory
from search_service.indexer.elastic_indexer import ElasticIndexer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Orchestrates the document indexing pipeline"""
    
    def __init__(self, incremental: bool = False):
        """
        Initialize indexer components.
        
        Args:
            incremental: If True, only index new/modified files
        """
        self.incremental = incremental
        self.drive_client = DriveClient()
        self.extractor_factory = ExtractorFactory(include_ocr=False)
        self.indexer = ElasticIndexer()
        
        self.stats = {
            'total_files': 0,
            'indexed': 0,
            'updated': 0,
            'skipped': 0,
            'deleted': 0,
            'errors': 0
        }
    
    def connect(self) -> bool:
        """Connect to all services"""
        logger.info("=" * 70)
        logger.info("Document Search - Indexing Pipeline")
        logger.info("=" * 70)
        
        # Connect to Elasticsearch
        logger.info("\n[1] Connecting to Elasticsearch...")
        if not self.indexer.connect():
            logger.error("Failed to connect to Elasticsearch")
            logger.error("Make sure Elasticsearch is running: docker compose up -d")
            return False
        
        # Create index if needed
        logger.info("\n[2] Ensuring index exists...")
        self.indexer.create_index()
        
        # Authenticate with Drive
        logger.info("\n[3] Authenticating with Google Drive...")
        if not self.drive_client.authenticate():
            logger.error("Failed to authenticate with Google Drive")
            return False
        
        return True
    
    def sync_files(self):
        """Main synchronization logic"""
        logger.info(f"\n[4] Listing files from Drive folder: {settings.google_drive_folder_id}")
        
        try:
            # Get files from Drive
            drive_files = self.drive_client.list_files()
            self.stats['total_files'] = len(drive_files)
            
            logger.info(f"Found {len(drive_files)} files in Drive")
            
            if not drive_files:
                logger.warning("No files to index!")
                return
            
            # Get currently indexed file IDs
            indexed_file_ids = set(self.indexer.get_all_document_ids())
            drive_file_ids = {f.file_id for f in drive_files}
            
            # Deletion sync: Find files that were deleted from Drive
            deleted_file_ids = indexed_file_ids - drive_file_ids
            if deleted_file_ids:
                logger.info(f"\n[5] Found {len(deleted_file_ids)} deleted files to remove from index")
                for file_id in deleted_file_ids:
                    if self.indexer.delete_document(file_id):
                        self.stats['deleted'] += 1
                        logger.info(f"  Removed deleted file: {file_id}")
            
            # Process each file
            logger.info(f"\n[6] Processing files...\n")
            
            for i, file in enumerate(drive_files, 1):
                logger.info(f"[{i}/{len(drive_files)}] {file.name}")
                
                try:
                    # Check if file is supported
                    if not self.extractor_factory.is_supported(file.mime_type, file.name):
                        logger.warning(f"  Unsupported file type, skipping")
                        self.stats['skipped'] += 1
                        continue
                    
                    # Incremental indexing: Check if file needs update
                    if self.incremental:
                        existing_doc = self.indexer.get_document(file.file_id)
                        if existing_doc:
                            existing_time = datetime.fromisoformat(existing_doc['updated_time'])
                            if file.modified_time <= existing_time:
                                logger.info(f"  Already up-to-date, skipping")
                                self.stats['skipped'] += 1
                                continue
                    
                    # Download file
                    logger.info(f"  Downloading...")
                    content = self.drive_client.download_file(file.file_id)
                    
                    # Extract text
                    logger.info(f"  Extracting text...")
                    text = self.extractor_factory.extract_text(
                        content, file.mime_type, file.name
                    )
                    
                    if not text:
                        logger.warning(f"  No text extracted, skipping")
                        self.stats['skipped'] += 1
                        continue
                    
                    # Prepare document
                    document = {
                        'file_id': file.file_id,
                        'file_name': file.name,
                        'file_path': file.path,
                        'url': file.url,
                        'mime_type': file.mime_type,
                        'extracted_text': text,
                        'updated_time': file.modified_time.isoformat(),
                        'size': file.size
                    }
                    
                    # Index document
                    logger.info(f"  Indexing...")
                    is_update = file.file_id in indexed_file_ids
                    
                    if self.indexer.index_document(document):
                        if is_update:
                            logger.info(f"  Updated ({len(text)} chars)")
                            self.stats['updated'] += 1
                        else:
                            logger.info(f"  Indexed ({len(text)} chars)")
                            self.stats['indexed'] += 1
                    else:
                        logger.error(f"  Indexing failed")
                        self.stats['errors'] += 1
                    
                except Exception as e:
                    logger.error(f"  Error: {e}")
                    self.stats['errors'] += 1
                    continue
            
        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
    
    def print_summary(self):
        """Print final summary"""
        logger.info("\n" + "=" * 70)
        logger.info("Sync Complete - Summary")
        logger.info("=" * 70)
        logger.info(f"Total files in Drive:  {self.stats['total_files']}")
        logger.info(f"Newly indexed:         {self.stats['indexed']}")
        logger.info(f"Updated:               {self.stats['updated']}")
        logger.info(f"Skipped:               {self.stats['skipped']}")
        logger.info(f"Deleted from index:    {self.stats['deleted']}")
        logger.info(f"Errors:                {self.stats['errors']}")
        logger.info("=" * 70)
        
        if self.stats['errors'] > 0:
            logger.warning("Some files failed to index. Check logs above.")
        else:
            logger.info("Sync completed successfully!")
    
    def run(self):
        """Execute the full indexing pipeline"""
        if not self.connect():
            sys.exit(1)
        
        self.sync_files()
        self.print_summary()


def main():
    """Main entry point with CLI arguments"""
    parser = argparse.ArgumentParser(
        description="Document Search - Index documents from Google Drive"
    )
    parser.add_argument(
        '--incremental', '-i',
        action='store_true',
        help='Only index new or modified files (faster)'
    )
    parser.add_argument(
        '--clean', '-c',
        action='store_true',
        help='Delete existing index and re-index all files'
    )
    
    args = parser.parse_args()
    
    # Handle clean flag
    if args.clean:
        logger.info("Clean mode: Deleting existing index...")
        indexer = ElasticIndexer()
        if indexer.connect():
            indexer.delete_index()
            logger.info("Index deleted")
        else:
            logger.error("Failed to connect to Elasticsearch")
            sys.exit(1)
    
    # Run indexing
    indexer = DocumentIndexer(incremental=args.incremental)
    
    if args.incremental:
        logger.info("Running in incremental mode - only new/modified files will be indexed")
    
    indexer.run()


if __name__ == "__main__":
    main()
