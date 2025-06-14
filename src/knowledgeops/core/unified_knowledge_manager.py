#!/usr/bin/env python3
"""
Unified Knowledge Integration Framework for KnowledgeOps Agent
Combines Confluence and SharePoint integrations with intelligent content processing and search capabilities.
"""

import os
import json
import logging
import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import hashlib
import pickle
from pathlib import Path

# Vector search and embeddings
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Import our integration modules
from confluence_integration import ConfluenceAPIClient, ConfluenceConfig, ConfluenceContent
from sharepoint_integration import SharePointAPIClient, SharePointConfig, SharePointContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UnifiedContent:
    """Unified content structure that normalizes content from different sources"""
    id: str
    source_type: str  # 'confluence' or 'sharepoint'
    source_id: str
    title: str
    content_text: str
    summary: str
    author: str
    created_date: datetime
    modified_date: datetime
    url: str
    content_type: str
    tags: List[str]
    metadata: Dict[str, Any]
    permissions: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    relevance_score: float = 0.0
    
    # Source-specific fields
    confluence_data: Optional[ConfluenceContent] = None
    sharepoint_data: Optional[SharePointContent] = None

@dataclass
class SearchQuery:
    """Structured search query with context and filters"""
    text: str
    user_context: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    max_results: int = 10
    include_sources: Optional[List[str]] = None  # ['confluence', 'sharepoint']
    semantic_search: bool = True
    keyword_search: bool = True

@dataclass
class SearchResult:
    """Search result with relevance scoring and context"""
    content: UnifiedContent
    relevance_score: float
    match_type: str  # 'semantic', 'keyword', 'hybrid'
    matched_fields: List[str]
    context_snippet: str

class ContentProcessor:
    """Processes and normalizes content from different sources"""
    
    def __init__(self):
        self.embedding_model = None
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """Load sentence transformer model for embeddings"""
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None
    
    def normalize_confluence_content(self, confluence_content: ConfluenceContent) -> UnifiedContent:
        """Convert Confluence content to unified format"""
        return UnifiedContent(
            id=f"confluence_{confluence_content.id}",
            source_type="confluence",
            source_id=confluence_content.id,
            title=confluence_content.title,
            content_text=confluence_content.content_text,
            summary=confluence_content.summary,
            author=confluence_content.author,
            created_date=confluence_content.created_date,
            modified_date=confluence_content.modified_date,
            url=confluence_content.url,
            content_type=confluence_content.content_type,
            tags=confluence_content.tags,
            metadata={
                'space_key': confluence_content.space_key,
                'space_name': confluence_content.space_name,
                'version': confluence_content.version,
                'parent_id': confluence_content.parent_id,
                **confluence_content.metadata
            },
            permissions=confluence_content.permissions,
            confluence_data=confluence_content
        )
    
    def normalize_sharepoint_content(self, sharepoint_content: SharePointContent) -> UnifiedContent:
        """Convert SharePoint content to unified format"""
        return UnifiedContent(
            id=f"sharepoint_{sharepoint_content.id}",
            source_type="sharepoint",
            source_id=sharepoint_content.id,
            title=sharepoint_content.title,
            content_text=sharepoint_content.content_text,
            summary=sharepoint_content.summary,
            author=sharepoint_content.author,
            created_date=sharepoint_content.created_date,
            modified_date=sharepoint_content.modified_date,
            url=sharepoint_content.url,
            content_type=sharepoint_content.content_type,
            tags=sharepoint_content.tags,
            metadata={
                'site_id': sharepoint_content.site_id,
                'site_name': sharepoint_content.site_name,
                'library_name': sharepoint_content.library_name,
                'file_type': sharepoint_content.file_type,
                'file_size': sharepoint_content.file_size,
                'managed_metadata': sharepoint_content.managed_metadata,
                **sharepoint_content.metadata
            },
            permissions=sharepoint_content.permissions,
            sharepoint_data=sharepoint_content
        )
    
    def generate_embedding(self, content: UnifiedContent) -> Optional[np.ndarray]:
        """Generate semantic embedding for content"""
        if not self.embedding_model:
            return None
        
        try:
            # Combine title and content for embedding
            text_for_embedding = f"{content.title}\n{content.summary}"
            if len(text_for_embedding) > 512:  # Truncate for model limits
                text_for_embedding = text_for_embedding[:512]
            
            embedding = self.embedding_model.encode(text_for_embedding)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error generating embedding for content {content.id}: {e}")
            return None
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for keyword-based search"""
        # Simple keyword extraction - in production, use more sophisticated NLP
        import re
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        # Extract words (alphanumeric, 3+ characters)
        words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', text.lower())
        keywords = [word for word in words if word not in stop_words]
        
        # Return unique keywords, limited to top 50
        return list(set(keywords))[:50]

class VectorSearchEngine:
    """Vector-based semantic search engine"""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.content_map = {}  # Maps index position to content ID
        self.is_trained = False
    
    def add_content(self, content_list: List[UnifiedContent]):
        """Add content embeddings to the search index"""
        embeddings = []
        valid_content = []
        
        for content in content_list:
            if content.embedding is not None:
                embeddings.append(content.embedding)
                valid_content.append(content)
        
        if not embeddings:
            logger.warning("No valid embeddings to add to index")
            return
        
        # Normalize embeddings for cosine similarity
        embeddings_array = np.array(embeddings)
        faiss.normalize_L2(embeddings_array)
        
        # Add to index
        start_idx = self.index.ntotal
        self.index.add(embeddings_array)
        
        # Update content mapping
        for i, content in enumerate(valid_content):
            self.content_map[start_idx + i] = content.id
        
        self.is_trained = True
        logger.info(f"Added {len(valid_content)} embeddings to search index")
    
    def search(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar content using vector similarity"""
        if not self.is_trained or self.index.ntotal == 0:
            return []
        
        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx in self.content_map:
                content_id = self.content_map[idx]
                results.append((content_id, float(score)))
        
        return results
    
    def save_index(self, filepath: str):
        """Save the search index to disk"""
        try:
            faiss.write_index(self.index, f"{filepath}.faiss")
            with open(f"{filepath}.map", 'wb') as f:
                pickle.dump(self.content_map, f)
            logger.info(f"Search index saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving search index: {e}")
    
    def load_index(self, filepath: str):
        """Load the search index from disk"""
        try:
            self.index = faiss.read_index(f"{filepath}.faiss")
            with open(f"{filepath}.map", 'rb') as f:
                self.content_map = pickle.load(f)
            self.is_trained = True
            logger.info(f"Search index loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading search index: {e}")

class KeywordSearchEngine:
    """Keyword-based search engine with TF-IDF scoring"""
    
    def __init__(self):
        self.content_keywords = {}  # content_id -> set of keywords
        self.keyword_content = {}   # keyword -> set of content_ids
        self.content_metadata = {}  # content_id -> metadata for scoring
    
    def add_content(self, content_list: List[UnifiedContent], processor: ContentProcessor):
        """Add content to keyword search index"""
        for content in content_list:
            # Extract keywords from title and content
            title_keywords = processor.extract_keywords(content.title)
            content_keywords = processor.extract_keywords(content.content_text[:1000])  # First 1000 chars
            tag_keywords = [tag.lower() for tag in content.tags]
            
            all_keywords = set(title_keywords + content_keywords + tag_keywords)
            
            # Store content keywords
            self.content_keywords[content.id] = all_keywords
            
            # Store metadata for scoring
            self.content_metadata[content.id] = {
                'title': content.title,
                'content_length': len(content.content_text),
                'tags': content.tags,
                'created_date': content.created_date,
                'modified_date': content.modified_date
            }
            
            # Update keyword -> content mapping
            for keyword in all_keywords:
                if keyword not in self.keyword_content:
                    self.keyword_content[keyword] = set()
                self.keyword_content[keyword].add(content.id)
        
        logger.info(f"Added {len(content_list)} items to keyword search index")
    
    def search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        """Search using keyword matching with TF-IDF-like scoring"""
        query_keywords = set(query.lower().split())
        
        # Find content that matches any query keywords
        matching_content = set()
        for keyword in query_keywords:
            if keyword in self.keyword_content:
                matching_content.update(self.keyword_content[keyword])
        
        if not matching_content:
            return []
        
        # Score each matching content
        scored_results = []
        for content_id in matching_content:
            score = self._calculate_keyword_score(content_id, query_keywords)
            scored_results.append((content_id, score))
        
        # Sort by score and return top k
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:k]
    
    def _calculate_keyword_score(self, content_id: str, query_keywords: set) -> float:
        """Calculate relevance score for content based on keyword matching"""
        content_keywords = self.content_keywords.get(content_id, set())
        metadata = self.content_metadata.get(content_id, {})
        
        # Calculate keyword overlap
        matching_keywords = query_keywords.intersection(content_keywords)
        if not matching_keywords:
            return 0.0
        
        # Base score: ratio of matching keywords
        base_score = len(matching_keywords) / len(query_keywords)
        
        # Boost for title matches
        title_words = set(metadata.get('title', '').lower().split())
        title_matches = query_keywords.intersection(title_words)
        title_boost = len(title_matches) * 0.5
        
        # Boost for tag matches
        tag_words = set(tag.lower() for tag in metadata.get('tags', []))
        tag_matches = query_keywords.intersection(tag_words)
        tag_boost = len(tag_matches) * 0.3
        
        # Recency boost (newer content gets slight boost)
        modified_date = metadata.get('modified_date')
        recency_boost = 0.0
        if modified_date:
            days_old = (datetime.now(timezone.utc) - modified_date).days
            recency_boost = max(0, (365 - days_old) / 365 * 0.1)  # Max 0.1 boost for recent content
        
        total_score = base_score + title_boost + tag_boost + recency_boost
        return min(total_score, 1.0)  # Cap at 1.0

class UnifiedKnowledgeManager:
    """Main manager that coordinates all knowledge sources and search capabilities"""
    
    def __init__(self, confluence_config: Optional[ConfluenceConfig] = None, 
                 sharepoint_config: Optional[SharePointConfig] = None):
        self.confluence_config = confluence_config
        self.sharepoint_config = sharepoint_config
        
        # Initialize clients
        self.confluence_client = ConfluenceAPIClient(confluence_config) if confluence_config else None
        self.sharepoint_client = SharePointAPIClient(sharepoint_config) if sharepoint_config else None
        
        # Initialize processing and search components
        self.content_processor = ContentProcessor()
        self.vector_search = VectorSearchEngine()
        self.keyword_search = KeywordSearchEngine()
        
        # Content storage
        self.unified_content = {}  # content_id -> UnifiedContent
        self.last_sync_time = {}   # source -> datetime
        
        # Configuration
        self.cache_dir = Path("./knowledge_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    async def initialize(self):
        """Initialize all clients and load cached data"""
        logger.info("Initializing Unified Knowledge Manager")
        
        # Initialize clients
        if self.confluence_client:
            await self.confluence_client.initialize()
            logger.info("Confluence client initialized")
        
        if self.sharepoint_client:
            await self.sharepoint_client.initialize()
            logger.info("SharePoint client initialized")
        
        # Load cached search indices
        self._load_cached_indices()
        
        logger.info("Unified Knowledge Manager initialization complete")
    
    async def sync_all_content(self, force_full_sync: bool = False):
        """Sync content from all configured sources"""
        logger.info("Starting content synchronization")
        
        all_content = []
        
        # Sync Confluence content
        if self.confluence_client:
            confluence_content = await self._sync_confluence_content(force_full_sync)
            all_content.extend(confluence_content)
        
        # Sync SharePoint content
        if self.sharepoint_client:
            sharepoint_content = await self._sync_sharepoint_content(force_full_sync)
            all_content.extend(sharepoint_content)
        
        # Process and index content
        if all_content:
            await self._process_and_index_content(all_content)
        
        logger.info(f"Content synchronization complete. Total items: {len(self.unified_content)}")
    
    async def _sync_confluence_content(self, force_full_sync: bool = False) -> List[UnifiedContent]:
        """Sync content from Confluence"""
        logger.info("Syncing Confluence content")
        
        since = None
        if not force_full_sync and 'confluence' in self.last_sync_time:
            since = self.last_sync_time['confluence']
        
        try:
            confluence_items = await self.confluence_client.sync_content(since=since)
            unified_items = [
                self.content_processor.normalize_confluence_content(item)
                for item in confluence_items
            ]
            
            self.last_sync_time['confluence'] = datetime.now(timezone.utc)
            logger.info(f"Synced {len(unified_items)} items from Confluence")
            return unified_items
            
        except Exception as e:
            logger.error(f"Error syncing Confluence content: {e}")
            return []
    
    async def _sync_sharepoint_content(self, force_full_sync: bool = False) -> List[UnifiedContent]:
        """Sync content from SharePoint"""
        logger.info("Syncing SharePoint content")
        
        since = None
        if not force_full_sync and 'sharepoint' in self.last_sync_time:
            since = self.last_sync_time['sharepoint']
        
        try:
            all_sharepoint_items = []
            
            # Get all sites if not configured
            sites = self.sharepoint_config.sites or []
            if not sites:
                discovered_sites = await self.sharepoint_client.discover_sites()
                sites = [site['id'] for site in discovered_sites[:10]]  # Limit to first 10 sites
            
            # Sync content from each site
            for site_id in sites:
                try:
                    site_items = await self.sharepoint_client.sync_site_content(site_id, since=since)
                    all_sharepoint_items.extend(site_items)
                except Exception as e:
                    logger.error(f"Error syncing SharePoint site {site_id}: {e}")
            
            unified_items = [
                self.content_processor.normalize_sharepoint_content(item)
                for item in all_sharepoint_items
            ]
            
            self.last_sync_time['sharepoint'] = datetime.now(timezone.utc)
            logger.info(f"Synced {len(unified_items)} items from SharePoint")
            return unified_items
            
        except Exception as e:
            logger.error(f"Error syncing SharePoint content: {e}")
            return []
    
    async def _process_and_index_content(self, content_list: List[UnifiedContent]):
        """Process content and update search indices"""
        logger.info("Processing and indexing content")
        
        # Generate embeddings
        for content in content_list:
            content.embedding = self.content_processor.generate_embedding(content)
            self.unified_content[content.id] = content
        
        # Update search indices
        self.vector_search.add_content(content_list)
        self.keyword_search.add_content(content_list, self.content_processor)
        
        # Save indices to cache
        self._save_cached_indices()
        
        logger.info(f"Processed and indexed {len(content_list)} content items")
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform unified search across all content sources"""
        logger.info(f"Searching for: {query.text}")
        
        results = []
        
        # Semantic search
        if query.semantic_search and self.content_processor.embedding_model:
            semantic_results = await self._semantic_search(query)
            results.extend(semantic_results)
        
        # Keyword search
        if query.keyword_search:
            keyword_results = await self._keyword_search(query)
            results.extend(keyword_results)
        
        # Combine and rank results
        final_results = self._combine_and_rank_results(results, query)
        
        # Apply filters
        filtered_results = self._apply_filters(final_results, query)
        
        # Limit results
        limited_results = filtered_results[:query.max_results]
        
        logger.info(f"Search completed. Found {len(limited_results)} results")
        return limited_results
    
    async def _semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform semantic search using vector embeddings"""
        if not self.content_processor.embedding_model:
            return []
        
        # Generate query embedding
        query_embedding = self.content_processor.embedding_model.encode(query.text)
        
        # Search vector index
        vector_results = self.vector_search.search(query_embedding, k=query.max_results * 2)
        
        results = []
        for content_id, score in vector_results:
            if content_id in self.unified_content:
                content = self.unified_content[content_id]
                result = SearchResult(
                    content=content,
                    relevance_score=score,
                    match_type='semantic',
                    matched_fields=['content', 'title'],
                    context_snippet=content.summary
                )
                results.append(result)
        
        return results
    
    async def _keyword_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform keyword-based search"""
        keyword_results = self.keyword_search.search(query.text, k=query.max_results * 2)
        
        results = []
        for content_id, score in keyword_results:
            if content_id in self.unified_content:
                content = self.unified_content[content_id]
                
                # Generate context snippet
                context_snippet = self._generate_context_snippet(content, query.text)
                
                result = SearchResult(
                    content=content,
                    relevance_score=score,
                    match_type='keyword',
                    matched_fields=['title', 'content', 'tags'],
                    context_snippet=context_snippet
                )
                results.append(result)
        
        return results
    
    def _combine_and_rank_results(self, results: List[SearchResult], query: SearchQuery) -> List[SearchResult]:
        """Combine and rank search results from different methods"""
        # Group results by content ID
        content_results = {}
        
        for result in results:
            content_id = result.content.id
            if content_id not in content_results:
                content_results[content_id] = []
            content_results[content_id].append(result)
        
        # Combine scores for content that appears in multiple result sets
        final_results = []
        for content_id, content_result_list in content_results.items():
            if len(content_result_list) == 1:
                # Single result
                final_results.append(content_result_list[0])
            else:
                # Multiple results - combine scores
                combined_result = content_result_list[0]
                combined_score = 0.0
                match_types = []
                
                for result in content_result_list:
                    combined_score += result.relevance_score
                    match_types.append(result.match_type)
                
                # Average the scores and mark as hybrid
                combined_result.relevance_score = combined_score / len(content_result_list)
                combined_result.match_type = 'hybrid' if len(set(match_types)) > 1 else match_types[0]
                
                final_results.append(combined_result)
        
        # Sort by relevance score
        final_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return final_results
    
    def _apply_filters(self, results: List[SearchResult], query: SearchQuery) -> List[SearchResult]:
        """Apply filters to search results"""
        filtered_results = results
        
        # Filter by source type
        if query.include_sources:
            filtered_results = [
                result for result in filtered_results
                if result.content.source_type in query.include_sources
            ]
        
        # Apply custom filters
        if query.filters:
            # Date range filter
            if 'date_range' in query.filters:
                date_range = query.filters['date_range']
                start_date = date_range.get('start')
                end_date = date_range.get('end')
                
                if start_date or end_date:
                    filtered_results = [
                        result for result in filtered_results
                        if self._date_in_range(result.content.modified_date, start_date, end_date)
                    ]
            
            # Content type filter
            if 'content_types' in query.filters:
                content_types = query.filters['content_types']
                filtered_results = [
                    result for result in filtered_results
                    if result.content.content_type in content_types
                ]
            
            # Tag filter
            if 'tags' in query.filters:
                required_tags = query.filters['tags']
                filtered_results = [
                    result for result in filtered_results
                    if any(tag in result.content.tags for tag in required_tags)
                ]
        
        return filtered_results
    
    def _date_in_range(self, date: datetime, start_date: Optional[str], end_date: Optional[str]) -> bool:
        """Check if date is within specified range"""
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if date < start:
                return False
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if date > end:
                return False
        
        return True
    
    def _generate_context_snippet(self, content: UnifiedContent, query: str) -> str:
        """Generate a context snippet showing query matches"""
        query_words = query.lower().split()
        content_text = content.content_text.lower()
        
        # Find the best matching sentence
        sentences = content.content_text.split('.')
        best_sentence = content.summary
        best_score = 0
        
        for sentence in sentences[:10]:  # Check first 10 sentences
            sentence_lower = sentence.lower()
            score = sum(1 for word in query_words if word in sentence_lower)
            if score > best_score:
                best_score = score
                best_sentence = sentence.strip()
        
        # Truncate if too long
        if len(best_sentence) > 200:
            best_sentence = best_sentence[:200] + "..."
        
        return best_sentence
    
    def _save_cached_indices(self):
        """Save search indices to cache"""
        try:
            # Save vector index
            vector_cache_path = self.cache_dir / "vector_index"
            self.vector_search.save_index(str(vector_cache_path))
            
            # Save content metadata
            content_cache_path = self.cache_dir / "content_cache.json"
            content_data = {}
            for content_id, content in self.unified_content.items():
                content_dict = asdict(content)
                # Remove embedding for JSON serialization
                content_dict.pop('embedding', None)
                content_dict.pop('confluence_data', None)
                content_dict.pop('sharepoint_data', None)
                # Convert datetime objects to ISO strings
                content_dict['created_date'] = content.created_date.isoformat()
                content_dict['modified_date'] = content.modified_date.isoformat()
                content_data[content_id] = content_dict
            
            with open(content_cache_path, 'w') as f:
                json.dump({
                    'content': content_data,
                    'last_sync_time': {
                        source: timestamp.isoformat()
                        for source, timestamp in self.last_sync_time.items()
                    }
                }, f, indent=2)
            
            logger.info("Search indices cached successfully")
        except Exception as e:
            logger.error(f"Error caching search indices: {e}")
    
    def _load_cached_indices(self):
        """Load search indices from cache"""
        try:
            # Load vector index
            vector_cache_path = self.cache_dir / "vector_index"
            if vector_cache_path.with_suffix('.faiss').exists():
                self.vector_search.load_index(str(vector_cache_path))
            
            # Load content metadata
            content_cache_path = self.cache_dir / "content_cache.json"
            if content_cache_path.exists():
                with open(content_cache_path, 'r') as f:
                    cache_data = json.load(f)
                
                # Restore content
                for content_id, content_dict in cache_data.get('content', {}).items():
                    # Convert ISO strings back to datetime objects
                    content_dict['created_date'] = datetime.fromisoformat(content_dict['created_date'])
                    content_dict['modified_date'] = datetime.fromisoformat(content_dict['modified_date'])
                    
                    content = UnifiedContent(**content_dict)
                    self.unified_content[content_id] = content
                
                # Restore last sync times
                for source, timestamp_str in cache_data.get('last_sync_time', {}).items():
                    self.last_sync_time[source] = datetime.fromisoformat(timestamp_str)
                
                # Rebuild keyword search index
                if self.unified_content:
                    content_list = list(self.unified_content.values())
                    self.keyword_search.add_content(content_list, self.content_processor)
                
                logger.info(f"Loaded {len(self.unified_content)} items from cache")
        except Exception as e:
            logger.error(f"Error loading cached indices: {e}")
    
    async def get_content_by_id(self, content_id: str) -> Optional[UnifiedContent]:
        """Get specific content by ID"""
        return self.unified_content.get(content_id)
    
    async def get_content_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed content"""
        stats = {
            'total_content': len(self.unified_content),
            'by_source': {},
            'by_content_type': {},
            'last_sync_times': self.last_sync_time,
            'search_index_size': self.vector_search.index.ntotal if self.vector_search.is_trained else 0
        }
        
        for content in self.unified_content.values():
            # Count by source
            source = content.source_type
            stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
            
            # Count by content type
            content_type = content.content_type
            stats['by_content_type'][content_type] = stats['by_content_type'].get(content_type, 0) + 1
        
        return stats
    
    async def close(self):
        """Close all clients and cleanup resources"""
        if self.confluence_client:
            await self.confluence_client.close()
        
        if self.sharepoint_client:
            await self.sharepoint_client.close()
        
        logger.info("Unified Knowledge Manager closed")

# Example usage
async def main():
    """Example usage of the Unified Knowledge Manager"""
    
    # Configure Confluence
    confluence_config = ConfluenceConfig(
        base_url=os.getenv("CONFLUENCE_BASE_URL", "https://your-domain.atlassian.net"),
        auth_type="api_token",
        username=os.getenv("CONFLUENCE_USERNAME"),
        api_token=os.getenv("CONFLUENCE_API_TOKEN"),
        spaces=["ENG", "DOCS"]
    )
    
    # Configure SharePoint
    sharepoint_config = SharePointConfig(
        tenant_id=os.getenv("SHAREPOINT_TENANT_ID"),
        client_id=os.getenv("SHAREPOINT_CLIENT_ID"),
        client_secret=os.getenv("SHAREPOINT_CLIENT_SECRET"),
        sites=["https://company.sharepoint.com/sites/engineering"]
    )
    
    # Initialize manager
    manager = UnifiedKnowledgeManager(confluence_config, sharepoint_config)
    
    try:
        await manager.initialize()
        
        # Sync content
        await manager.sync_all_content()
        
        # Get stats
        stats = await manager.get_content_stats()
        print(f"Content statistics: {json.dumps(stats, indent=2, default=str)}")
        
        # Perform searches
        search_queries = [
            "deployment procedures",
            "API documentation",
            "security policies",
            "troubleshooting guide"
        ]
        
        for query_text in search_queries:
            query = SearchQuery(
                text=query_text,
                max_results=5,
                semantic_search=True,
                keyword_search=True
            )
            
            results = await manager.search(query)
            
            print(f"\nSearch results for '{query_text}':")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.content.title}")
                print(f"   Source: {result.content.source_type}")
                print(f"   Score: {result.relevance_score:.3f}")
                print(f"   Match: {result.match_type}")
                print(f"   Snippet: {result.context_snippet[:100]}...")
                print()
    
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())

