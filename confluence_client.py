"""
Confluence Cloud Client
Handles search and content retrieval from Confluence Cloud
"""

import os
import logging
from typing import List, Dict, Any
import aiohttp
import base64
from urllib.parse import quote

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """
    Client for Confluence Cloud API
    """
    
    def __init__(self):
        self.base_url = os.getenv("CONFLUENCE_CLOUD_URL")
        self.email = os.getenv("CONFLUENCE_EMAIL")
        self.api_token = os.getenv("CONFLUENCE_API_TOKEN")
        
        if not all([self.base_url, self.email, self.api_token]):
            logger.warning("Confluence configuration incomplete")
            self.enabled = False
        else:
            self.enabled = True
            # Create basic auth header
            auth_string = f"{self.email}:{self.api_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            self.headers = {
                "Authorization": f"Basic {auth_b64}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            logger.info("Confluence client initialized")
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Confluence for relevant content
        """
        if not self.enabled:
            logger.warning("Confluence client not enabled")
            return []
        
        try:
            # Use Confluence Cloud search API
            search_url = f"{self.base_url}/rest/api/search"
            
            params = {
                "cql": f'text ~ "{query}" AND type = "page"',
                "limit": 10,
                "expand": "content.body.storage,content.space,content.version"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_search_results(data)
                    else:
                        logger.error(f"Confluence search failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Confluence search error: {str(e)}")
            return []
    
    def _parse_search_results(self, data: Dict) -> List[Dict[str, Any]]:
        """
        Parse Confluence search results
        """
        results = []
        
        for item in data.get("results", []):
            content = item.get("content", {})
            
            # Extract text content from storage format
            body = content.get("body", {}).get("storage", {}).get("value", "")
            # Simple HTML tag removal for preview
            import re
            text_content = re.sub(r'<[^>]+>', '', body)
            
            result = {
                "title": content.get("title", "Untitled"),
                "url": f"{self.base_url}{content.get('_links', {}).get('webui', '')}",
                "content": text_content[:1000],  # Limit content length
                "source": "Confluence",
                "last_modified": content.get("version", {}).get("when", "Unknown"),
                "space": content.get("space", {}).get("name", "Unknown")
            }
            
            results.append(result)
        
        return results

