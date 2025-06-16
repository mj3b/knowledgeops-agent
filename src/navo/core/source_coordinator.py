"""
NAVO Phase 3: Multi-Source Orchestration
Source Coordinator - Unified cross-platform knowledge orchestration
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..integrations.confluence.client import ConfluenceClient
from ..integrations.sharepoint.client import SharePointClient
from ..integrations.openai.enterprise_client import EnterpriseGPTClient
from .cache_manager import CacheManager
from .permission_manager import PermissionManager

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Supported knowledge source types."""
    CONFLUENCE = "confluence"
    SHAREPOINT = "sharepoint"
    TEAMS = "teams"
    GITHUB = "github"
    JIRA = "jira"
    NOTION = "notion"


class ContentPriority(Enum):
    """Content priority levels for orchestration."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ARCHIVE = "archive"


@dataclass
class SourceMetadata:
    """Metadata for knowledge sources."""
    source_type: SourceType
    source_id: str
    name: str
    base_url: str
    enabled: bool = True
    priority: ContentPriority = ContentPriority.MEDIUM
    last_sync: Optional[datetime] = None
    sync_frequency: timedelta = field(default_factory=lambda: timedelta(hours=6))
    content_types: List[str] = field(default_factory=list)
    permissions: Dict[str, Any] = field(default_factory=dict)
    health_status: str = "unknown"
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class UnifiedSearchResult:
    """Unified search result across multiple sources."""
    content_id: str
    title: str
    content: str
    source_type: SourceType
    source_id: str
    url: str
    relevance_score: float
    freshness_score: float
    authority_score: float
    combined_score: float
    last_modified: datetime
    author: str
    tags: List[str] = field(default_factory=list)
    permissions: Dict[str, Any] = field(default_factory=dict)
    content_type: str = "document"
    parent_id: Optional[str] = None
    related_content: List[str] = field(default_factory=list)


@dataclass
class CrossPlatformQuery:
    """Cross-platform query with orchestration metadata."""
    query_id: str
    text: str
    user_id: str
    intent: str
    context: Dict[str, Any]
    source_preferences: List[SourceType] = field(default_factory=list)
    content_type_filters: List[str] = field(default_factory=list)
    freshness_requirement: Optional[timedelta] = None
    authority_requirement: float = 0.0
    max_results_per_source: int = 10
    enable_cross_reference: bool = True
    enable_content_fusion: bool = True


class SourceCoordinator:
    """
    Coordinates knowledge discovery across multiple sources with intelligent orchestration.
    
    Phase 3 capabilities:
    - Unified cross-platform search
    - Intelligent source prioritization
    - Content fusion and cross-referencing
    - Permission-aware orchestration
    - Real-time source health monitoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sources: Dict[str, SourceMetadata] = {}
        self.clients: Dict[SourceType, Any] = {}
        self.cache_manager = CacheManager(config.get("cache", {}))
        self.permission_manager = PermissionManager(config.get("permissions", {}))
        self.gpt_client = EnterpriseGPTClient(config.get("openai", {}))
        
        # Performance tracking
        self.query_stats = {
            "total_queries": 0,
            "avg_response_time": 0.0,
            "source_performance": {},
            "fusion_success_rate": 0.0
        }
        
        # Initialize sources
        self._initialize_sources()
        
        logger.info("SourceCoordinator initialized with multi-source orchestration")
    
    def _initialize_sources(self):
        """Initialize configured knowledge sources."""
        integrations = self.config.get("integrations", {})
        
        # Initialize Confluence
        if integrations.get("confluence", {}).get("enabled", False):
            confluence_config = integrations["confluence"]
            self.clients[SourceType.CONFLUENCE] = ConfluenceClient(confluence_config)
            self.sources["confluence"] = SourceMetadata(
                source_type=SourceType.CONFLUENCE,
                source_id="confluence",
                name="Confluence",
                base_url=confluence_config.get("base_url", ""),
                priority=ContentPriority.HIGH,
                content_types=["page", "blogpost", "attachment"]
            )
        
        # Initialize SharePoint
        if integrations.get("sharepoint", {}).get("enabled", False):
            sharepoint_config = integrations["sharepoint"]
            self.clients[SourceType.SHAREPOINT] = SharePointClient(sharepoint_config)
            self.sources["sharepoint"] = SourceMetadata(
                source_type=SourceType.SHAREPOINT,
                source_id="sharepoint",
                name="SharePoint",
                base_url=sharepoint_config.get("site_url", ""),
                priority=ContentPriority.HIGH,
                content_types=["document", "list", "page"]
            )
        
        logger.info(f"Initialized {len(self.sources)} knowledge sources")
    
    async def unified_search(self, query: CrossPlatformQuery, user_context: Dict[str, Any]) -> List[UnifiedSearchResult]:
        """
        Perform unified search across all configured sources.
        
        Args:
            query: Cross-platform query with orchestration metadata
            user_context: User context for permission filtering
            
        Returns:
            Unified and ranked search results
        """
        start_time = datetime.now()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(query, user_context)
            cached_results = await self.cache_manager.get(cache_key)
            if cached_results:
                logger.info(f"Returning cached results for query: {query.query_id}")
                return cached_results
            
            # Get user permissions
            user_permissions = await self.permission_manager.get_user_permissions(
                query.user_id, user_context
            )
            
            # Execute parallel searches across sources
            search_tasks = []
            for source_id, source_meta in self.sources.items():
                if not source_meta.enabled:
                    continue
                
                # Check source preferences
                if query.source_preferences and source_meta.source_type not in query.source_preferences:
                    continue
                
                # Check user permissions for source
                if not self._check_source_permission(source_meta, user_permissions):
                    continue
                
                task = self._search_source(source_meta, query, user_permissions)
                search_tasks.append(task)
            
            # Wait for all searches to complete
            source_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Process and combine results
            all_results = []
            for i, results in enumerate(source_results):
                if isinstance(results, Exception):
                    logger.error(f"Search failed for source: {results}")
                    continue
                
                if isinstance(results, list):
                    all_results.extend(results)
            
            # Apply cross-platform intelligence
            if query.enable_cross_reference:
                all_results = await self._apply_cross_references(all_results)
            
            if query.enable_content_fusion:
                all_results = await self._apply_content_fusion(all_results, query)
            
            # Rank and filter results
            ranked_results = await self._rank_unified_results(all_results, query, user_context)
            
            # Cache results
            await self.cache_manager.set(cache_key, ranked_results, ttl=1800)
            
            # Update performance metrics
            response_time = (datetime.now() - start_time).total_seconds()
            await self._update_performance_metrics(query, response_time, len(ranked_results))
            
            logger.info(f"Unified search completed: {len(ranked_results)} results in {response_time:.2f}s")
            return ranked_results
            
        except Exception as e:
            logger.error(f"Unified search failed: {str(e)}")
            raise
    
    async def _search_source(
        self, 
        source_meta: SourceMetadata, 
        query: CrossPlatformQuery,
        user_permissions: Dict[str, Any]
    ) -> List[UnifiedSearchResult]:
        """Search a specific knowledge source."""
        try:
            client = self.clients.get(source_meta.source_type)
            if not client:
                logger.warning(f"No client available for source: {source_meta.source_type}")
                return []
            
            # Execute source-specific search
            if source_meta.source_type == SourceType.CONFLUENCE:
                raw_results = await client.search_content(
                    query.text,
                    spaces=query.context.get("confluence_spaces"),
                    content_types=query.content_type_filters or source_meta.content_types,
                    max_results=query.max_results_per_source
                )
            elif source_meta.source_type == SourceType.SHAREPOINT:
                raw_results = await client.search_documents(
                    query.text,
                    sites=query.context.get("sharepoint_sites"),
                    file_types=query.content_type_filters,
                    max_results=query.max_results_per_source
                )
            else:
                logger.warning(f"Search not implemented for source: {source_meta.source_type}")
                return []
            
            # Convert to unified format
            unified_results = []
            for raw_result in raw_results:
                unified_result = await self._convert_to_unified_result(
                    raw_result, source_meta, query
                )
                if unified_result:
                    unified_results.append(unified_result)
            
            # Apply permission filtering
            filtered_results = await self._filter_by_permissions(
                unified_results, user_permissions, source_meta
            )
            
            logger.info(f"Source {source_meta.source_id}: {len(filtered_results)} results")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Search failed for source {source_meta.source_id}: {str(e)}")
            source_meta.error_count += 1
            source_meta.last_error = str(e)
            source_meta.health_status = "error"
            return []
    
    async def _convert_to_unified_result(
        self, 
        raw_result: Dict[str, Any], 
        source_meta: SourceMetadata,
        query: CrossPlatformQuery
    ) -> Optional[UnifiedSearchResult]:
        """Convert source-specific result to unified format."""
        try:
            # Calculate relevance score using AI
            relevance_score = await self._calculate_relevance_score(
                raw_result.get("content", ""), query.text
            )
            
            # Calculate freshness score
            last_modified = raw_result.get("last_modified")
            if isinstance(last_modified, str):
                last_modified = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
            elif not isinstance(last_modified, datetime):
                last_modified = datetime.now()
            
            freshness_score = self._calculate_freshness_score(last_modified)
            
            # Calculate authority score based on source and content metadata
            authority_score = self._calculate_authority_score(raw_result, source_meta)
            
            # Calculate combined score
            combined_score = (
                relevance_score * 0.5 +
                freshness_score * 0.3 +
                authority_score * 0.2
            )
            
            return UnifiedSearchResult(
                content_id=raw_result.get("id", ""),
                title=raw_result.get("title", ""),
                content=raw_result.get("content", ""),
                source_type=source_meta.source_type,
                source_id=source_meta.source_id,
                url=raw_result.get("url", ""),
                relevance_score=relevance_score,
                freshness_score=freshness_score,
                authority_score=authority_score,
                combined_score=combined_score,
                last_modified=last_modified,
                author=raw_result.get("author", ""),
                tags=raw_result.get("tags", []),
                permissions=raw_result.get("permissions", {}),
                content_type=raw_result.get("type", "document"),
                parent_id=raw_result.get("parent_id"),
                related_content=raw_result.get("related", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to convert result to unified format: {str(e)}")
            return None
    
    async def _calculate_relevance_score(self, content: str, query: str) -> float:
        """Calculate AI-powered relevance score."""
        try:
            # Use Enterprise GPT for semantic similarity
            prompt = f"""
            Rate the relevance of this content to the query on a scale of 0.0 to 1.0.
            
            Query: {query}
            
            Content: {content[:2000]}...
            
            Return only a number between 0.0 and 1.0.
            """
            
            response = await self.gpt_client.generate_response(
                prompt, max_tokens=10, temperature=0.1
            )
            
            try:
                score = float(response.strip())
                return max(0.0, min(1.0, score))
            except ValueError:
                # Fallback to keyword matching
                return self._calculate_keyword_relevance(content, query)
                
        except Exception as e:
            logger.warning(f"AI relevance calculation failed: {str(e)}")
            return self._calculate_keyword_relevance(content, query)
    
    def _calculate_keyword_relevance(self, content: str, query: str) -> float:
        """Fallback keyword-based relevance calculation."""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        matches = len(query_words.intersection(content_words))
        return min(1.0, matches / len(query_words))
    
    def _calculate_freshness_score(self, last_modified: datetime) -> float:
        """Calculate freshness score based on content age."""
        now = datetime.now(last_modified.tzinfo) if last_modified.tzinfo else datetime.now()
        age = now - last_modified
        
        # Fresh content (< 30 days) gets high score
        if age.days < 30:
            return 1.0
        # Recent content (< 90 days) gets medium score
        elif age.days < 90:
            return 0.7
        # Older content (< 365 days) gets lower score
        elif age.days < 365:
            return 0.4
        # Very old content gets minimal score
        else:
            return 0.1
    
    def _calculate_authority_score(self, result: Dict[str, Any], source_meta: SourceMetadata) -> float:
        """Calculate authority score based on source and content metadata."""
        base_score = 0.5
        
        # Source priority bonus
        if source_meta.priority == ContentPriority.CRITICAL:
            base_score += 0.3
        elif source_meta.priority == ContentPriority.HIGH:
            base_score += 0.2
        elif source_meta.priority == ContentPriority.MEDIUM:
            base_score += 0.1
        
        # Content type bonus
        if result.get("type") in ["runbook", "procedure", "policy"]:
            base_score += 0.2
        elif result.get("type") in ["documentation", "guide"]:
            base_score += 0.1
        
        # Author authority (if available)
        author = result.get("author", "")
        if "admin" in author.lower() or "lead" in author.lower():
            base_score += 0.1
        
        return min(1.0, base_score)
    
    async def _apply_cross_references(self, results: List[UnifiedSearchResult]) -> List[UnifiedSearchResult]:
        """Apply cross-platform content references."""
        try:
            # Group results by content similarity
            content_groups = {}
            for result in results:
                content_hash = hashlib.md5(result.title.encode()).hexdigest()[:8]
                if content_hash not in content_groups:
                    content_groups[content_hash] = []
                content_groups[content_hash].append(result)
            
            # Add cross-references for related content
            for group in content_groups.values():
                if len(group) > 1:
                    for result in group:
                        related_ids = [r.content_id for r in group if r.content_id != result.content_id]
                        result.related_content.extend(related_ids)
            
            logger.info(f"Applied cross-references to {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Cross-reference application failed: {str(e)}")
            return results
    
    async def _apply_content_fusion(
        self, 
        results: List[UnifiedSearchResult], 
        query: CrossPlatformQuery
    ) -> List[UnifiedSearchResult]:
        """Apply AI-powered content fusion for enhanced results."""
        try:
            if len(results) < 2:
                return results
            
            # Group similar content for fusion
            fusion_candidates = []
            for i, result1 in enumerate(results):
                for j, result2 in enumerate(results[i+1:], i+1):
                    similarity = await self._calculate_content_similarity(result1, result2)
                    if similarity > 0.7:  # High similarity threshold
                        fusion_candidates.append((result1, result2, similarity))
            
            # Apply fusion to top candidates
            fused_results = results.copy()
            for result1, result2, similarity in fusion_candidates[:3]:  # Limit fusion operations
                fused_content = await self._fuse_content(result1, result2, query)
                if fused_content:
                    # Create fused result
                    fused_result = UnifiedSearchResult(
                        content_id=f"fused_{result1.content_id}_{result2.content_id}",
                        title=f"Comprehensive: {result1.title}",
                        content=fused_content,
                        source_type=result1.source_type,  # Primary source
                        source_id="multi_source",
                        url=result1.url,  # Primary URL
                        relevance_score=max(result1.relevance_score, result2.relevance_score),
                        freshness_score=max(result1.freshness_score, result2.freshness_score),
                        authority_score=max(result1.authority_score, result2.authority_score),
                        combined_score=max(result1.combined_score, result2.combined_score) + 0.1,
                        last_modified=max(result1.last_modified, result2.last_modified),
                        author=f"{result1.author}, {result2.author}",
                        tags=list(set(result1.tags + result2.tags)),
                        content_type="fused_content",
                        related_content=[result1.content_id, result2.content_id]
                    )
                    fused_results.append(fused_result)
            
            logger.info(f"Applied content fusion: {len(fusion_candidates)} fusions")
            return fused_results
            
        except Exception as e:
            logger.error(f"Content fusion failed: {str(e)}")
            return results
    
    async def _calculate_content_similarity(
        self, 
        result1: UnifiedSearchResult, 
        result2: UnifiedSearchResult
    ) -> float:
        """Calculate similarity between two content pieces."""
        try:
            # Simple similarity based on title and content overlap
            title_words1 = set(result1.title.lower().split())
            title_words2 = set(result2.title.lower().split())
            
            if not title_words1 or not title_words2:
                return 0.0
            
            title_similarity = len(title_words1.intersection(title_words2)) / len(title_words1.union(title_words2))
            
            # Content similarity (first 500 chars)
            content1_words = set(result1.content[:500].lower().split())
            content2_words = set(result2.content[:500].lower().split())
            
            if not content1_words or not content2_words:
                return title_similarity
            
            content_similarity = len(content1_words.intersection(content2_words)) / len(content1_words.union(content2_words))
            
            return (title_similarity * 0.4 + content_similarity * 0.6)
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0
    
    async def _fuse_content(
        self, 
        result1: UnifiedSearchResult, 
        result2: UnifiedSearchResult,
        query: CrossPlatformQuery
    ) -> Optional[str]:
        """Use AI to fuse content from multiple sources."""
        try:
            prompt = f"""
            Combine and synthesize the following related content pieces to create a comprehensive response to the query.
            Maintain accuracy and cite both sources appropriately.
            
            Query: {query.text}
            
            Source 1 ({result1.source_type.value}): {result1.title}
            {result1.content[:1000]}
            
            Source 2 ({result2.source_type.value}): {result2.title}
            {result2.content[:1000]}
            
            Create a comprehensive synthesis that combines the best information from both sources.
            """
            
            fused_content = await self.gpt_client.generate_response(
                prompt, max_tokens=1500, temperature=0.3
            )
            
            return fused_content
            
        except Exception as e:
            logger.error(f"Content fusion failed: {str(e)}")
            return None
    
    async def _rank_unified_results(
        self, 
        results: List[UnifiedSearchResult], 
        query: CrossPlatformQuery,
        user_context: Dict[str, Any]
    ) -> List[UnifiedSearchResult]:
        """Rank unified results using advanced scoring."""
        try:
            # Apply query-specific filters
            filtered_results = results
            
            # Freshness filter
            if query.freshness_requirement:
                cutoff_date = datetime.now() - query.freshness_requirement
                filtered_results = [
                    r for r in filtered_results 
                    if r.last_modified >= cutoff_date
                ]
            
            # Authority filter
            if query.authority_requirement > 0:
                filtered_results = [
                    r for r in filtered_results 
                    if r.authority_score >= query.authority_requirement
                ]
            
            # Sort by combined score
            ranked_results = sorted(
                filtered_results, 
                key=lambda x: x.combined_score, 
                reverse=True
            )
            
            # Apply diversity to avoid source clustering
            diverse_results = self._apply_result_diversity(ranked_results)
            
            return diverse_results
            
        except Exception as e:
            logger.error(f"Result ranking failed: {str(e)}")
            return results
    
    def _apply_result_diversity(self, results: List[UnifiedSearchResult]) -> List[UnifiedSearchResult]:
        """Apply diversity to prevent source clustering."""
        if len(results) <= 5:
            return results
        
        diverse_results = []
        source_counts = {}
        
        for result in results:
            source_key = f"{result.source_type.value}_{result.source_id}"
            current_count = source_counts.get(source_key, 0)
            
            # Limit results per source to maintain diversity
            if current_count < 3 or len(diverse_results) < 10:
                diverse_results.append(result)
                source_counts[source_key] = current_count + 1
        
        return diverse_results
    
    async def _filter_by_permissions(
        self, 
        results: List[UnifiedSearchResult],
        user_permissions: Dict[str, Any],
        source_meta: SourceMetadata
    ) -> List[UnifiedSearchResult]:
        """Filter results based on user permissions."""
        try:
            filtered_results = []
            
            for result in results:
                if await self.permission_manager.check_content_access(
                    user_permissions, result.permissions, source_meta.source_type.value
                ):
                    filtered_results.append(result)
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Permission filtering failed: {str(e)}")
            return results
    
    def _check_source_permission(
        self, 
        source_meta: SourceMetadata, 
        user_permissions: Dict[str, Any]
    ) -> bool:
        """Check if user has access to a knowledge source."""
        source_permissions = user_permissions.get("sources", {})
        return source_permissions.get(source_meta.source_id, True)  # Default allow
    
    def _generate_cache_key(self, query: CrossPlatformQuery, user_context: Dict[str, Any]) -> str:
        """Generate cache key for unified search."""
        key_data = {
            "query": query.text,
            "user_id": query.user_id,
            "sources": [s.value for s in query.source_preferences],
            "content_types": query.content_type_filters,
            "context_hash": hashlib.md5(str(query.context).encode()).hexdigest()[:8]
        }
        return f"unified_search:{hashlib.md5(str(key_data).encode()).hexdigest()}"
    
    async def _update_performance_metrics(
        self, 
        query: CrossPlatformQuery, 
        response_time: float,
        result_count: int
    ):
        """Update performance tracking metrics."""
        self.query_stats["total_queries"] += 1
        
        # Update average response time
        current_avg = self.query_stats["avg_response_time"]
        total_queries = self.query_stats["total_queries"]
        self.query_stats["avg_response_time"] = (
            (current_avg * (total_queries - 1) + response_time) / total_queries
        )
        
        logger.info(f"Performance: {response_time:.2f}s, {result_count} results")
    
    async def get_source_health(self) -> Dict[str, Any]:
        """Get health status of all knowledge sources."""
        health_status = {}
        
        for source_id, source_meta in self.sources.items():
            health_status[source_id] = {
                "status": source_meta.health_status,
                "enabled": source_meta.enabled,
                "last_sync": source_meta.last_sync.isoformat() if source_meta.last_sync else None,
                "error_count": source_meta.error_count,
                "last_error": source_meta.last_error
            }
        
        return health_status
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get orchestration performance metrics."""
        return {
            "query_stats": self.query_stats,
            "source_count": len(self.sources),
            "enabled_sources": len([s for s in self.sources.values() if s.enabled]),
            "cache_stats": await self.cache_manager.get_stats()
        }

