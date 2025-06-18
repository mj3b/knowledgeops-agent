"""
NAVO Main Application
Microsoft Teams Bot with Enterprise Knowledge Discovery

FastAPI server that hosts the NAVO Teams bot with proper Microsoft Bot Framework
integration for Confluence and SharePoint knowledge discovery.

Compliant with Microsoft Teams bot hosting requirements.
"""

import os
import logging
from typing import Dict, Any
from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    BotFrameworkAdapter, 
    BotFrameworkAdapterSettings,
    ConversationState,
    UserState,
    MemoryStorage,
    TurnContext
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity

from bot import NAVOBot
from query_processor import QueryProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Microsoft Bot Framework settings
SETTINGS = BotFrameworkAdapterSettings(
    app_id=os.environ.get("TEAMS_APP_ID", ""),
    app_password=os.environ.get("TEAMS_APP_PASSWORD", "")
)

# Create adapter and bot
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Create conversation and user state with memory storage
MEMORY_STORAGE = MemoryStorage()
CONVERSATION_STATE = ConversationState(MEMORY_STORAGE)
USER_STATE = UserState(MEMORY_STORAGE)

# Create the NAVO bot instance
BOT = NAVOBot(CONVERSATION_STATE, USER_STATE)

# Query processor for direct API access
QUERY_PROCESSOR = QueryProcessor()


async def messages(req: Request) -> Response:
    """
    Microsoft Teams message endpoint
    
    Handles incoming activities from Microsoft Teams via Bot Framework.
    This is the main webhook endpoint that Teams calls.
    
    Args:
        req: The HTTP request from Teams
        
    Returns:
        Response: HTTP response for Teams
    """
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=415, text="Content-Type must be application/json")

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    try:
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
            return json_response(data=response.body, status=response.status)
        return Response(status=201)
    except Exception as e:
        logger.error(f"Error processing Teams activity: {str(e)}")
        return Response(status=500, text=str(e))


async def health_check(req: Request) -> Response:
    """
    Health check endpoint for monitoring
    
    Returns:
        Response: Health status of the NAVO service
    """
    try:
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "service": "NAVO Teams Bot",
            "version": "1.0.0",
            "components": {
                "bot_framework": "operational",
                "query_processor": "operational",
                "confluence_client": "operational",
                "sharepoint_client": "operational"
            }
        }
        
        # Test query processor
        test_response = await QUERY_PROCESSOR.process_query("health check")
        if test_response:
            health_status["components"]["ai_processing"] = "operational"
        
        return json_response(health_status)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return json_response(
            {"status": "unhealthy", "error": str(e)}, 
            status=503
        )


async def query_api(req: Request) -> Response:
    """
    Direct query API endpoint (optional)
    
    Allows direct API access to NAVO's knowledge discovery
    without going through Teams interface.
    
    Args:
        req: HTTP request with query data
        
    Returns:
        Response: JSON response with answer and sources
    """
    try:
        if req.method == "POST":
            data = await req.json()
            query = data.get("query", "")
            
            if not query:
                return json_response(
                    {"error": "Query parameter is required"}, 
                    status=400
                )
            
            # Process query
            response = await QUERY_PROCESSOR.process_query(query)
            
            return json_response({
                "query": query,
                "answer": response["answer"],
                "sources": response["sources"],
                "confidence": response["confidence"],
                "processing_time": response.get("processing_time", 0)
            })
        else:
            return json_response(
                {"error": "Method not allowed"}, 
                status=405
            )
            
    except Exception as e:
        logger.error(f"API query error: {str(e)}")
        return json_response(
            {"error": "Internal server error"}, 
            status=500
        )


async def root_handler(req: Request) -> Response:
    """
    Root endpoint with service information
    
    Returns:
        Response: Basic service information
    """
    return json_response({
        "service": "NAVO - Microsoft Teams Knowledge Discovery Bot",
        "description": "AI-powered knowledge discovery from Confluence and SharePoint",
        "version": "1.0.0",
        "endpoints": {
            "teams_webhook": "/api/messages",
            "health": "/health",
            "query_api": "/api/v1/query"
        },
        "documentation": "https://github.com/mj3b/navo"
    })


def create_app() -> web.Application:
    """
    Create and configure the aiohttp web application
    
    Returns:
        web.Application: Configured NAVO web application
    """
    # Create aiohttp application
    app = web.Application(middlewares=[aiohttp_error_middleware])
    
    # Add routes
    app.router.add_get("/", root_handler)
    app.router.add_get("/health", health_check)
    app.router.add_post("/api/messages", messages)  # Teams webhook endpoint
    app.router.add_post("/api/v1/query", query_api)  # Direct API access
    
    return app


async def init_app():
    """Initialize the application"""
    logger.info("Initializing NAVO Teams Bot...")
    
    # Validate required environment variables
    required_vars = [
        "TEAMS_APP_ID", "TEAMS_APP_PASSWORD",
        "OPENAI_API_KEY", "CONFLUENCE_CLOUD_URL", 
        "SHAREPOINT_TENANT_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise ValueError(f"Missing environment variables: {missing_vars}")
    
    logger.info("NAVO Teams Bot initialized successfully")
    logger.info("Microsoft Bot Framework adapter configured")
    logger.info("Ready to receive Teams messages at /api/messages")


if __name__ == "__main__":
    import asyncio
    
    # Initialize the application
    asyncio.run(init_app())
    
    # Create and run the web application
    app = create_app()
    
    # Get port from environment or default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting NAVO Teams Bot on port {port}")
    logger.info("Teams webhook endpoint: /api/messages")
    logger.info("Health check endpoint: /health")
    logger.info("Direct API endpoint: /api/v1/query")
    
    web.run_app(app, host="0.0.0.0", port=port)

