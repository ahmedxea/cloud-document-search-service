"""
Elasticsearch indexer implementation.
Handles document indexing and search using Elasticsearch.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from elasticsearch import Elasticsearch, exceptions as es_exceptions
from .base_indexer import BaseIndexer
from ..config import settings

logger = logging.getLogger(__name__)


class ElasticIndexer(BaseIndexer):
    """Elasticsearch implementation of search indexer"""
    
    def __init__(self):
        """Initialize Elasticsearch client"""
        self.client: Optional[Elasticsearch] = None
        self.index_name = settings.elasticsearch_index
        self.host = settings.elasticsearch_host
    
    def connect(self) -> bool:
        """Connect to Elasticsearch"""
        try:
            self.client = Elasticsearch([self.host])
            
            # Test connection
            if not self.client.ping():
                logger.error("Elasticsearch is not responding")
                return False
            
            # Get cluster info
            info = self.client.info()
            logger.info(f"Connected to Elasticsearch {info['version']['number']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            return False
    
    def create_index(self) -> bool:
        """Create index with document mapping"""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            # Check if index already exists
            if self.client.indices.exists(index=self.index_name):
                logger.info(f"Index '{self.index_name}' already exists")
                return True
            
            # Define index mapping
            mapping = {
                "mappings": {
                    "properties": {
                        "file_id": {"type": "keyword"},
                        "file_name": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}}
                        },
                        "file_path": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}}
                        },
                        "url": {"type": "keyword"},
                        "mime_type": {"type": "keyword"},
                        "extracted_text": {"type": "text"},
                        "updated_time": {"type": "date"},
                        "indexed_time": {"type": "date"},
                        "size": {"type": "long"}
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            }
            
            # Create index
            self.client.indices.create(index=self.index_name, **mapping)
            logger.info(f"Created index '{self.index_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False
    
    def index_document(self, document: Dict[str, Any]) -> bool:
        """Index a single document"""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            # Add indexed timestamp
            doc = document.copy()
            doc['indexed_time'] = datetime.utcnow().isoformat()
            
            # Use file_id as document ID
            file_id = doc['file_id']
            
            # Index document
            self.client.index(
                index=self.index_name,
                id=file_id,
                document=doc,
                refresh='wait_for'  # Make immediately searchable
            )
            
            logger.debug(f"Indexed document: {doc['file_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            return False
    
    def bulk_index(self, documents: List[Dict[str, Any]]) -> int:
        """Index multiple documents in batch"""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if not documents:
            return 0
        
        try:
            from elasticsearch.helpers import bulk
            
            # Prepare bulk actions
            actions = []
            for doc in documents:
                doc_copy = doc.copy()
                doc_copy['indexed_time'] = datetime.utcnow().isoformat()
                
                actions.append({
                    "_index": self.index_name,
                    "_id": doc_copy['file_id'],
                    "_source": doc_copy
                })
            
            # Execute bulk indexing
            success, failed = bulk(self.client, actions, refresh='wait_for')
            
            logger.info(f"Bulk indexed {success} documents ({failed} failed)")
            return success
            
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return 0
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for documents"""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            # Build search query
            # Match in extracted_text (main content) and file_name (boost results)
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "extracted_text",
                            "file_name^2",  # Boost file name matches
                            "file_path"
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "size": limit,
                "_source": ["file_id", "file_name", "file_path", "url", "mime_type", "updated_time"],
                "highlight": {
                    "fields": {
                        "extracted_text": {
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        }
                    }
                }
            }
            
            # Execute search
            response = self.client.search(index=self.index_name, **search_body)
            
            # Format results
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'score': hit['_score'],
                    'file_id': hit['_source']['file_id'],
                    'file_name': hit['_source']['file_name'],
                    'file_path': hit['_source']['file_path'],
                    'url': hit['_source']['url'],
                    'mime_type': hit['_source']['mime_type'],
                    'updated_time': hit['_source']['updated_time']
                }
                
                # Add highlights if available
                if 'highlight' in hit:
                    result['highlights'] = hit['highlight'].get('extracted_text', [])
                
                results.append(result)
            
            logger.info(f"Found {len(results)} results for query: '{query}'")
            return results
            
        except es_exceptions.NotFoundError:
            logger.warning(f"Index '{self.index_name}' not found")
            return []
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete_document(self, file_id: str) -> bool:
        """Delete a document"""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            self.client.delete(index=self.index_name, id=file_id, refresh='wait_for')
            logger.debug(f"Deleted document: {file_id}")
            return True
        except es_exceptions.NotFoundError:
            logger.warning(f"Document not found: {file_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    def document_exists(self, file_id: str) -> bool:
        """Check if document exists"""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            return bool(self.client.exists(index=self.index_name, id=file_id))
        except Exception:
            return False
    
    def get_document(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            response = self.client.get(index=self.index_name, id=file_id)
            return response['_source']
        except es_exceptions.NotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    def get_all_document_ids(self) -> List[str]:
        """Get all document IDs"""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            # Scroll through all documents
            response = self.client.search(
                index=self.index_name,
                query={"match_all": {}},
                source=False,
                size=1000,
                scroll='2m'
            )
            
            file_ids = [hit['_id'] for hit in response['hits']['hits']]
            
            # Handle pagination
            scroll_id = response.get('_scroll_id')
            while scroll_id and len(response['hits']['hits']) > 0:
                response = self.client.scroll(scroll_id=scroll_id, scroll='2m')
                file_ids.extend([hit['_id'] for hit in response['hits']['hits']])
                scroll_id = response.get('_scroll_id')
            
            return file_ids
            
        except es_exceptions.NotFoundError:
            return []
        except Exception as e:
            logger.error(f"Failed to get document IDs: {e}")
            return []
    
    def delete_index(self) -> bool:
        """Delete the entire index"""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            if self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
                logger.info(f"Deleted index '{self.index_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete index: {e}")
            return False
