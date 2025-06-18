"""
SharePoint Online Client
Handles search and content retrieval from SharePoint Online via Microsoft Graph API
for NAVO knowledge discovery
"""

import os
import logging
from typing import List, Dict, Any
import aiohttp
import json

logger = logging.getLogger(__name__)


class SharePointClient:
    """
    Client for SharePoint Online via Microsoft Graph API
    Provides search and content retrieval capabilities
    """
    
    def __init__(self):
        self.tenant_id = os.getenv("SHAREPOINT_TENANT_ID")
        self.client_id = os.getenv("SHAREPOINT_CLIENT_ID")
        self.client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET")
        self.site_url = os.getenv("SHAREPOINT_SITE_URL")
        
        # Validate configuration
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            logger.warning("SharePoint configuration incomplete - missing required environment variables")
            self.enabled = False
        else:
            self.enabled = True
            self.access_token = None
            self.token_expires_at = 0
            logger.info("SharePoint client initialized successfully")
    
    async def _get_access_token(self) -> str:
        """
        Get access token for Microsoft Graph API using client credentials flow
        
        Returns:
            Access token string or None if authentication fails
        """
        import time
        
        # Check if current token is still valid
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            logger.info("Requesting new SharePoint access token")
            
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    token_url, 
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data["access_token"]
                        
                        # Set token expiration (subtract 5 minutes for safety)
                        expires_in = token_data.get("expires_in", 3600)
                        self.token_expires_at = time.time() + expires_in - 300
                        
                        logger.info("SharePoint access token obtained successfully")
                        return self.access_token
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get SharePoint access token: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"SharePoint authentication error: {str(e)}")
            return None
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search SharePoint for relevant content using Microsoft Graph Search API
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of search results with title, content, URL, and metadata
        """
        if not self.enabled:
            logger.warning("SharePoint client not enabled - skipping search")
            return []
        
        try:
            logger.info(f"Searching SharePoint for: {query}")
            
            access_token = await self._get_access_token()
            if not access_token:
                logger.error("Could not obtain SharePoint access token")
                return []
            
            # Use Microsoft Graph search API
            search_url = "https://graph.microsoft.com/v1.0/search/query"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Build search request for SharePoint content
            search_body = {
                "requests": [
                    {
                        "entityTypes": ["driveItem", "listItem"],
                        "query": {
                            "queryString": query
                        },
                        "from": 0,
                        "size": min(limit, 25),  # Graph API limit
                        "fields": [
                            "name",
                            "webUrl", 
                            "lastModifiedDateTime",
                            "createdBy",
                            "fileSystemInfo",
                            "parentReference"
                        ]
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    search_url, 
                    headers=headers, 
                    json=search_body,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        results = self._parse_search_results(data)
                        logger.info(f"Found {len(results)} SharePoint results")
                        return results
                    elif response.status == 401:
                        logger.error("SharePoint authentication failed - token may be invalid")
                        self.access_token = None  # Force token refresh
                        return []
                    elif response.status == 403:
                        logger.error("SharePoint access forbidden - check app permissions")
                        return []
                    else:
                        error_text = await response.text()
                        logger.error(f"SharePoint search failed: {response.status} - {error_text}")
                        return []
                        
        except aiohttp.ClientError as e:
            logger.error(f"SharePoint network error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"SharePoint search error: {str(e)}")
            return []
    
    def _parse_search_results(self, data: Dict) -> List[Dict[str, Any]]:
        """
        Parse Microsoft Graph search API response
        
        Args:
            data: Raw API response data
            
        Returns:
            List of formatted search results
        """
        results = []
        
        try:
            for response in data.get("value", []):
                hits_containers = response.get("hitsContainers", [])
                
                for hits_container in hits_containers:
                    for hit in hits_container.get("hits", []):
                        try:
                            resource = hit.get("resource", {})
                            
                            # Extract basic information
                            name = resource.get("name", "Untitled Document")
                            web_url = resource.get("webUrl", "")
                            last_modified = resource.get("lastModifiedDateTime", "Unknown")
                            
                            # Get file type information
                            file_info = resource.get("fileSystemInfo", {})
                            file_extension = file_info.get("fileExtension", "")
                            
                            # Get parent/location information
                            parent_ref = resource.get("parentReference", {})
                            site_name = parent_ref.get("siteId", "SharePoint")
                            
                            # Extract content summary if available
                            content = ""
                            if "summary" in hit:
                                content = hit["summary"]
                            elif "snippet" in hit:
                                content = hit["snippet"]
                            
                            # Get author information
                            author = "Unknown"
                            created_by = resource.get("createdBy", {})
                            if created_by and "user" in created_by:
                                author = created_by["user"].get("displayName", "Unknown")
                            
                            # Determine document type
                            doc_type = self._get_document_type(name, file_extension)
                            
                            result = {
                                "title": name,
                                "url": web_url,
                                "content": content or f"SharePoint document: {name}",
                                "source": "SharePoint",
                                "last_modified": last_modified,
                                "file_type": file_extension,
                                "document_type": doc_type,
                                "author": author,
                                "site": site_name
                            }
                            
                            results.append(result)
                            
                        except Exception as e:
                            logger.warning(f"Error parsing SharePoint search result: {str(e)}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error parsing SharePoint search response: {str(e)}")
        
        return results
    
    def _get_document_type(self, filename: str, extension: str) -> str:
        """
        Determine document type based on filename and extension
        
        Args:
            filename: Document filename
            extension: File extension
            
        Returns:
            Human-readable document type
        """
        extension = extension.lower().lstrip('.')
        
        type_mapping = {
            'docx': 'Word Document',
            'doc': 'Word Document', 
            'xlsx': 'Excel Spreadsheet',
            'xls': 'Excel Spreadsheet',
            'pptx': 'PowerPoint Presentation',
            'ppt': 'PowerPoint Presentation',
            'pdf': 'PDF Document',
            'txt': 'Text File',
            'md': 'Markdown Document',
            'html': 'Web Page',
            'htm': 'Web Page'
        }
        
        return type_mapping.get(extension, 'Document')

