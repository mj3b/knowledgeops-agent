"""
NAVO Main Application
Simple FastAPI server for Teams bot integration with Confluence and SharePoint
"""

import os
import logging
from fastapi import FastAPI, Request, Response
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from dotenv import load_dotenv

from bot import NAVOBot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NAVO Teams Bot",
    description="Microsoft Teams Knowledge Discovery Bot",
    version="1.0.0"
)

# Bot Framework authentication
auth_config = ConfigurationBotFrameworkAuthentication(
    app_id=os.getenv("TEAMS_APP_ID"),
    app_password=os.getenv("TEAMS_APP_PASSWORD")
)

# Create adapter and bot
adapter = CloudAdapter(auth_config)
bot = NAVOBot()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "NAVO Teams Bot is running",
        "version": "1.0.0",
        "description": "Microsoft Teams Knowledge Discovery Bot"
    }

@app.get("/health")
async def health():
    """Detailed health check with integration status"""
    integrations = {
        "confluence": bool(os.getenv("CONFLUENCE_CLOUD_URL") and 
                          os.getenv("CONFLUENCE_EMAIL") and 
                          os.getenv("CONFLUENCE_API_TOKEN")),
        "sharepoint": bool(os.getenv("SHAREPOINT_TENANT_ID") and 
                          os.getenv("SHAREPOINT_CLIENT_ID") and 
                          os.getenv("SHAREPOINT_CLIENT_SECRET")),
        "enterprise_gpt": bool(os.getenv("OPENAI_API_KEY")),
        "teams": bool(os.getenv("TEAMS_APP_ID") and 
                     os.getenv("TEAMS_APP_PASSWORD"))
    }
    
    all_configured = all(integrations.values())
    
    return {
        "status": "healthy" if all_configured else "partial",
        "bot": "active",
        "integrations": integrations,
        "ready": all_configured
    }

@app.post("/api/messages")
async def messages(request: Request):
    """Teams bot messaging endpoint"""
    try:
        body = await request.body()
        auth_header = request.headers.get("Authorization", "")
        
        response = await adapter.process_activity(
            body.decode(), 
            auth_header, 
            bot.on_message_activity
        )
        
        if response:
            return Response(content=response.body, status_code=response.status)
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing Teams message: {str(e)}")
        return Response(status_code=500)

@app.post("/api/v1/query")
async def query_endpoint(request: Request):
    """Direct query endpoint for testing"""
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            return {"error": "Query parameter required"}
        
        # Process query directly
        response = await bot.query_processor.process_query(query)
        
        return {
            "query": query,
            "response": response
        }
        
    except Exception as e:
        logger.error(f"Error processing direct query: {str(e)}")
        return {"error": "Internal server error"}

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting NAVO Teams Bot on {host}:{port}")
    logger.info("Integrations configured:")
    logger.info(f"  - Confluence: {bool(os.getenv('CONFLUENCE_CLOUD_URL'))}")
    logger.info(f"  - SharePoint: {bool(os.getenv('SHAREPOINT_TENANT_ID'))}")
    logger.info(f"  - Enterprise GPT: {bool(os.getenv('OPENAI_API_KEY'))}")
    logger.info(f"  - Teams: {bool(os.getenv('TEAMS_APP_ID'))}")
    
    uvicorn.run(app, host=host, port=port)

