#!/usr/bin/env python3
"""
KnowledgeOps Agent - Main Flask Application
Enterprise web application with REST API and web interface for unified knowledge search.
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
import threading
import time

# Import our unified knowledge manager
from unified_knowledge_manager import (
    UnifiedKnowledgeManager, SearchQuery, ConfluenceConfig, SharePointConfig
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
CORS(app)  # Enable CORS for API access

# Global knowledge manager instance
knowledge_manager = None
background_sync_task = None

# Configuration
CONFLUENCE_ENABLED = os.getenv("CONFLUENCE_ENABLED", "true").lower() == "true"
SHAREPOINT_ENABLED = os.getenv("SHAREPOINT_ENABLED", "true").lower() == "true"
AUTO_SYNC_INTERVAL = int(os.getenv("AUTO_SYNC_INTERVAL", "3600"))  # 1 hour default

def create_knowledge_manager():
    """Create and configure the knowledge manager"""
    confluence_config = None
    sharepoint_config = None
    
    # Configure Confluence if enabled
    if CONFLUENCE_ENABLED:
        confluence_config = ConfluenceConfig(
            base_url=os.getenv("CONFLUENCE_BASE_URL"),
            auth_type=os.getenv("CONFLUENCE_AUTH_TYPE", "api_token"),
            username=os.getenv("CONFLUENCE_USERNAME"),
            api_token=os.getenv("CONFLUENCE_API_TOKEN"),
            client_id=os.getenv("CONFLUENCE_CLIENT_ID"),
            client_secret=os.getenv("CONFLUENCE_CLIENT_SECRET"),
            spaces=os.getenv("CONFLUENCE_SPACES", "").split(",") if os.getenv("CONFLUENCE_SPACES") else None,
            max_results=int(os.getenv("CONFLUENCE_MAX_RESULTS", "100"))
        )
    
    # Configure SharePoint if enabled
    if SHAREPOINT_ENABLED:
        sharepoint_config = SharePointConfig(
            tenant_id=os.getenv("SHAREPOINT_TENANT_ID"),
            client_id=os.getenv("SHAREPOINT_CLIENT_ID"),
            client_secret=os.getenv("SHAREPOINT_CLIENT_SECRET"),
            sites=os.getenv("SHAREPOINT_SITES", "").split(",") if os.getenv("SHAREPOINT_SITES") else None,
            max_results=int(os.getenv("SHAREPOINT_MAX_RESULTS", "100"))
        )
    
    return UnifiedKnowledgeManager(confluence_config, sharepoint_config)

async def initialize_knowledge_manager():
    """Initialize the knowledge manager asynchronously"""
    global knowledge_manager
    
    try:
        knowledge_manager = create_knowledge_manager()
        await knowledge_manager.initialize()
        
        # Perform initial sync
        logger.info("Performing initial content synchronization...")
        await knowledge_manager.sync_all_content()
        
        logger.info("Knowledge manager initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize knowledge manager: {e}")
        return False

def run_async_in_thread(coro):
    """Run async function in a separate thread"""
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    thread = threading.Thread(target=run)
    thread.start()
    thread.join()

def background_sync():
    """Background task for periodic content synchronization"""
    while True:
        try:
            if knowledge_manager:
                logger.info("Starting background content sync")
                
                async def sync_task():
                    await knowledge_manager.sync_all_content()
                
                run_async_in_thread(sync_task())
                logger.info("Background content sync completed")
            
            time.sleep(AUTO_SYNC_INTERVAL)
        except Exception as e:
            logger.error(f"Error in background sync: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'services': {
            'confluence': CONFLUENCE_ENABLED and knowledge_manager is not None,
            'sharepoint': SHAREPOINT_ENABLED and knowledge_manager is not None
        }
    }
    
    if knowledge_manager:
        try:
            async def get_stats():
                return await knowledge_manager.get_content_stats()
            
            stats = asyncio.run(get_stats())
            status['content_stats'] = stats
        except Exception as e:
            status['error'] = str(e)
            status['status'] = 'degraded'
    
    return jsonify(status)

@app.route('/api/search', methods=['GET', 'POST'])
def search_content():
    """Search content across all sources"""
    if not knowledge_manager:
        return jsonify({'error': 'Knowledge manager not initialized'}), 503
    
    try:
        # Parse request parameters
        if request.method == 'GET':
            query_text = request.args.get('q', '')
            max_results = int(request.args.get('limit', 10))
            sources = request.args.getlist('sources')
            semantic_search = request.args.get('semantic', 'true').lower() == 'true'
            keyword_search = request.args.get('keyword', 'true').lower() == 'true'
            filters = {}
        else:
            data = request.get_json() or {}
            query_text = data.get('query', '')
            max_results = data.get('max_results', 10)
            sources = data.get('sources', [])
            semantic_search = data.get('semantic_search', True)
            keyword_search = data.get('keyword_search', True)
            filters = data.get('filters', {})
        
        if not query_text:
            return jsonify({'error': 'Query text is required'}), 400
        
        # Create search query
        search_query = SearchQuery(
            text=query_text,
            max_results=max_results,
            include_sources=sources if sources else None,
            semantic_search=semantic_search,
            keyword_search=keyword_search,
            filters=filters
        )
        
        # Perform search
        async def search_task():
            return await knowledge_manager.search(search_query)
        
        results = asyncio.run(search_task())
        
        # Format results for API response
        formatted_results = []
        for result in results:
            content = result.content
            formatted_result = {
                'id': content.id,
                'title': content.title,
                'summary': content.summary,
                'url': content.url,
                'source_type': content.source_type,
                'content_type': content.content_type,
                'author': content.author,
                'created_date': content.created_date.isoformat(),
                'modified_date': content.modified_date.isoformat(),
                'tags': content.tags,
                'relevance_score': result.relevance_score,
                'match_type': result.match_type,
                'context_snippet': result.context_snippet,
                'metadata': {
                    key: value for key, value in content.metadata.items()
                    if key not in ['confluence_data', 'sharepoint_data']
                }
            }
            formatted_results.append(formatted_result)
        
        response = {
            'query': query_text,
            'total_results': len(formatted_results),
            'results': formatted_results,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/content/<content_id>', methods=['GET'])
def get_content_by_id(content_id):
    """Get specific content by ID"""
    if not knowledge_manager:
        return jsonify({'error': 'Knowledge manager not initialized'}), 503
    
    try:
        async def get_content_task():
            return await knowledge_manager.get_content_by_id(content_id)
        
        content = asyncio.run(get_content_task())
        
        if not content:
            return jsonify({'error': 'Content not found'}), 404
        
        # Format content for API response
        formatted_content = {
            'id': content.id,
            'title': content.title,
            'content_text': content.content_text,
            'summary': content.summary,
            'url': content.url,
            'source_type': content.source_type,
            'content_type': content.content_type,
            'author': content.author,
            'created_date': content.created_date.isoformat(),
            'modified_date': content.modified_date.isoformat(),
            'tags': content.tags,
            'metadata': content.metadata
        }
        
        return jsonify(formatted_content)
    
    except Exception as e:
        logger.error(f"Error getting content {content_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync', methods=['POST'])
def trigger_sync():
    """Manually trigger content synchronization"""
    if not knowledge_manager:
        return jsonify({'error': 'Knowledge manager not initialized'}), 503
    
    try:
        force_full_sync = request.get_json().get('force_full_sync', False) if request.get_json() else False
        
        async def sync_task():
            await knowledge_manager.sync_all_content(force_full_sync=force_full_sync)
            return await knowledge_manager.get_content_stats()
        
        stats = asyncio.run(sync_task())
        
        return jsonify({
            'message': 'Content synchronization completed',
            'stats': stats,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_content_stats():
    """Get content statistics"""
    if not knowledge_manager:
        return jsonify({'error': 'Knowledge manager not initialized'}), 503
    
    try:
        async def stats_task():
            return await knowledge_manager.get_content_stats()
        
        stats = asyncio.run(stats_task())
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

# Web Interface Routes

@app.route('/')
def index():
    """Main web interface"""
    return render_template_string(WEB_INTERFACE_TEMPLATE)

@app.route('/search')
def search_page():
    """Search results page"""
    query = request.args.get('q', '')
    if not query:
        return render_template_string(WEB_INTERFACE_TEMPLATE)
    
    # Perform search via API
    try:
        search_query = SearchQuery(text=query, max_results=20)
        
        async def search_task():
            return await knowledge_manager.search(search_query)
        
        results = asyncio.run(search_task())
        
        return render_template_string(SEARCH_RESULTS_TEMPLATE, query=query, results=results)
    
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return render_template_string(ERROR_TEMPLATE, error=str(e))

# HTML Templates

WEB_INTERFACE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KnowledgeOps Agent</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .search-container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .search-box {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .search-button {
            background: #007acc;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
        }
        .search-button:hover {
            background: #005a9e;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .feature-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .feature-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .api-section {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 30px;
        }
        .code-block {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            overflow-x: auto;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 KnowledgeOps Agent</h1>
        <p>Intelligent knowledge discovery across Confluence and SharePoint</p>
    </div>

    <div class="search-container">
        <form action="/search" method="get">
            <input type="text" name="q" class="search-box" placeholder="Ask me anything about your organization's knowledge..." required>
            <button type="submit" class="search-button">Search Knowledge Base</button>
        </form>
    </div>

    <div class="features">
        <div class="feature-card">
            <div class="feature-title">🤖 AI-Powered Search</div>
            <p>Natural language queries with semantic understanding. Ask questions like "How do I deploy to production?" or "What are the security policies?"</p>
        </div>
        
        <div class="feature-card">
            <div class="feature-title">🔗 Multi-Platform Integration</div>
            <p>Searches across Confluence and SharePoint simultaneously, providing unified results from all your knowledge sources.</p>
        </div>
        
        <div class="feature-card">
            <div class="feature-title">🎯 Intelligent Ranking</div>
            <p>Results ranked by relevance using both semantic similarity and keyword matching for the most accurate results.</p>
        </div>
        
        <div class="feature-card">
            <div class="feature-title">🔒 Security Aware</div>
            <p>Respects existing permissions and access controls. You only see content you're authorized to access.</p>
        </div>
    </div>

    <div class="api-section">
        <h2>API Access</h2>
        <p>Integrate KnowledgeOps Agent into your applications using our REST API:</p>
        
        <h3>Search Content</h3>
        <div class="code-block">
GET /api/search?q=deployment+procedures&limit=10
        </div>
        
        <h3>Get Content by ID</h3>
        <div class="code-block">
GET /api/content/{content_id}
        </div>
        
        <h3>Health Check</h3>
        <div class="code-block">
GET /api/health
        </div>
        
        <h3>Content Statistics</h3>
        <div class="code-block">
GET /api/stats
        </div>
    </div>

    <script>
        // Auto-focus search box
        document.querySelector('.search-box').focus();
        
        // Handle form submission
        document.querySelector('form').addEventListener('submit', function(e) {
            const query = document.querySelector('.search-box').value.trim();
            if (!query) {
                e.preventDefault();
                alert('Please enter a search query');
            }
        });
    </script>
</body>
</html>
"""

SEARCH_RESULTS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Results - KnowledgeOps Agent</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .search-box {
            width: 70%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-right: 10px;
        }
        .search-button {
            background: #007acc;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
        }
        .results-info {
            margin: 20px 0;
            color: #666;
        }
        .result-item {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 15px;
        }
        .result-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .result-title a {
            color: #007acc;
            text-decoration: none;
        }
        .result-title a:hover {
            text-decoration: underline;
        }
        .result-meta {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .result-snippet {
            line-height: 1.5;
            margin-bottom: 10px;
        }
        .result-tags {
            margin-top: 10px;
        }
        .tag {
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 5px;
        }
        .source-badge {
            background: #4caf50;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            text-transform: uppercase;
        }
        .source-badge.sharepoint {
            background: #ff9800;
        }
        .relevance-score {
            float: right;
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 KnowledgeOps Agent</h1>
        <form action="/search" method="get">
            <input type="text" name="q" class="search-box" value="{{ query }}" required>
            <button type="submit" class="search-button">Search</button>
        </form>
    </div>

    <div class="results-info">
        Found {{ results|length }} results for "{{ query }}"
    </div>

    {% for result in results %}
    <div class="result-item">
        <div class="result-title">
            <a href="{{ result.content.url }}" target="_blank">{{ result.content.title }}</a>
            <span class="relevance-score">{{ "%.3f"|format(result.relevance_score) }}</span>
        </div>
        
        <div class="result-meta">
            <span class="source-badge {{ result.content.source_type }}">{{ result.content.source_type }}</span>
            by {{ result.content.author }} • 
            {{ result.content.modified_date.strftime('%Y-%m-%d') }} •
            {{ result.match_type }} match
        </div>
        
        <div class="result-snippet">
            {{ result.context_snippet }}
        </div>
        
        {% if result.content.tags %}
        <div class="result-tags">
            {% for tag in result.content.tags[:5] %}
            <span class="tag">{{ tag }}</span>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    {% endfor %}

    {% if not results %}
    <div class="result-item">
        <h3>No results found</h3>
        <p>Try different keywords or check if the content exists in your knowledge base.</p>
    </div>
    {% endif %}
</body>
</html>
"""

ERROR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - KnowledgeOps Agent</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
        }
        .error-container {
            background: #ffebee;
            border: 1px solid #f44336;
            border-radius: 10px;
            padding: 30px;
        }
        .error-title {
            color: #f44336;
            font-size: 24px;
            margin-bottom: 15px;
        }
        .back-link {
            margin-top: 20px;
        }
        .back-link a {
            color: #007acc;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-title">⚠️ Error</div>
        <p>{{ error }}</p>
        <div class="back-link">
            <a href="/">← Back to Search</a>
        </div>
    </div>
</body>
</html>
"""

# Application startup
def startup():
    """Initialize the application"""
    global background_sync_task
    
    logger.info("Starting KnowledgeOps Agent application")
    
    # Initialize knowledge manager
    success = asyncio.run(initialize_knowledge_manager())
    
    if not success:
        logger.error("Failed to initialize knowledge manager")
        return False
    
    # Start background sync task
    if AUTO_SYNC_INTERVAL > 0:
        background_sync_task = threading.Thread(target=background_sync, daemon=True)
        background_sync_task.start()
        logger.info(f"Background sync started with {AUTO_SYNC_INTERVAL}s interval")
    
    logger.info("KnowledgeOps Agent application started successfully")
    return True

# Cleanup on shutdown
@app.teardown_appcontext
def cleanup(error):
    """Cleanup resources"""
    if knowledge_manager:
        asyncio.run(knowledge_manager.close())

if __name__ == '__main__':
    # Initialize application
    if startup():
        # Run Flask app
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug,
            threaded=True
        )
    else:
        logger.error("Application startup failed")
        exit(1)

