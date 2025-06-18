"""
SharePoint Online Client
Handles search and content retrieval from SharePoint Online via Microsoft Graph
"""

import os
import logging
from typing import List, Dict, Any
import aiohttp

logger = logging.getLogger(__name__)


class SharePointClient:
    """
    Client for SharePoint Online via Microsoft Graph API
    """
    
    def __init__(self):
        self.tenant_id = os.getenv("SHAREPOINT_TENANT_ID")
        self.client_id = os.getenv("SHAREPOINT_CLIENT_ID")
        self.client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET")
        self.site_url = os.getenv("SHAREPOINT_SITE_URL")
        
        if not all([self.tenant_id, self.client_id, self.client_secret, self.site_url]):
            logger.warning("SharePoint configuration incomplete")
            self.enabled = False
        else:
            self.enabled = True
            self.access_token = None
            logger.info("SharePoint client initialized")
    
    async def _get_access_token(self) -> str:
        """
        Get access token for Microsoft Graph API
        """
        if self.access_token:
            return self.access_token
        
        try:
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data["access_token"]
                        return self.access_token
                    else:
                        logger.error(f"Failed to get SharePoint access token: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"SharePoint authentication error: {str(e)}")
            return None
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search SharePoint for relevant content
        """
        if not self.enabled:
            logger.warning("SharePoint client not enabled")
            return []
        
        try:
            access_token = await self._get_access_token()
            if not access_token:
                return []
            
            # Use Microsoft Graph search API
            search_url = "https://graph.microsoft.com/v1.0/search/query"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Search request body
            search_body = {
                "requests": [
                    {
                        "entityTypes": ["driveItem"],
                        "query": {
                            "queryString": query
                        },
                        "from": 0,
                        "size": 10
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(search_url, headers=headers, json=search_body) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_search_results(data)
                    else:
                        logger.error(f"SharePoint search failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"SharePoint search error: {str(e)}")
            return []
    
    def _parse_search_results(self, data: Dict) -> List[Dict[str, Any]]:
        """
        Parse SharePoint search results
        """
        results = []
        
        for response in data.get("value", []):
            hits = response.get("hitsContainers", [])
            
            for hit_container in hits:
                for hit in hit_container.get("hits", []):
                    resource = hit.get("resource", {})
                    
                    # Extract file information
                    name = resource.get("name", "Untitled")
                    web_url = resource.get("webUrl", "")
                    last_modified = resource.get("lastModifiedDateTime", "Unknown")
                    
                    # Get content preview if available
                    content = ""
                    if "summary" in hit:
                        content = hit["summary"]
                    
                    result = {
                        "title": name,
                        "url": web_url,
                        "content": content,
                        "source": "SharePoint",
                        "last_modified": last_modified,
                        "file_type": resource.get("fileSystemInfo", {}).get("fileExtension", "")
                    }
                    
                    results.append(result)
        
        return results

