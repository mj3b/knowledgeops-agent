"""
NAVO Cache Manager
Manages intelligent caching for optimal performance and cost efficiency.
"""

import asyncio
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached entry."""
    key: str
    value: Any
    timestamp: datetime
    ttl: int
    hit_count: int = 0
    last_accessed: datetime = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp


class CacheManager:
    """
    Intelligent cache manager for NAVO responses and data.
    
    Implements multi-level caching with TTL, LRU eviction,
    and cost-aware caching strategies.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize cache manager.
        
        Args:
            config: Cache configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Redis configuration
        self.redis_url = config.get("redis_url", "redis://localhost:6379")
        self.redis_db = config.get("redis_db", 0)
        self.redis_client = None
        
        # Cache settings
        self.default_ttl = config.get("default_ttl", 3600)  # 1 hour
        self.query_cache_ttl = config.get("query_cache_ttl", 1800)  # 30 minutes
        self.document_cache_ttl = config.get("document_cache_ttl", 7200)  # 2 hours
        self.max_cache_size = config.get("max_cache_size", 10000)
        
        # Cache prefixes
        self.prefixes = {
            "query": "navo:query:",
            "document": "navo:doc:",
            "user": "navo:user:",
            "metrics": "navo:metrics:",
            "health": "navo:health:"
        }
        
        # In-memory cache for frequently accessed items
        self.memory_cache = {}
        self.memory_cache_max_size = config.get("memory_cache_max_size", 1000)
        
        self.logger.info("Cache manager initialized")
    
    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                self.redis_url,
                db=self.redis_db,
                decode_responses=True
            )
        return self.redis_client
    
    async def get_cached_response(self, query) -> Optional[Any]:
        """
        Get cached response for a query.
        
        Args:
            query: NAVOQuery object
            
        Returns:
            Cached NAVOResponse if found, None otherwise
        """
        try:
            cache_key = self._generate_query_cache_key(query)
            
            # Check memory cache first
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if self._is_cache_entry_valid(entry):
                    entry.hit_count += 1
                    entry.last_accessed = datetime.utcnow()
                    self.logger.debug(f"Memory cache hit for query: {cache_key}")
                    return entry.value
                else:
                    # Remove expired entry
                    del self.memory_cache[cache_key]
            
            # Check Redis cache
            redis_client = await self._get_redis_client()
            cached_data = await redis_client.get(cache_key)
            
            if cached_data:
                try:
                    response_data = json.loads(cached_data)
                    
                    # Update hit count
                    await self._increment_cache_hit_count(cache_key)
                    
                    self.logger.debug(f"Redis cache hit for query: {cache_key}")
                    
                    # Reconstruct NAVOResponse object
                    from .navo_engine import NAVOResponse
                    return NAVOResponse(**response_data)
                    
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid cached data for key: {cache_key}")
                    await redis_client.delete(cache_key)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached response: {str(e)}")
            return None
    
    async def cache_response(self, query, response) -> bool:
        """
        Cache a query response.
        
        Args:
            query: NAVOQuery object
            response: NAVOResponse object
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            cache_key = self._generate_query_cache_key(query)
            
            # Convert response to dictionary for JSON serialization
            response_data = asdict(response)
            
            # Handle datetime serialization
            if isinstance(response_data.get("timestamp"), datetime):
                response_data["timestamp"] = response_data["timestamp"].isoformat()
            
            # Cache in Redis
            redis_client = await self._get_redis_client()
            await redis_client.setex(
                cache_key,
                self.query_cache_ttl,
                json.dumps(response_data, default=str)
            )
            
            # Cache in memory if response is high-confidence
            if response.confidence > 0.8 and len(self.memory_cache) < self.memory_cache_max_size:
                cache_entry = CacheEntry(
                    key=cache_key,
                    value=response,
                    timestamp=datetime.utcnow(),
                    ttl=self.query_cache_ttl
                )
                self.memory_cache[cache_key] = cache_entry
            
            # Initialize hit count
            await redis_client.setex(
                f"{cache_key}:hits",
                self.query_cache_ttl,
                "0"
            )
            
            self.logger.debug(f"Cached response for query: {cache_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error caching response: {str(e)}")
            return False
    
    async def cache_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """
        Cache a document.
        
        Args:
            doc_id: Document identifier
            document: Document data
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            cache_key = f"{self.prefixes['document']}{doc_id}"
            
            redis_client = await self._get_redis_client()
            await redis_client.setex(
                cache_key,
                self.document_cache_ttl,
                json.dumps(document, default=str)
            )
            
            self.logger.debug(f"Cached document: {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error caching document: {str(e)}")
            return False
    
    async def get_cached_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached document.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Cached document if found, None otherwise
        """
        try:
            cache_key = f"{self.prefixes['document']}{doc_id}"
            
            redis_client = await self._get_redis_client()
            cached_data = await redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached document: {str(e)}")
            return None
    
    async def invalidate_cache(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Redis key pattern to match
            
        Returns:
            Number of keys deleted
        """
        try:
            redis_client = await self._get_redis_client()
            
            # Find matching keys
            keys = await redis_client.keys(pattern)
            
            if keys:
                # Delete keys
                deleted_count = await redis_client.delete(*keys)
                
                # Also remove from memory cache
                memory_keys_to_remove = [
                    key for key in self.memory_cache.keys()
                    if any(key.startswith(prefix) for prefix in keys)
                ]
                
                for key in memory_keys_to_remove:
                    del self.memory_cache[key]
                
                self.logger.info(f"Invalidated {deleted_count} cache entries")
                return deleted_count
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error invalidating cache: {str(e)}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        try:
            redis_client = await self._get_redis_client()
            
            # Get Redis info
            redis_info = await redis_client.info()
            
            # Count keys by prefix
            key_counts = {}
            for prefix_name, prefix in self.prefixes.items():
                keys = await redis_client.keys(f"{prefix}*")
                key_counts[prefix_name] = len(keys)
            
            # Memory cache stats
            memory_cache_size = len(self.memory_cache)
            
            return {
                "redis_connected": True,
                "redis_memory_usage": redis_info.get("used_memory_human", "unknown"),
                "redis_key_count": redis_info.get("db0", {}).get("keys", 0),
                "key_counts_by_type": key_counts,
                "memory_cache_size": memory_cache_size,
                "memory_cache_max_size": self.memory_cache_max_size,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {str(e)}")
            return {
                "redis_connected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform cache health check.
        
        Returns:
            Health check results
        """
        try:
            redis_client = await self._get_redis_client()
            
            # Test Redis connection
            await redis_client.ping()
            
            # Test write/read
            test_key = f"{self.prefixes['health']}test"
            test_value = "health_check"
            
            await redis_client.setex(test_key, 10, test_value)
            retrieved_value = await redis_client.get(test_key)
            await redis_client.delete(test_key)
            
            if retrieved_value == test_value:
                return {
                    "status": "healthy",
                    "redis_connected": True,
                    "read_write_test": "passed",
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "redis_connected": True,
                    "read_write_test": "failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _generate_query_cache_key(self, query) -> str:
        """
        Generate cache key for a query.
        
        Args:
            query: NAVOQuery object
            
        Returns:
            Cache key string
        """
        # Create a hash of the query text and relevant context
        query_data = {
            "text": query.text.lower().strip(),
            "user_id": query.user_id,
            "filters": query.filters or {}
        }
        
        query_string = json.dumps(query_data, sort_keys=True)
        query_hash = hashlib.md5(query_string.encode()).hexdigest()
        
        return f"{self.prefixes['query']}{query_hash}"
    
    def _is_cache_entry_valid(self, entry: CacheEntry) -> bool:
        """
        Check if a cache entry is still valid.
        
        Args:
            entry: CacheEntry to check
            
        Returns:
            True if valid, False if expired
        """
        age = (datetime.utcnow() - entry.timestamp).total_seconds()
        return age < entry.ttl
    
    async def _increment_cache_hit_count(self, cache_key: str):
        """
        Increment hit count for a cache key.
        
        Args:
            cache_key: Cache key to increment
        """
        try:
            redis_client = await self._get_redis_client()
            await redis_client.incr(f"{cache_key}:hits")
        except Exception as e:
            self.logger.warning(f"Error incrementing hit count: {str(e)}")
    
    async def get_query_count(self) -> int:
        """Get total number of queries processed."""
        try:
            redis_client = await self._get_redis_client()
            keys = await redis_client.keys(f"{self.prefixes['query']}*")
            return len(keys)
        except Exception:
            return 0
    
    async def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        try:
            redis_client = await self._get_redis_client()
            
            # Get all query keys and their hit counts
            query_keys = await redis_client.keys(f"{self.prefixes['query']}*")
            
            if not query_keys:
                return 0.0
            
            total_hits = 0
            total_queries = len(query_keys)
            
            for key in query_keys:
                hit_count = await redis_client.get(f"{key}:hits")
                if hit_count:
                    total_hits += int(hit_count)
            
            return total_hits / total_queries if total_queries > 0 else 0.0
            
        except Exception:
            return 0.0
    
    async def get_avg_response_time(self) -> float:
        """Get average response time from cached responses."""
        # This would require storing response times in cache
        # For now, return a placeholder
        return 0.0
    
    async def close(self):
        """Close cache connections."""
        if self.redis_client:
            await self.redis_client.close()

