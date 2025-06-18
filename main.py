"""
NAVO Main Application
Simple FastAPI server for Teams bot
"""

import os
import logging
from fastapi import FastAPI, Request, Response
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from dotenv import load_dotenv

from src.navo.bot import NAVOBot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="NAVO Teams Bot", version="1.0.0")

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
    return {"status": "NAVO Teams Bot is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "bot": "active",
        "integrations": {
            "confluence": bool(os.getenv("CONFLUENCE_CLOUD_URL")),
            "sharepoint": bool(os.getenv("SHAREPOINT_TENANT_ID")),
            "enterprise_gpt": bool(os.getenv("OPENAI_API_KEY"))
        }
    }

@app.post("/api/messages")
async def messages(request: Request):
    """Teams bot messaging endpoint"""
    try:
        body = await request.body()
        auth_header = request.headers.get("Authorization", "")
        response = await adapter.process_activity(body.decode(), auth_header, bot.on_message_activity)
        
        if response:
            return Response(content=response.body, status_code=response.status)
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return Response(status_code=500)

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting NAVO Teams Bot on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

