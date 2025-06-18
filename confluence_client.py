"""
Confluence Cloud Client
Handles search and content retrieval from Confluence Cloud API
for NAVO knowledge discovery
"""

import os
import logging
import base64
from typing import List, Dict, Any
import aiohttp
from urllib.parse import quote

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """
    Client for Confluence Cloud REST API v2
    Provides search and content retrieval capabilities
    """
    
    def __init__(self):
        self.base_url = os.getenv("CONFLUENCE_CLOUD_URL")
        self.email = os.getenv("CONFLUENCE_EMAIL")
        self.api_token = os.getenv("CONFLUENCE_API_TOKEN")
        
        # Validate configuration
        if not all([self.base_url, self.email, self.api_token]):
            logger.warning("Confluence configuration incomplete - some environment variables missing")
            self.enabled = False
        else:
            self.enabled = True
            self._setup_authentication()
            logger.info("Confluence client initialized successfully")
    
    def _setup_authentication(self):
        """Setup basic authentication headers for Confluence Cloud API"""
        auth_string = f"{self.email}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search Confluence for relevant content using CQL
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of search results with title, content, URL, and metadata
        """
        if not self.enabled:
            logger.warning("Confluence client not enabled - skipping search")
            return []
        
        try:
            logger.info(f"Searching Confluence for: {query}")
            
            # Use Confluence Cloud search API with CQL
            search_url = f"{self.base_url}/rest/api/search"
            
            # Build CQL query for pages containing the search terms
            cql_query = f'text ~ "{query}" AND type = "page"'
            
            params = {
                "cql": cql_query,
                "limit": limit,
                "expand": "content.body.storage,content.space,content.version,content.history"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    search_url, 
                    headers=self.headers, 
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        results = self._parse_search_results(data)
                        logger.info(f"Found {len(results)} Confluence results")
                        return results
                    elif response.status == 401:
                        logger.error("Confluence authentication failed - check API token")
                        return []
                    elif response.status == 403:
                        logger.error("Confluence access forbidden - check permissions")
                        return []
                    else:
                        logger.error(f"Confluence search failed with status: {response.status}")
                        return []
                        
        except aiohttp.ClientError as e:
            logger.error(f"Confluence network error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Confluence search error: {str(e)}")
            return []
    
    def _parse_search_results(self, data: Dict) -> List[Dict[str, Any]]:
        """
        Parse Confluence search API response
        
        Args:
            data: Raw API response data
            
        Returns:
            List of formatted search results
        """
        results = []
        
        for item in data.get("results", []):
            try:
                content = item.get("content", {})
                
                # Extract basic information
                title = content.get("title", "Untitled Page")
                content_id = content.get("id", "")
                
                # Build web URL
                web_path = content.get("_links", {}).get("webui", "")
                web_url = f"{self.base_url}{web_path}" if web_path else ""
                
                # Extract text content from storage format
                body = content.get("body", {}).get("storage", {}).get("value", "")
                text_content = self._extract_text_content(body)
                
                # Get metadata
                space_name = content.get("space", {}).get("name", "Unknown Space")
                version_info = content.get("version", {})
                last_modified = version_info.get("when", "Unknown")
                
                # Get author information if available
                author = "Unknown"
                history = content.get("history", {})
                if history and "lastUpdated" in history:
                    author_info = history["lastUpdated"].get("by", {})
                    author = author_info.get("displayName", "Unknown")
                
                result = {
                    "title": title,
                    "url": web_url,
                    "content": text_content,
                    "source": "Confluence",
                    "last_modified": last_modified,
                    "space": space_name,
                    "author": author,
                    "content_id": content_id
                }
                
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Error parsing Confluence result: {str(e)}")
                continue
        
        return results
    
    def _extract_text_content(self, html_content: str) -> str:
        """
        Extract plain text from Confluence storage format HTML
        
        Args:
            html_content: HTML content from Confluence storage format
            
        Returns:
            Plain text content with basic formatting preserved
        """
        if not html_content:
            return ""
        
        try:
            import re
            
            # Remove script and style elements
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Convert common HTML elements to readable text
            html_content = re.sub(r'<br[^>]*>', '\n', html_content)
            html_content = re.sub(r'<p[^>]*>', '\n', html_content)
            html_content = re.sub(r'</p>', '\n', html_content)
            html_content = re.sub(r'<h[1-6][^>]*>', '\n## ', html_content)
            html_content = re.sub(r'</h[1-6]>', '\n', html_content)
            html_content = re.sub(r'<li[^>]*>', '\n• ', html_content)
            
            # Remove all remaining HTML tags
            text_content = re.sub(r'<[^>]+>', '', html_content)
            
            # Clean up whitespace
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
            text_content = re.sub(r'[ \t]+', ' ', text_content)
            text_content = text_content.strip()
            
            # Limit content length for processing
            if len(text_content) > 2000:
                text_content = text_content[:2000] + "..."
            
            return text_content
            
        except Exception as e:
            logger.warning(f"Error extracting text content: {str(e)}")
            return html_content[:500] if html_content else ""

