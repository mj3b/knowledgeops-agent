"""
NAVO Core Engine
The heart of NAVO's knowledge discovery capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from ..integrations.openai.enterprise_client import OpenAIEnterpriseClient
from ..integrations.confluence.client import ConfluenceClient
from ..integrations.sharepoint.client import SharePointClient
from .query_processor import QueryProcessor
from .response_generator import ResponseGenerator
from .cache_manager import CacheManager
from .permission_manager import PermissionManager

logger = logging.getLogger(__name__)


@dataclass
class NAVOQuery:
    """Represents a user query to NAVO."""
    text: str
    user_id: str
    context: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class NAVOResponse:
    """Represents NAVO's response to a query."""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    processing_time: float
    query_id: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class NAVOEngine:
    """
    NAVO Core Engine - The central orchestrator for knowledge discovery.
    
    Integrates OpenAI Enterprise with organizational knowledge sources
    to provide intelligent, context-aware responses.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize NAVO Engine with configuration.
        
        Args:
            config: Configuration dictionary containing API keys, settings, etc.
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize core components
        self.openai_client = OpenAIEnterpriseClient(config.get("openai", {}))
        self.query_processor = QueryProcessor(config.get("query_processing", {}))
        self.response_generator = ResponseGenerator(
            openai_client=self.openai_client,
            config=config.get("response_generation", {})
        )
        self.cache_manager = CacheManager(config.get("cache", {}))
        self.permission_manager = PermissionManager(config.get("permissions", {}))
        
        # Initialize integration clients
        self.confluence_client = None
        self.sharepoint_client = None
        
        if config.get("integrations", {}).get("confluence", {}).get("enabled", False):
            self.confluence_client = ConfluenceClient(
                config["integrations"]["confluence"]
            )
            
        if config.get("integrations", {}).get("sharepoint", {}).get("enabled", False):
            self.sharepoint_client = SharePointClient(
                config["integrations"]["sharepoint"]
            )
        
        self.logger.info("NAVO Engine initialized successfully")
    
    async def process_query(self, query: NAVOQuery) -> NAVOResponse:
        """
        Process a user query and return an intelligent response.
        
        Args:
            query: The user query to process
            
        Returns:
            NAVOResponse containing the answer and supporting information
        """
        start_time = datetime.utcnow()
        query_id = f"navo_{int(start_time.timestamp() * 1000)}"
        
        self.logger.info(f"Processing query {query_id}: {query.text[:100]}...")
        
        try:
            # Check cache first
            cached_response = await self.cache_manager.get_cached_response(query)
            if cached_response:
                self.logger.info(f"Returning cached response for query {query_id}")
                return cached_response
            
            # Process the query to understand intent and extract entities
            processed_query = await self.query_processor.process(query)
            
            # Check user permissions for the query context
            user_permissions = await self.permission_manager.get_user_permissions(
                query.user_id, processed_query.context
            )
            
            # Search for relevant documents across integrated systems
            relevant_docs = await self._search_knowledge_sources(
                processed_query, user_permissions
            )
            
            # Generate response using OpenAI Enterprise
            response = await self.response_generator.generate_response(
                processed_query, relevant_docs
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create NAVO response
            navo_response = NAVOResponse(
                answer=response.answer,
                sources=response.sources,
                confidence=response.confidence,
                processing_time=processing_time,
                query_id=query_id
            )
            
            # Cache the response for future queries
            await self.cache_manager.cache_response(query, navo_response)
            
            self.logger.info(
                f"Query {query_id} processed successfully in {processing_time:.2f}s"
            )
            
            return navo_response
            
        except Exception as e:
            self.logger.error(f"Error processing query {query_id}: {str(e)}")
            
            # Return error response
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            return NAVOResponse(
                answer="I apologize, but I encountered an error while processing your query. Please try again or contact support if the issue persists.",
                sources=[],
                confidence=0.0,
                processing_time=processing_time,
                query_id=query_id
            )
    
    async def _search_knowledge_sources(
        self, 
        processed_query: Any, 
        user_permissions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search across all configured knowledge sources.
        
        Args:
            processed_query: The processed query with intent and entities
            user_permissions: User's access permissions
            
        Returns:
            List of relevant documents from all sources
        """
        search_tasks = []
        
        # Search Confluence if enabled and user has access
        if (self.confluence_client and 
            user_permissions.get("confluence", {}).get("enabled", False)):
            search_tasks.append(
                self.confluence_client.search(
                    processed_query, user_permissions["confluence"]
                )
            )
        
        # Search SharePoint if enabled and user has access
        if (self.sharepoint_client and 
            user_permissions.get("sharepoint", {}).get("enabled", False)):
            search_tasks.append(
                self.sharepoint_client.search(
                    processed_query, user_permissions["sharepoint"]
                )
            )
        
        # Execute all searches concurrently
        if search_tasks:
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results and filter out exceptions
            all_docs = []
            for result in search_results:
                if isinstance(result, Exception):
                    self.logger.warning(f"Search error: {str(result)}")
                    continue
                all_docs.extend(result)
            
            # Sort by relevance and return top results
            all_docs.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            return all_docs[:self.config.get("max_search_results", 10)]
        
        return []
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all NAVO components.
        
        Returns:
            Dictionary containing health status of all components
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check OpenAI Enterprise connection
        try:
            await self.openai_client.health_check()
            health_status["components"]["openai_enterprise"] = "healthy"
        except Exception as e:
            health_status["components"]["openai_enterprise"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check Confluence connection
        if self.confluence_client:
            try:
                await self.confluence_client.health_check()
                health_status["components"]["confluence"] = "healthy"
            except Exception as e:
                health_status["components"]["confluence"] = f"unhealthy: {str(e)}"
                health_status["status"] = "degraded"
        
        # Check SharePoint connection
        if self.sharepoint_client:
            try:
                await self.sharepoint_client.health_check()
                health_status["components"]["sharepoint"] = "healthy"
            except Exception as e:
                health_status["components"]["sharepoint"] = f"unhealthy: {str(e)}"
                health_status["status"] = "degraded"
        
        # Check cache
        try:
            await self.cache_manager.health_check()
            health_status["components"]["cache"] = "healthy"
        except Exception as e:
            health_status["components"]["cache"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        return health_status
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get NAVO performance and usage metrics.
        
        Returns:
            Dictionary containing various metrics
        """
        return {
            "queries_processed": await self.cache_manager.get_query_count(),
            "cache_hit_rate": await self.cache_manager.get_hit_rate(),
            "average_response_time": await self.cache_manager.get_avg_response_time(),
            "active_integrations": len([
                client for client in [self.confluence_client, self.sharepoint_client]
                if client is not None
            ]),
            "timestamp": datetime.utcnow().isoformat()
        }

