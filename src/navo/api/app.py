"""
NAVO Enhanced API Application
Production-ready FastAPI application with Phase 3 & 4 capabilities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

from ..core.navo_engine import NAVOEngine
from ..core.source_coordinator import SourceCoordinator, CrossPlatformQuery, SourceType
from ..core.knowledge_lifecycle_manager import KnowledgeLifecycleManager
from ..core.memory_layer import NAVOMemoryLayer
from ..core.reasoning_engine import NAVOReasoningEngine
from ..core.cache_manager import CacheManager
from ..core.permission_manager import PermissionManager

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Request/Response Models
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    user_id: str = Field(..., description="User identifier")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    source_preferences: List[str] = Field(default_factory=list, description="Preferred sources")
    max_results: int = Field(default=10, description="Maximum results to return")
    enable_reasoning: bool = Field(default=True, description="Enable reasoning engine")
    enable_memory: bool = Field(default=True, description="Enable memory layer")

class QueryResponse(BaseModel):
    query_id: str
    response: str
    sources: List[Dict[str, Any]]
    reasoning: Optional[Dict[str, Any]] = None
    memory_context: Optional[Dict[str, Any]] = None
    response_time: float
    confidence_score: float
    suggestions: List[str] = Field(default_factory=list)

class ProactiveInsightsResponse(BaseModel):
    user_patterns: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    knowledge_gaps: List[Dict[str, Any]]
    predictive_suggestions: List[Dict[str, Any]]
    generated_at: str

class LifecycleDashboardResponse(BaseModel):
    lifecycle_distribution: Dict[str, int]
    knowledge_gaps: Dict[str, Any]
    recommendations: Dict[str, Any]
    predictive_cache: Dict[str, Any]
    performance: Dict[str, Any]
    last_updated: str

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    components: Dict[str, str]
    performance_metrics: Dict[str, Any]

# Global application state
app_state = {
    "navo_engine": None,
    "source_coordinator": None,
    "lifecycle_manager": None,
    "memory_layer": None,
    "reasoning_engine": None,
    "cache_manager": None,
    "permission_manager": None,
    "start_time": datetime.now()
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting NAVO Enterprise Knowledge Discovery Platform")
    
    try:
        # Initialize components
        config = app.state.config
        
        app_state["navo_engine"] = NAVOEngine(config)
        app_state["source_coordinator"] = SourceCoordinator(config)
        app_state["lifecycle_manager"] = KnowledgeLifecycleManager(config)
        app_state["memory_layer"] = NAVOMemoryLayer(config.get("memory", {}))
        app_state["reasoning_engine"] = NAVOReasoningEngine(config.get("reasoning", {}))
        app_state["cache_manager"] = CacheManager(config.get("cache", {}))
        app_state["permission_manager"] = PermissionManager(config.get("permissions", {}))
        
        # Initialize memory and reasoning
        await app_state["memory_layer"].initialize()
        await app_state["reasoning_engine"].initialize()
        
        # Start proactive management
        await app_state["lifecycle_manager"].start_proactive_management()
        
        logger.info("NAVO platform initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize NAVO platform: {str(e)}")
        raise
    
    # Shutdown
    logger.info("Shutting down NAVO platform")
    
    try:
        # Stop proactive management
        if app_state["lifecycle_manager"]:
            await app_state["lifecycle_manager"].stop_proactive_management()
        
        # Cleanup components
        if app_state["memory_layer"]:
            await app_state["memory_layer"].cleanup()
        
        if app_state["cache_manager"]:
            await app_state["cache_manager"].cleanup()
        
        logger.info("NAVO platform shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

def create_app(config: Dict[str, Any]) -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="NAVO - Enterprise Knowledge Discovery Platform",
        description="AI-powered conversational interface with transparent reasoning, memory, and continuous learning",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
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
    
    # Authentication dependency
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current user from authentication token."""
        if not credentials:
            return {"user_id": "anonymous", "permissions": {}}
        
        # In production, validate JWT token here
        # For now, return mock user
        return {"user_id": "authenticated_user", "permissions": {}}
    
    # API Routes
    
    @app.get("/", response_model=Dict[str, str])
    async def root():
        """Root endpoint with platform information."""
        return {
            "platform": "NAVO - Enterprise Knowledge Discovery Platform",
            "version": "2.0.0",
            "description": "AI-powered conversational interface with transparent reasoning, memory, and continuous learning",
            "status": "operational",
            "documentation": "/docs"
        }
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        try:
            uptime = (datetime.now() - app_state["start_time"]).total_seconds()
            
            # Check component health
            components = {}
            if app_state["source_coordinator"]:
                source_health = await app_state["source_coordinator"].get_source_health()
                components["sources"] = "healthy" if source_health else "degraded"
            
            if app_state["memory_layer"]:
                components["memory"] = "healthy"
            
            if app_state["reasoning_engine"]:
                components["reasoning"] = "healthy"
            
            if app_state["cache_manager"]:
                cache_stats = await app_state["cache_manager"].get_stats()
                components["cache"] = "healthy" if cache_stats else "degraded"
            
            # Get performance metrics
            performance_metrics = {}
            if app_state["source_coordinator"]:
                performance_metrics = await app_state["source_coordinator"].get_performance_metrics()
            
            return HealthResponse(
                status="healthy",
                version="2.0.0",
                uptime=uptime,
                components=components,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Health check failed")
    
    @app.post("/query", response_model=QueryResponse)
    async def query_knowledge(
        request: QueryRequest,
        background_tasks: BackgroundTasks,
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        """Process knowledge query with full NAVO capabilities."""
        start_time = datetime.now()
        
        try:
            # Create cross-platform query
            cross_platform_query = CrossPlatformQuery(
                query_id=f"query_{int(start_time.timestamp())}",
                text=request.query,
                user_id=request.user_id,
                intent="knowledge_discovery",
                context=request.context,
                source_preferences=[SourceType(s) for s in request.source_preferences if s in [st.value for st in SourceType]],
                max_results_per_source=request.max_results // 2  # Distribute across sources
            )
            
            # Execute unified search
            search_results = await app_state["source_coordinator"].unified_search(
                cross_platform_query, 
                current_user
            )
            
            # Apply reasoning if enabled
            reasoning_result = None
            if request.enable_reasoning and app_state["reasoning_engine"]:
                reasoning_result = await app_state["reasoning_engine"].analyze_query(
                    request.query,
                    search_results,
                    current_user
                )
            
            # Update memory if enabled
            memory_context = None
            if request.enable_memory and app_state["memory_layer"]:
                memory_context = await app_state["memory_layer"].store_interaction(
                    user_id=request.user_id,
                    query=request.query,
                    results=search_results,
                    reasoning=reasoning_result
                )
            
            # Generate response using NAVO engine
            response_text = await app_state["navo_engine"].generate_response(
                query=request.query,
                search_results=search_results,
                reasoning_result=reasoning_result,
                memory_context=memory_context,
                user_context=current_user
            )
            
            # Calculate response time and confidence
            response_time = (datetime.now() - start_time).total_seconds()
            confidence_score = reasoning_result.get("confidence", 0.8) if reasoning_result else 0.8
            
            # Generate suggestions
            suggestions = []
            if reasoning_result and reasoning_result.get("follow_up_questions"):
                suggestions = reasoning_result["follow_up_questions"][:3]
            
            # Background task: Update analytics
            background_tasks.add_task(
                update_query_analytics,
                request.query,
                request.user_id,
                len(search_results),
                response_time,
                confidence_score
            )
            
            return QueryResponse(
                query_id=cross_platform_query.query_id,
                response=response_text,
                sources=[
                    {
                        "id": result.content_id,
                        "title": result.title,
                        "url": result.url,
                        "source_type": result.source_type.value,
                        "relevance_score": result.relevance_score,
                        "freshness_score": result.freshness_score
                    }
                    for result in search_results[:request.max_results]
                ],
                reasoning=reasoning_result,
                memory_context=memory_context,
                response_time=response_time,
                confidence_score=confidence_score,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")
    
    @app.get("/insights/{user_id}", response_model=ProactiveInsightsResponse)
    async def get_proactive_insights(
        user_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        """Get proactive insights for a user."""
        try:
            # Verify user access
            if current_user["user_id"] != user_id and "admin" not in current_user.get("permissions", {}):
                raise HTTPException(status_code=403, detail="Access denied")
            
            insights = await app_state["lifecycle_manager"].get_proactive_insights(user_id)
            
            return ProactiveInsightsResponse(**insights)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Proactive insights failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate insights")
    
    @app.get("/dashboard/lifecycle", response_model=LifecycleDashboardResponse)
    async def get_lifecycle_dashboard(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        """Get knowledge lifecycle dashboard."""
        try:
            # Check admin permissions
            if "admin" not in current_user.get("permissions", {}):
                raise HTTPException(status_code=403, detail="Admin access required")
            
            dashboard_data = await app_state["lifecycle_manager"].get_lifecycle_dashboard()
            
            return LifecycleDashboardResponse(**dashboard_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Dashboard generation failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate dashboard")
    
    @app.get("/sources/health")
    async def get_sources_health(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        """Get health status of all knowledge sources."""
        try:
            health_status = await app_state["source_coordinator"].get_source_health()
            return {"sources": health_status}
            
        except Exception as e:
            logger.error(f"Source health check failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Source health check failed")
    
    @app.get("/performance/metrics")
    async def get_performance_metrics(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        """Get platform performance metrics."""
        try:
            metrics = await app_state["source_coordinator"].get_performance_metrics()
            return {"performance": metrics}
            
        except Exception as e:
            logger.error(f"Performance metrics failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get performance metrics")
    
    @app.post("/feedback")
    async def submit_feedback(
        query_id: str,
        rating: int = Field(..., ge=1, le=5),
        comment: str = "",
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        """Submit feedback for a query response."""
        try:
            # Store feedback in memory layer
            if app_state["memory_layer"]:
                await app_state["memory_layer"].store_feedback(
                    query_id=query_id,
                    user_id=current_user["user_id"],
                    rating=rating,
                    comment=comment
                )
            
            return {"status": "success", "message": "Feedback submitted"}
            
        except Exception as e:
            logger.error(f"Feedback submission failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to submit feedback")
    
    # WebSocket endpoint for real-time interactions
    @app.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket, user_id: str):
        """WebSocket endpoint for real-time knowledge discovery."""
        await websocket.accept()
        
        try:
            while True:
                # Receive query
                data = await websocket.receive_json()
                query = data.get("query", "")
                
                if not query:
                    await websocket.send_json({"error": "Query is required"})
                    continue
                
                # Process query (simplified)
                response = await process_websocket_query(query, user_id)
                
                # Send response
                await websocket.send_json(response)
                
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            await websocket.close()
    
    # Background task functions
    async def update_query_analytics(
        query: str, 
        user_id: str, 
        result_count: int, 
        response_time: float,
        confidence_score: float
    ):
        """Background task to update query analytics."""
        try:
            # Update analytics in memory layer
            if app_state["memory_layer"]:
                await app_state["memory_layer"].update_analytics({
                    "query": query,
                    "user_id": user_id,
                    "result_count": result_count,
                    "response_time": response_time,
                    "confidence_score": confidence_score,
                    "timestamp": datetime.now()
                })
        except Exception as e:
            logger.error(f"Analytics update failed: {str(e)}")
    
    async def process_websocket_query(query: str, user_id: str) -> Dict[str, Any]:
        """Process WebSocket query."""
        try:
            # Simplified query processing for WebSocket
            start_time = datetime.now()
            
            # Create basic query
            cross_platform_query = CrossPlatformQuery(
                query_id=f"ws_{int(start_time.timestamp())}",
                text=query,
                user_id=user_id,
                intent="realtime_query",
                context={"websocket": True},
                max_results_per_source=3
            )
            
            # Execute search
            results = await app_state["source_coordinator"].unified_search(
                cross_platform_query, 
                {"user_id": user_id}
            )
            
            # Generate response
            response_text = await app_state["navo_engine"].generate_response(
                query=query,
                search_results=results,
                user_context={"user_id": user_id}
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "query_id": cross_platform_query.query_id,
                "response": response_text,
                "source_count": len(results),
                "response_time": response_time
            }
            
        except Exception as e:
            logger.error(f"WebSocket query processing failed: {str(e)}")
            return {"error": str(e)}
    
    return app

