"""
NAVO FastAPI Application
Main web application and API endpoints for NAVO.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from ..core.navo_engine import NAVOEngine, NAVOQuery, NAVOResponse
from ..core.cache_manager import CacheManager
from .middleware.auth import AuthMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.logging import LoggingMiddleware

logger = logging.getLogger(__name__)


# Pydantic models for API
class QueryRequest(BaseModel):
    """Request model for queries."""
    text: str = Field(..., min_length=1, max_length=1000, description="Query text")
    user_id: str = Field(..., description="User identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")


class QueryResponse(BaseModel):
    """Response model for queries."""
    query_id: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    processing_time: float
    follow_up_questions: Optional[List[str]] = None
    timestamp: str


class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str
    timestamp: str
    components: Dict[str, Any]
    version: str = "2.0.0"


class MetricsResponse(BaseModel):
    """Response model for metrics."""
    queries_processed: int
    cache_hit_rate: float
    average_response_time: float
    active_integrations: int
    timestamp: str


# Global NAVO engine instance
navo_engine: Optional[NAVOEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global navo_engine
    
    # Startup
    logger.info("Starting NAVO application...")
    
    # Initialize NAVO engine with configuration
    config = app.state.config
    navo_engine = NAVOEngine(config)
    
    logger.info("NAVO application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NAVO application...")
    
    if navo_engine:
        # Close any open connections
        if hasattr(navo_engine, 'openai_client'):
            await navo_engine.openai_client.close()
        if hasattr(navo_engine, 'cache_manager'):
            await navo_engine.cache_manager.close()
        if hasattr(navo_engine, 'confluence_client') and navo_engine.confluence_client:
            await navo_engine.confluence_client.close()
        if hasattr(navo_engine, 'sharepoint_client') and navo_engine.sharepoint_client:
            await navo_engine.sharepoint_client.close()
    
    logger.info("NAVO application shutdown complete")


def create_app(config: Dict[str, Any]) -> FastAPI:
    """
    Create and configure the NAVO FastAPI application.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="NAVO - Navigate + Ops",
        description="T-Mobile Enterprise knowledge discovery platform with Enterprise GPT integration",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan
    )
    
    # Store config in app state
    app.state.config = config
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get("cors", {}).get("allowed_origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, config=config.get("rate_limiting", {}))
    
    # Add authentication middleware if enabled
    if config.get("authentication", {}).get("enabled", False):
        app.add_middleware(AuthMiddleware, config=config.get("authentication", {}))
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="src/navo/web/static"), name="static")
    
    # Templates
    templates = Jinja2Templates(directory="src/navo/web/templates")
    
    # API Routes
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Serve the main NAVO interface."""
        return templates.TemplateResponse("index.html", {
            "request": request,
            "title": "NAVO - Navigate + Ops",
            "tagline": "NAVO knows where it's written."
        })
    
    @app.post("/api/v1/query", response_model=QueryResponse)
    async def query(request: QueryRequest, background_tasks: BackgroundTasks) -> QueryResponse:
        """
        Process a user query and return an intelligent response.
        
        Args:
            request: Query request containing text and metadata
            background_tasks: FastAPI background tasks
            
        Returns:
            Query response with answer and sources
        """
        if not navo_engine:
            raise HTTPException(status_code=503, detail="NAVO engine not initialized")
        
        try:
            # Create NAVO query
            navo_query = NAVOQuery(
                text=request.text,
                user_id=request.user_id,
                context=request.context,
                filters=request.filters
            )
            
            # Process the query
            response = await navo_engine.process_query(navo_query)
            
            # Log query for analytics (background task)
            background_tasks.add_task(log_query_analytics, navo_query, response)
            
            return QueryResponse(
                query_id=response.query_id,
                answer=response.answer,
                sources=response.sources,
                confidence=response.confidence,
                processing_time=response.processing_time,
                follow_up_questions=getattr(response, 'follow_up_questions', None),
                timestamp=response.timestamp.isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/api/v1/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """
        Perform comprehensive health check of all NAVO components.
        
        Returns:
            Health status of all components
        """
        if not navo_engine:
            return HealthResponse(
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                components={"navo_engine": "not_initialized"}
            )
        
        try:
            health_status = await navo_engine.health_check()
            
            return HealthResponse(
                status=health_status["status"],
                timestamp=health_status["timestamp"],
                components=health_status["components"]
            )
            
        except Exception as e:
            logger.error(f"Error in health check: {str(e)}")
            return HealthResponse(
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                components={"error": str(e)}
            )
    
    @app.get("/api/v1/metrics", response_model=MetricsResponse)
    async def get_metrics() -> MetricsResponse:
        """
        Get NAVO performance and usage metrics.
        
        Returns:
            Performance and usage metrics
        """
        if not navo_engine:
            raise HTTPException(status_code=503, detail="NAVO engine not initialized")
        
        try:
            metrics = await navo_engine.get_metrics()
            
            return MetricsResponse(
                queries_processed=metrics["queries_processed"],
                cache_hit_rate=metrics["cache_hit_rate"],
                average_response_time=metrics["average_response_time"],
                active_integrations=metrics["active_integrations"],
                timestamp=metrics["timestamp"]
            )
            
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.post("/api/v1/cache/invalidate")
    async def invalidate_cache(pattern: str = "*") -> Dict[str, Any]:
        """
        Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Cache key pattern to invalidate
            
        Returns:
            Invalidation results
        """
        if not navo_engine:
            raise HTTPException(status_code=503, detail="NAVO engine not initialized")
        
        try:
            deleted_count = await navo_engine.cache_manager.invalidate_cache(pattern)
            
            return {
                "status": "success",
                "deleted_count": deleted_count,
                "pattern": pattern,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/api/v1/cache/stats")
    async def get_cache_stats() -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        if not navo_engine:
            raise HTTPException(status_code=503, detail="NAVO engine not initialized")
        
        try:
            stats = await navo_engine.cache_manager.get_cache_stats()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.post("/api/v1/sync/confluence")
    async def sync_confluence(
        background_tasks: BackgroundTasks,
        spaces: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Trigger Confluence synchronization.
        
        Args:
            background_tasks: FastAPI background tasks
            spaces: Optional list of spaces to sync
            
        Returns:
            Sync initiation status
        """
        if not navo_engine or not navo_engine.confluence_client:
            raise HTTPException(status_code=503, detail="Confluence integration not available")
        
        # Start sync in background
        background_tasks.add_task(run_confluence_sync, spaces)
        
        return {
            "status": "initiated",
            "message": "Confluence sync started in background",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @app.post("/api/v1/sync/sharepoint")
    async def sync_sharepoint(
        background_tasks: BackgroundTasks,
        sites: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Trigger SharePoint synchronization.
        
        Args:
            background_tasks: FastAPI background tasks
            sites: Optional list of sites to sync
            
        Returns:
            Sync initiation status
        """
        if not navo_engine or not navo_engine.sharepoint_client:
            raise HTTPException(status_code=503, detail="SharePoint integration not available")
        
        # Start sync in background
        background_tasks.add_task(run_sharepoint_sync, sites)
        
        return {
            "status": "initiated",
            "message": "SharePoint sync started in background",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @app.get("/api/v1/integrations/status")
    async def get_integration_status() -> Dict[str, Any]:
        """
        Get status of all integrations.
        
        Returns:
            Integration status information
        """
        if not navo_engine:
            raise HTTPException(status_code=503, detail="NAVO engine not initialized")
        
        status = {
            "openai_enterprise": {
                "enabled": True,
                "status": "unknown"
            },
            "confluence": {
                "enabled": navo_engine.confluence_client is not None,
                "status": "unknown"
            },
            "sharepoint": {
                "enabled": navo_engine.sharepoint_client is not None,
                "status": "unknown"
            }
        }
        
        try:
            # Check OpenAI Enterprise status
            openai_health = await navo_engine.openai_client.health_check()
            status["openai_enterprise"]["status"] = openai_health["status"]
            
            # Check Confluence status
            if navo_engine.confluence_client:
                confluence_health = await navo_engine.confluence_client.health_check()
                status["confluence"]["status"] = confluence_health["status"]
            
            # Check SharePoint status
            if navo_engine.sharepoint_client:
                sharepoint_health = await navo_engine.sharepoint_client.health_check()
                status["sharepoint"]["status"] = sharepoint_health["status"]
                
        except Exception as e:
            logger.error(f"Error checking integration status: {str(e)}")
        
        return {
            "integrations": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Error handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        """Handle 404 errors."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": "The requested resource was not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return app


async def log_query_analytics(query: NAVOQuery, response: NAVOResponse):
    """
    Log query analytics for monitoring and improvement.
    
    Args:
        query: The original query
        response: The generated response
    """
    try:
        # In a real implementation, this would log to analytics system
        analytics_data = {
            "query_id": response.query_id,
            "user_id": query.user_id,
            "query_text": query.text,
            "query_length": len(query.text),
            "response_confidence": response.confidence,
            "processing_time": response.processing_time,
            "sources_count": len(response.sources),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Query analytics: {analytics_data}")
        
    except Exception as e:
        logger.error(f"Error logging analytics: {str(e)}")


async def run_confluence_sync(spaces: Optional[List[str]] = None):
    """
    Run Confluence synchronization in background.
    
    Args:
        spaces: Optional list of spaces to sync
    """
    try:
        if navo_engine and navo_engine.confluence_client:
            logger.info("Starting background Confluence sync")
            results = await navo_engine.confluence_client.sync_spaces(spaces)
            logger.info(f"Confluence sync completed: {results}")
        
    except Exception as e:
        logger.error(f"Error in background Confluence sync: {str(e)}")


async def run_sharepoint_sync(sites: Optional[List[str]] = None):
    """
    Run SharePoint synchronization in background.
    
    Args:
        sites: Optional list of sites to sync
    """
    try:
        if navo_engine and navo_engine.sharepoint_client:
            logger.info("Starting background SharePoint sync")
            results = await navo_engine.sharepoint_client.sync_sites(sites)
            logger.info(f"SharePoint sync completed: {results}")
        
    except Exception as e:
        logger.error(f"Error in background SharePoint sync: {str(e)}")

