"""
NAVO SharePoint Integration Client
Enhanced SharePoint integration with Microsoft Graph API and OpenAI Enterprise optimization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import aiohttp
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SharePointDocument:
    """Represents a SharePoint document."""
    id: str
    name: str
    content: str
    site_name: str
    site_url: str
    web_url: str
    last_modified: datetime
    created: datetime
    author: str
    file_type: str
    size: int
    path: str
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class SharePointClient:
    """
    Enhanced SharePoint client for NAVO using Microsoft Graph API
    with intelligent document processing and OpenAI Enterprise integration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SharePoint client.
        
        Args:
            config: SharePoint configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Authentication settings
        self.tenant_id = config.get("tenant_id")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.scope = config.get("scope", "https://graph.microsoft.com/.default")
        
        # SharePoint settings
        self.site_urls = config.get("site_urls", [])
        self.sites_to_exclude = config.get("sites_to_exclude", [])
        self.file_types = config.get("file_types", [".docx", ".pdf", ".txt", ".md"])
        self.max_file_size_mb = config.get("max_file_size_mb", 50)
        self.max_results_per_request = config.get("max_results_per_request", 50)
        
        # Processing settings
        self.extract_metadata = config.get("extract_metadata", True)
        self.respect_permissions = config.get("respect_permissions", True)
        
        # Graph API endpoints
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
        self.auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        # Session and token management
        self.session = None
        self.access_token = None
        self.token_expires_at = None
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("SharePoint tenant_id, client_id, and client_secret are required")
        
        self.logger.info("SharePoint client initialized")
    
    async def _get_access_token(self) -> str:
        """
        Get or refresh access token for Microsoft Graph API.
        
        Returns:
            Valid access token
        """
        # Check if current token is still valid
        if (self.access_token and self.token_expires_at and 
            datetime.utcnow() < self.token_expires_at - timedelta(minutes=5)):
            return self.access_token
        
        # Get new token
        session = await self._get_session()
        
        token_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope
        }
        
        async with session.post(self.auth_url, data=token_data) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get access token: {error_text}")
            
            token_response = await response.json()
            
            self.access_token = token_response["access_token"]
            expires_in = token_response.get("expires_in", 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            self.logger.debug("Access token refreshed")
            return self.access_token
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "NAVO/2.0.0"
            }
            
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        
        return self.session
    
    async def _get_authenticated_session(self) -> aiohttp.ClientSession:
        """Get session with authentication headers."""
        session = await self._get_session()
        token = await self._get_access_token()
        
        # Update authorization header
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        return session
    
    async def search(
        self, 
        processed_query, 
        user_permissions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search SharePoint for relevant documents.
        
        Args:
            processed_query: ProcessedQuery object with search criteria
            user_permissions: User's SharePoint permissions
            
        Returns:
            List of relevant documents
        """
        self.logger.info(f"Searching SharePoint for: {processed_query.original_text[:100]}...")
        
        try:
            # Build search query
            search_query = self._build_search_query(processed_query, user_permissions)
            
            # Execute search across configured sites
            all_results = []
            
            for site_url in self.site_urls:
                if self._should_skip_site(site_url, user_permissions):
                    continue
                
                try:
                    site_results = await self._search_site(site_url, search_query)
                    all_results.extend(site_results)
                except Exception as e:
                    self.logger.warning(f"Error searching site {site_url}: {str(e)}")
                    continue
            
            # Process and rank results
            processed_results = await self._process_search_results(
                all_results, processed_query
            )
            
            self.logger.info(f"Found {len(processed_results)} SharePoint documents")
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Error searching SharePoint: {str(e)}")
            return []
    
    async def get_document(self, site_url: str, item_id: str) -> Optional[SharePointDocument]:
        """
        Get a specific SharePoint document.
        
        Args:
            site_url: SharePoint site URL
            item_id: Document item ID
            
        Returns:
            SharePointDocument if found, None otherwise
        """
        try:
            session = await self._get_authenticated_session()
            
            # Get site ID first
            site_id = await self._get_site_id(site_url)
            if not site_id:
                return None
            
            # Get document metadata
            url = f"{self.graph_base_url}/sites/{site_id}/drive/items/{item_id}"
            params = {"expand": "listItem"}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Get document content if it's a text file
                    content = await self._get_document_content(site_id, item_id)
                    
                    return self._parse_sharepoint_document(data, site_url, content)
                elif response.status == 404:
                    self.logger.warning(f"SharePoint document not found: {item_id}")
                    return None
                else:
                    error_text = await response.text()
                    self.logger.error(f"Error getting SharePoint document: {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting SharePoint document {item_id}: {str(e)}")
            return None
    
    async def sync_sites(self, sites: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sync documents from specified SharePoint sites.
        
        Args:
            sites: List of site URLs to sync (None for all configured sites)
            
        Returns:
            Sync results summary
        """
        if sites is None:
            sites = self.site_urls
        
        if not sites:
            self.logger.warning("No sites configured for sync")
            return {"status": "skipped", "reason": "no_sites_configured"}
        
        self.logger.info(f"Starting sync for {len(sites)} SharePoint sites")
        
        sync_results = {
            "status": "completed",
            "sites_synced": 0,
            "documents_processed": 0,
            "documents_updated": 0,
            "errors": []
        }
        
        for site_url in sites:
            if site_url in self.sites_to_exclude:
                self.logger.info(f"Skipping excluded site: {site_url}")
                continue
            
            try:
                site_results = await self._sync_site(site_url)
                sync_results["sites_synced"] += 1
                sync_results["documents_processed"] += site_results["documents_processed"]
                sync_results["documents_updated"] += site_results["documents_updated"]
                
            except Exception as e:
                error_msg = f"Error syncing site {site_url}: {str(e)}"
                self.logger.error(error_msg)
                sync_results["errors"].append(error_msg)
        
        self.logger.info(f"SharePoint sync completed: {sync_results}")
        return sync_results
    
    def _build_search_query(
        self, 
        processed_query, 
        user_permissions: Dict[str, Any]
    ) -> str:
        """
        Build SharePoint search query from processed query.
        
        Args:
            processed_query: ProcessedQuery object
            user_permissions: User's permissions
            
        Returns:
            SharePoint search query string
        """
        # Build search terms
        search_terms = []
        
        # Add keywords
        if processed_query.keywords:
            # Use quotes for exact phrase matching
            main_keywords = processed_query.keywords[:5]
            for keyword in main_keywords:
                search_terms.append(f'"{keyword}"')
        
        # Add entity-based search terms
        for entity in processed_query.entities:
            if entity.type in ["systems", "technologies", "code"]:
                search_terms.append(f'"{entity.text}"')
        
        # Combine search terms
        if search_terms:
            return " AND ".join(search_terms)
        else:
            # Fallback to original text
            return processed_query.original_text
    
    def _should_skip_site(self, site_url: str, user_permissions: Dict[str, Any]) -> bool:
        """
        Check if a site should be skipped based on permissions.
        
        Args:
            site_url: Site URL to check
            user_permissions: User's permissions
            
        Returns:
            True if site should be skipped
        """
        if not self.respect_permissions:
            return False
        
        # Extract site name from URL
        site_name = self._extract_site_name(site_url)
        
        # Check if user has access
        accessible_sites = user_permissions.get("sites", [])
        
        if "*" in accessible_sites:
            return False  # User has access to all sites
        
        return site_name not in accessible_sites
    
    async def _search_site(self, site_url: str, search_query: str) -> List[Dict[str, Any]]:
        """
        Search a specific SharePoint site.
        
        Args:
            site_url: SharePoint site URL
            search_query: Search query string
            
        Returns:
            List of search results from the site
        """
        session = await self._get_authenticated_session()
        
        # Get site ID
        site_id = await self._get_site_id(site_url)
        if not site_id:
            return []
        
        # Search using Microsoft Graph search API
        search_url = f"{self.graph_base_url}/search/query"
        
        search_request = {
            "requests": [
                {
                    "entityTypes": ["driveItem"],
                    "query": {
                        "queryString": search_query
                    },
                    "from": 0,
                    "size": self.max_results_per_request,
                    "fields": [
                        "id", "name", "webUrl", "lastModifiedDateTime", 
                        "createdDateTime", "size", "file", "folder"
                    ]
                }
            ]
        }
        
        results = []
        
        async with session.post(search_url, json=search_request) as response:
            if response.status == 200:
                data = await response.json()
                
                for search_response in data.get("value", []):
                    hits = search_response.get("hitsContainers", [])
                    for hit_container in hits:
                        for hit in hit_container.get("hits", []):
                            resource = hit.get("resource", {})
                            
                            # Filter by site and file type
                            if (site_id in resource.get("webUrl", "") and
                                self._is_supported_file_type(resource.get("name", ""))):
                                results.append(resource)
            else:
                error_text = await response.text()
                self.logger.warning(f"Search failed for site {site_url}: {error_text}")
        
        return results
    
    async def _get_site_id(self, site_url: str) -> Optional[str]:
        """
        Get SharePoint site ID from URL.
        
        Args:
            site_url: SharePoint site URL
            
        Returns:
            Site ID if found
        """
        try:
            session = await self._get_authenticated_session()
            
            # Extract hostname and site path
            from urllib.parse import urlparse
            parsed = urlparse(site_url)
            hostname = parsed.hostname
            site_path = parsed.path.strip("/")
            
            # Get site by hostname and path
            url = f"{self.graph_base_url}/sites/{hostname}:/{site_path}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("id")
                else:
                    self.logger.warning(f"Could not get site ID for {site_url}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting site ID for {site_url}: {str(e)}")
            return None
    
    async def _get_document_content(self, site_id: str, item_id: str) -> str:
        """
        Get document content for text files.
        
        Args:
            site_id: SharePoint site ID
            item_id: Document item ID
            
        Returns:
            Document content as string
        """
        try:
            session = await self._get_authenticated_session()
            
            # Get document content
            url = f"{self.graph_base_url}/sites/{site_id}/drive/items/{item_id}/content"
            
            async with session.get(url) as response:
                if response.status == 200:
                    content_type = response.headers.get("content-type", "")
                    
                    if "text/" in content_type:
                        return await response.text()
                    else:
                        # For binary files, return empty content
                        # In a real implementation, you might use OCR or document parsing
                        return ""
                else:
                    return ""
                    
        except Exception as e:
            self.logger.warning(f"Error getting document content: {str(e)}")
            return ""
    
    def _parse_sharepoint_document(
        self, 
        data: Dict[str, Any], 
        site_url: str, 
        content: str
    ) -> SharePointDocument:
        """
        Parse SharePoint API response into SharePointDocument.
        
        Args:
            data: Raw SharePoint API response
            site_url: SharePoint site URL
            content: Document content
            
        Returns:
            SharePointDocument object
        """
        # Extract file information
        file_info = data.get("file", {})
        
        # Extract dates
        last_modified = datetime.fromisoformat(
            data.get("lastModifiedDateTime", datetime.utcnow().isoformat()).replace("Z", "+00:00")
        )
        created = datetime.fromisoformat(
            data.get("createdDateTime", datetime.utcnow().isoformat()).replace("Z", "+00:00")
        )
        
        # Extract author information
        created_by = data.get("createdBy", {}).get("user", {})
        author = created_by.get("displayName", "Unknown")
        
        return SharePointDocument(
            id=data.get("id", ""),
            name=data.get("name", ""),
            content=content,
            site_name=self._extract_site_name(site_url),
            site_url=site_url,
            web_url=data.get("webUrl", ""),
            last_modified=last_modified,
            created=created,
            author=author,
            file_type=file_info.get("mimeType", ""),
            size=data.get("size", 0),
            path=data.get("parentReference", {}).get("path", "")
        )
    
    async def _process_search_results(
        self, 
        search_results: List[Dict[str, Any]], 
        processed_query
    ) -> List[Dict[str, Any]]:
        """
        Process and rank search results.
        
        Args:
            search_results: Raw search results from SharePoint
            processed_query: ProcessedQuery object
            
        Returns:
            Processed and ranked results
        """
        processed_results = []
        
        for result in search_results:
            try:
                # Get document content if needed
                content = ""
                if self._is_text_file(result.get("name", "")):
                    # In a real implementation, you would fetch the content
                    # For now, we'll use the name as a summary
                    content = result.get("name", "")
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(result, processed_query)
                
                # Convert to standard format
                processed_doc = {
                    "id": result.get("id", ""),
                    "title": result.get("name", ""),
                    "content": content,
                    "summary": content[:300] + "..." if len(content) > 300 else content,
                    "source": "sharepoint",
                    "url": result.get("webUrl", ""),
                    "last_modified": result.get("lastModifiedDateTime", ""),
                    "author": result.get("createdBy", {}).get("user", {}).get("displayName", "Unknown"),
                    "file_type": result.get("file", {}).get("mimeType", ""),
                    "size": result.get("size", 0),
                    "relevance_score": relevance_score
                }
                
                processed_results.append(processed_doc)
                
            except Exception as e:
                self.logger.warning(f"Error processing search result: {str(e)}")
                continue
        
        # Sort by relevance score
        processed_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return processed_results
    
    def _calculate_relevance_score(self, doc: Dict[str, Any], processed_query) -> float:
        """
        Calculate relevance score for a document.
        
        Args:
            doc: SharePoint document data
            processed_query: ProcessedQuery object
            
        Returns:
            Relevance score between 0 and 1
        """
        score = 0.0
        
        # File name matching (high weight)
        name_lower = doc.get("name", "").lower()
        for keyword in processed_query.keywords:
            if keyword.lower() in name_lower:
                score += 0.4
        
        # Entity matching
        for entity in processed_query.entities:
            entity_text = entity.text.lower()
            if entity_text in name_lower:
                score += 0.3 * entity.confidence
        
        # File type preference (prefer text documents)
        file_type = doc.get("file", {}).get("mimeType", "")
        if "text/" in file_type or "document" in file_type:
            score += 0.1
        
        # Recency bonus
        last_modified = doc.get("lastModifiedDateTime", "")
        if last_modified:
            try:
                mod_date = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
                days_old = (datetime.utcnow().replace(tzinfo=mod_date.tzinfo) - mod_date).days
                if days_old < 30:
                    score += 0.2
                elif days_old < 90:
                    score += 0.1
            except:
                pass
        
        return min(score, 1.0)
    
    def _is_supported_file_type(self, filename: str) -> bool:
        """Check if file type is supported for indexing."""
        if not filename:
            return False
        
        file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        return file_ext in self.file_types
    
    def _is_text_file(self, filename: str) -> bool:
        """Check if file is a text file."""
        if not filename:
            return False
        
        text_extensions = [".txt", ".md", ".csv", ".json", ".xml"]
        file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        return file_ext in text_extensions
    
    def _extract_site_name(self, site_url: str) -> str:
        """Extract site name from SharePoint URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(site_url)
            path_parts = parsed.path.strip("/").split("/")
            
            # Typically the site name is after /sites/
            if "sites" in path_parts:
                site_index = path_parts.index("sites")
                if site_index + 1 < len(path_parts):
                    return path_parts[site_index + 1]
            
            return "Unknown"
        except:
            return "Unknown"
    
    async def _sync_site(self, site_url: str) -> Dict[str, Any]:
        """
        Sync all documents from a specific site.
        
        Args:
            site_url: SharePoint site URL
            
        Returns:
            Sync results for the site
        """
        self.logger.info(f"Syncing SharePoint site: {site_url}")
        
        results = {
            "documents_processed": 0,
            "documents_updated": 0
        }
        
        try:
            session = await self._get_authenticated_session()
            
            # Get site ID
            site_id = await self._get_site_id(site_url)
            if not site_id:
                return results
            
            # Get all files from the site
            url = f"{self.graph_base_url}/sites/{site_id}/drive/root/children"
            
            await self._sync_folder_recursive(session, url, results)
            
        except Exception as e:
            self.logger.error(f"Error syncing site {site_url}: {str(e)}")
        
        return results
    
    async def _sync_folder_recursive(
        self, 
        session: aiohttp.ClientSession, 
        folder_url: str, 
        results: Dict[str, Any]
    ):
        """
        Recursively sync all files in a folder.
        
        Args:
            session: Authenticated HTTP session
            folder_url: Graph API URL for the folder
            results: Results dictionary to update
        """
        try:
            async with session.get(folder_url) as response:
                if response.status != 200:
                    return
                
                data = await response.json()
                items = data.get("value", [])
                
                for item in items:
                    if item.get("folder"):
                        # Recursively process subfolders
                        children_url = item.get("@microsoft.graph.downloadUrl")
                        if children_url:
                            await self._sync_folder_recursive(session, children_url, results)
                    elif item.get("file"):
                        # Process file
                        if self._is_supported_file_type(item.get("name", "")):
                            results["documents_processed"] += 1
                            results["documents_updated"] += 1
                            
        except Exception as e:
            self.logger.warning(f"Error syncing folder: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on SharePoint connection.
        
        Returns:
            Health check results
        """
        try:
            # Test authentication
            token = await self._get_access_token()
            
            session = await self._get_authenticated_session()
            
            # Test basic Graph API connectivity
            url = f"{self.graph_base_url}/me"
            
            async with session.get(url) as response:
                if response.status == 200:
                    return {
                        "status": "healthy",
                        "graph_api_accessible": True,
                        "configured_sites": len(self.site_urls),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}: {error_text}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close the client session."""
        if self.session and not self.session.closed:
            await self.session.close()

