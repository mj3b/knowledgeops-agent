"""
NAVO Confluence Integration Client
Enhanced Confluence integration with OpenAI Enterprise optimization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import aiohttp
import base64
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConfluenceDocument:
    """Represents a Confluence document."""
    id: str
    title: str
    content: str
    space_key: str
    space_name: str
    url: str
    last_modified: datetime
    author: str
    version: int
    labels: List[str] = None
    attachments: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.attachments is None:
            self.attachments = []


class ConfluenceClient:
    """
    Enhanced Confluence client for NAVO with intelligent document processing
    and OpenAI Enterprise integration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Confluence client.
        
        Args:
            config: Confluence configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Connection settings
        self.base_url = config.get("base_url", "").rstrip("/")
        self.username = config.get("username")
        self.api_token = config.get("api_token")
        self.cloud_id = config.get("cloud_id")
        
        # Sync settings
        self.spaces_to_sync = config.get("spaces_to_sync", [])
        self.spaces_to_exclude = config.get("spaces_to_exclude", [])
        self.content_types = config.get("content_types", ["page", "blogpost"])
        self.max_results_per_request = config.get("max_results_per_request", 50)
        self.sync_attachments = config.get("sync_attachments", True)
        self.max_attachment_size_mb = config.get("max_attachment_size_mb", 10)
        
        # Processing settings
        self.extract_custom_fields = config.get("extract_custom_fields", True)
        self.respect_permissions = config.get("respect_permissions", True)
        
        # Session for connection pooling
        self.session = None
        
        if not all([self.base_url, self.username, self.api_token]):
            raise ValueError("Confluence base_url, username, and api_token are required")
        
        self.logger.info(f"Confluence client initialized for: {self.base_url}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with authentication."""
        if self.session is None or self.session.closed:
            # Create basic auth header
            auth_string = f"{self.username}:{self.api_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_header = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "NAVO/2.0.0"
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        
        return self.session
    
    async def search(
        self, 
        processed_query, 
        user_permissions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search Confluence for relevant documents.
        
        Args:
            processed_query: ProcessedQuery object with search criteria
            user_permissions: User's Confluence permissions
            
        Returns:
            List of relevant documents
        """
        self.logger.info(f"Searching Confluence for: {processed_query.original_text[:100]}...")
        
        try:
            # Build search query
            search_query = self._build_search_query(processed_query, user_permissions)
            
            # Execute search
            search_results = await self._execute_search(search_query)
            
            # Process and rank results
            processed_results = await self._process_search_results(
                search_results, processed_query
            )
            
            self.logger.info(f"Found {len(processed_results)} Confluence documents")
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Error searching Confluence: {str(e)}")
            return []
    
    async def get_document(self, document_id: str) -> Optional[ConfluenceDocument]:
        """
        Get a specific Confluence document by ID.
        
        Args:
            document_id: Confluence page or blog post ID
            
        Returns:
            ConfluenceDocument if found, None otherwise
        """
        try:
            session = await self._get_session()
            
            # Get page content with expanded fields
            url = f"{self.base_url}/rest/api/content/{document_id}"
            params = {
                "expand": "body.storage,space,history,metadata.labels,version"
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_confluence_document(data)
                elif response.status == 404:
                    self.logger.warning(f"Confluence document not found: {document_id}")
                    return None
                else:
                    error_text = await response.text()
                    self.logger.error(f"Error getting Confluence document: {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting Confluence document {document_id}: {str(e)}")
            return None
    
    async def sync_spaces(self, spaces: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sync documents from specified Confluence spaces.
        
        Args:
            spaces: List of space keys to sync (None for all configured spaces)
            
        Returns:
            Sync results summary
        """
        if spaces is None:
            spaces = self.spaces_to_sync
        
        if not spaces:
            self.logger.warning("No spaces configured for sync")
            return {"status": "skipped", "reason": "no_spaces_configured"}
        
        self.logger.info(f"Starting sync for spaces: {spaces}")
        
        sync_results = {
            "status": "completed",
            "spaces_synced": 0,
            "documents_processed": 0,
            "documents_updated": 0,
            "errors": []
        }
        
        for space_key in spaces:
            if space_key in self.spaces_to_exclude:
                self.logger.info(f"Skipping excluded space: {space_key}")
                continue
            
            try:
                space_results = await self._sync_space(space_key)
                sync_results["spaces_synced"] += 1
                sync_results["documents_processed"] += space_results["documents_processed"]
                sync_results["documents_updated"] += space_results["documents_updated"]
                
            except Exception as e:
                error_msg = f"Error syncing space {space_key}: {str(e)}"
                self.logger.error(error_msg)
                sync_results["errors"].append(error_msg)
        
        self.logger.info(f"Sync completed: {sync_results}")
        return sync_results
    
    async def _build_search_query(
        self, 
        processed_query, 
        user_permissions: Dict[str, Any]
    ) -> str:
        """
        Build Confluence search query from processed query.
        
        Args:
            processed_query: ProcessedQuery object
            user_permissions: User's permissions
            
        Returns:
            Confluence search query string
        """
        # Start with keywords
        query_parts = []
        
        # Add main keywords
        if processed_query.keywords:
            # Use the most important keywords
            main_keywords = processed_query.keywords[:5]
            keyword_query = " AND ".join(f'"{keyword}"' for keyword in main_keywords)
            query_parts.append(f"({keyword_query})")
        
        # Add entity-based search terms
        for entity in processed_query.entities:
            if entity.type in ["systems", "technologies", "code"]:
                query_parts.append(f'"{entity.text}"')
        
        # Restrict to accessible spaces if permissions are enforced
        if self.respect_permissions and user_permissions.get("spaces"):
            accessible_spaces = user_permissions["spaces"]
            if "*" not in accessible_spaces:
                space_query = " OR ".join(f"space={space}" for space in accessible_spaces)
                query_parts.append(f"({space_query})")
        
        # Combine query parts
        if query_parts:
            return " AND ".join(query_parts)
        else:
            # Fallback to simple text search
            return processed_query.original_text
    
    async def _execute_search(self, search_query: str) -> List[Dict[str, Any]]:
        """
        Execute search against Confluence API.
        
        Args:
            search_query: Search query string
            
        Returns:
            List of search results
        """
        session = await self._get_session()
        
        url = f"{self.base_url}/rest/api/content/search"
        params = {
            "cql": search_query,
            "limit": self.max_results_per_request,
            "expand": "body.storage,space,history,metadata.labels"
        }
        
        all_results = []
        start = 0
        
        while True:
            params["start"] = start
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Confluence search failed: {error_text}")
                
                data = await response.json()
                results = data.get("results", [])
                
                if not results:
                    break
                
                all_results.extend(results)
                
                # Check if there are more results
                if len(results) < self.max_results_per_request:
                    break
                
                start += len(results)
                
                # Limit total results to prevent excessive API calls
                if len(all_results) >= 200:
                    break
        
        return all_results
    
    async def _process_search_results(
        self, 
        search_results: List[Dict[str, Any]], 
        processed_query
    ) -> List[Dict[str, Any]]:
        """
        Process and rank search results.
        
        Args:
            search_results: Raw search results from Confluence
            processed_query: ProcessedQuery object
            
        Returns:
            Processed and ranked results
        """
        processed_results = []
        
        for result in search_results:
            try:
                # Parse the result
                doc = self._parse_confluence_document(result)
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(doc, processed_query)
                
                # Convert to standard format
                processed_doc = {
                    "id": doc.id,
                    "title": doc.title,
                    "content": doc.content[:1000] + "..." if len(doc.content) > 1000 else doc.content,
                    "summary": doc.content[:300] + "..." if len(doc.content) > 300 else doc.content,
                    "source": "confluence",
                    "url": doc.url,
                    "last_modified": doc.last_modified.isoformat(),
                    "author": doc.author,
                    "space": doc.space_name,
                    "relevance_score": relevance_score,
                    "labels": doc.labels
                }
                
                processed_results.append(processed_doc)
                
            except Exception as e:
                self.logger.warning(f"Error processing search result: {str(e)}")
                continue
        
        # Sort by relevance score
        processed_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return processed_results
    
    def _parse_confluence_document(self, data: Dict[str, Any]) -> ConfluenceDocument:
        """
        Parse Confluence API response into ConfluenceDocument.
        
        Args:
            data: Raw Confluence API response
            
        Returns:
            ConfluenceDocument object
        """
        # Extract content
        content = ""
        if "body" in data and "storage" in data["body"]:
            content = data["body"]["storage"].get("value", "")
            # Remove HTML tags for cleaner content
            import re
            content = re.sub(r'<[^>]+>', '', content)
        
        # Extract space information
        space = data.get("space", {})
        space_key = space.get("key", "")
        space_name = space.get("name", "")
        
        # Extract history/version info
        history = data.get("history", {})
        version_info = data.get("version", {})
        
        # Extract labels
        labels = []
        if "metadata" in data and "labels" in data["metadata"]:
            labels = [label.get("name", "") for label in data["metadata"]["labels"].get("results", [])]
        
        # Build URL
        url = f"{self.base_url}/spaces/{space_key}/pages/{data['id']}"
        if "webui" in data.get("_links", {}):
            url = self.base_url + data["_links"]["webui"]
        
        return ConfluenceDocument(
            id=data["id"],
            title=data.get("title", ""),
            content=content,
            space_key=space_key,
            space_name=space_name,
            url=url,
            last_modified=datetime.fromisoformat(
                history.get("lastUpdated", {}).get("when", datetime.utcnow().isoformat()).replace("Z", "+00:00")
            ),
            author=history.get("lastUpdated", {}).get("by", {}).get("displayName", "Unknown"),
            version=version_info.get("number", 1),
            labels=labels
        )
    
    def _calculate_relevance_score(self, doc: ConfluenceDocument, processed_query) -> float:
        """
        Calculate relevance score for a document.
        
        Args:
            doc: ConfluenceDocument to score
            processed_query: ProcessedQuery object
            
        Returns:
            Relevance score between 0 and 1
        """
        score = 0.0
        
        # Title matching (high weight)
        title_lower = doc.title.lower()
        for keyword in processed_query.keywords:
            if keyword.lower() in title_lower:
                score += 0.3
        
        # Content matching (medium weight)
        content_lower = doc.content.lower()
        keyword_matches = sum(1 for keyword in processed_query.keywords 
                            if keyword.lower() in content_lower)
        score += 0.2 * (keyword_matches / max(len(processed_query.keywords), 1))
        
        # Entity matching (high weight)
        for entity in processed_query.entities:
            entity_text = entity.text.lower()
            if entity_text in title_lower:
                score += 0.4 * entity.confidence
            elif entity_text in content_lower:
                score += 0.2 * entity.confidence
        
        # Label matching
        for label in doc.labels:
            if any(keyword.lower() in label.lower() for keyword in processed_query.keywords):
                score += 0.1
        
        # Recency bonus (newer documents get slight boost)
        days_old = (datetime.utcnow() - doc.last_modified.replace(tzinfo=None)).days
        if days_old < 30:
            score += 0.1
        elif days_old < 90:
            score += 0.05
        
        return min(score, 1.0)
    
    async def _sync_space(self, space_key: str) -> Dict[str, Any]:
        """
        Sync all documents from a specific space.
        
        Args:
            space_key: Confluence space key
            
        Returns:
            Sync results for the space
        """
        self.logger.info(f"Syncing Confluence space: {space_key}")
        
        results = {
            "documents_processed": 0,
            "documents_updated": 0
        }
        
        session = await self._get_session()
        
        # Get all content from the space
        url = f"{self.base_url}/rest/api/content"
        params = {
            "spaceKey": space_key,
            "limit": self.max_results_per_request,
            "expand": "body.storage,space,history,metadata.labels,version"
        }
        
        start = 0
        while True:
            params["start"] = start
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get space content: {error_text}")
                
                data = await response.json()
                content_items = data.get("results", [])
                
                if not content_items:
                    break
                
                for item in content_items:
                    try:
                        # Process each document
                        doc = self._parse_confluence_document(item)
                        
                        # Here you would typically save to your document store
                        # For now, we'll just count it
                        results["documents_processed"] += 1
                        results["documents_updated"] += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing document {item.get('id')}: {str(e)}")
                
                if len(content_items) < self.max_results_per_request:
                    break
                
                start += len(content_items)
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Confluence connection.
        
        Returns:
            Health check results
        """
        try:
            session = await self._get_session()
            
            # Test basic connectivity
            url = f"{self.base_url}/rest/api/space"
            params = {"limit": 1}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "healthy",
                        "confluence_url": self.base_url,
                        "accessible_spaces": len(data.get("results", [])),
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

