"""
Test script for Elasticsearch indexer.
Downloads files from Drive, extracts text, and indexes in Elasticsearch.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from search_service.cloud.drive_client import DriveClient
from search_service.extractor.extractor_factory import ExtractorFactory
from search_service.indexer.elastic_indexer import ElasticIndexer
from search_service.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Test complete indexing pipeline"""
    logger.info("=" * 60)
    logger.info("Testing Elasticsearch Indexer")
    logger.info("=" * 60)
    
    # Step 1: Connect to Elasticsearch
    logger.info("\n[1] Connecting to Elasticsearch...")
    indexer = ElasticIndexer()
    if not indexer.connect():
        logger.error("Failed to connect to Elasticsearch")
        logger.error("Make sure Elasticsearch is running: docker-compose up -d")
        return
    
    # Step 2: Create index
    logger.info("\n[2] Creating search index...")
    if not indexer.create_index():
        logger.error("Failed to create index")
        return
    
    # Step 3: Authenticate with Drive
    logger.info("\n[3] Authenticating with Google Drive...")
    drive_client = DriveClient()
    if not drive_client.authenticate():
        logger.error("Authentication failed")
        return
    
    # Step 4: List files
    logger.info(f"\n[4] Listing files from folder: {settings.google_drive_folder_id}")
    files = drive_client.list_files()
    logger.info(f"Found {len(files)} files")
    
    if not files:
        logger.warning("No files to index!")
        return
    
    # Step 5: Extract and index
    logger.info("\n[5] Extracting text and indexing documents...\n")
    extractor_factory = ExtractorFactory()
    
    indexed_count = 0
    skipped_count = 0
    
    for i, file in enumerate(files, 1):
        logger.info(f"\n[{i}/{len(files)}] Processing: {file.name}")
        
        # Check if supported
        if not extractor_factory.is_supported(file.mime_type, file.name):
            logger.warning(f"Unsupported file type, skipping")
            skipped_count += 1
            continue
        
        try:
            # Download file
            logger.info("  Downloading...")
            content = drive_client.download_file(file.file_id)
            
            # Extract text
            logger.info("  Extracting text...")
            text = extractor_factory.extract_text(content, file.mime_type, file.name)
            
            if not text:
                logger.warning("  No text extracted, skipping")
                skipped_count += 1
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
            logger.info("  Indexing...")
            if indexer.index_document(document):
                logger.info(f"  Indexed successfully ({len(text)} chars)")
                indexed_count += 1
            else:
                logger.error("  Indexing failed")
                
        except Exception as e:
            logger.error(f"  Error: {e}")
    
    # Step 6: Test search
    logger.info("\n" + "=" * 60)
    logger.info(f"Indexing complete!")
    logger.info(f"  Indexed: {indexed_count}")
    logger.info(f"  Skipped: {skipped_count}")
    logger.info("=" * 60)
    
    if indexed_count > 0:
        logger.info("\n[6] Testing search functionality...\n")
        
        # Test searches
        test_queries = [
            "engineering",
            "search",
            "API",
            "laptop"
        ]
        
        for query in test_queries:
            logger.info(f"\nSearch: '{query}'")
            logger.info("-" * 40)
            results = indexer.search(query, limit=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    logger.info(f"{i}. {result['file_name']} (score: {result['score']:.2f})")
                    logger.info(f"   Path: {result['file_path']}")
                    if 'highlights' in result and result['highlights']:
                        logger.info(f"   Match: ...{result['highlights'][0]}...")
            else:
                logger.info("  No results found")
    
    logger.info("\n" + "=" * 60)
    logger.info("All tests complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
