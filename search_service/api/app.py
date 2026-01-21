"""
FastAPI application for document search service.
Provides REST API endpoints for searching indexed documents.
"""
import logging
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..indexer.elastic_indexer import ElasticIndexer
from ..config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global indexer instance
indexer: Optional[ElasticIndexer] = None


# Pydantic models for API responses
class SearchResult(BaseModel):
    """Single search result"""
    file_name: str = Field(..., description="Name of the file")
    file_path: str = Field(..., description="Full path to the file")
    url: str = Field(..., description="Direct link to the file")
    mime_type: str = Field(..., description="MIME type of the file")
    score: float = Field(..., description="Relevance score")
    updated_time: str = Field(..., description="Last modified time")
    highlights: Optional[List[str]] = Field(None, description="Text snippets with matches")


class SearchResponse(BaseModel):
    """Search API response"""
    query: str = Field(..., description="The search query")
    total_results: int = Field(..., description="Number of results found")
    results: List[SearchResult] = Field(..., description="List of matching documents")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    elasticsearch_connected: bool = Field(..., description="Elasticsearch connection status")
    index_name: str = Field(..., description="Name of the search index")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global indexer
    
    # Startup: Connect to Elasticsearch
    logger.info("Starting up Document Search Service...")
    indexer = ElasticIndexer()
    
    if indexer.connect():
        logger.info("Connected to Elasticsearch")
        
        # Ensure index exists
        if not indexer.create_index():
            logger.warning("Index already exists or creation failed")
    else:
        logger.error("Failed to connect to Elasticsearch")
        logger.error("Make sure Elasticsearch is running: docker compose up -d")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Document Search Service...")


# Create FastAPI app
app = FastAPI(
    title="Document Search API",
    description="Search documents from Google Drive indexed in Elasticsearch",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Root endpoint")
async def root():
    """Root endpoint - returns service information"""
    return {
        "service": "Document Search API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/search?q=<query>&limit=<optional_limit>",
            "health": "/health"
        }
    }


@app.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """
    Health check endpoint.
    Returns service status and Elasticsearch connection status.
    """
    if not indexer:
        return HealthResponse(
            status="error",
            elasticsearch_connected=False,
            index_name=settings.elasticsearch_index
        )
    
    # Test Elasticsearch connection
    es_connected = False
    try:
        if indexer.client and indexer.client.ping():
            es_connected = True
    except Exception:
        pass
    
    status = "healthy" if es_connected else "unhealthy"
    
    return HealthResponse(
        status=status,
        elasticsearch_connected=es_connected,
        index_name=settings.elasticsearch_index
    )


@app.get(
    "/search",
    response_model=SearchResponse,
    summary="Search documents",
    responses={
        200: {"description": "Search results"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def search_documents(
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100)
):
    """
    Search for documents matching the query.
    
    - **q**: Search query string (required)
    - **limit**: Maximum number of results to return (default: 10, max: 100)
    
    Returns a list of matching documents with relevance scores and highlighted snippets.
    """
    if not indexer:
        raise HTTPException(
            status_code=500,
            detail="Search service not initialized. Elasticsearch connection failed."
        )
    
    try:
        # Perform search
        results = indexer.search(query=q, limit=limit)
        
        # Convert to response model
        search_results = [
            SearchResult(
                file_name=result['file_name'],
                file_path=result['file_path'],
                url=result['url'],
                mime_type=result['mime_type'],
                score=round(result['score'], 2),
                updated_time=result['updated_time'],
                highlights=result.get('highlights', [])
            )
            for result in results
        ]
        
        return SearchResponse(
            query=q,
            total_results=len(search_results),
            results=search_results
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/stats", summary="Index statistics")
async def get_stats():
    """
    Get index statistics.
    Returns information about indexed documents.
    """
    if not indexer:
        raise HTTPException(
            status_code=500,
            detail="Search service not initialized"
        )
    
    try:
        # Get all document IDs
        doc_ids = indexer.get_all_document_ids()
        
        return {
            "total_documents": len(doc_ids),
            "index_name": settings.elasticsearch_index,
            "elasticsearch_host": settings.elasticsearch_host
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        "search_service.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )
