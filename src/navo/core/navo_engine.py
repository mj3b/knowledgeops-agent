"""
NAVO Core Engine
Enhanced with JUNO-inspired memory and reasoning capabilities
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .query_processor import NAVOQueryProcessor
from .response_generator import NAVOResponseGenerator
from .cache_manager import NAVOCacheManager
from .permission_manager import NAVOPermissionManager
from .memory_layer import NAVOMemoryLayer
from .reasoning_engine import NAVOReasoningEngine
from ..integrations.openai.enterprise_client import EnterpriseGPTClient

logger = logging.getLogger(__name__)

class NAVOEngine:
    """
    Enhanced NAVO Core Engine with JUNO-inspired capabilities.
    Integrates memory, reasoning, and Enterprise GPT for intelligent knowledge discovery.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize core components
        self.query_processor = NAVOQueryProcessor(config)
        self.response_generator = NAVOResponseGenerator(config)
        self.cache_manager = NAVOCacheManager(config)
        self.permission_manager = NAVOPermissionManager(config)
        
        # Initialize JUNO-inspired components
        self.memory_layer = NAVOMemoryLayer(
            db_path=config.get("memory", {}).get("db_path", "navo_memory.db")
        )
        self.reasoning_engine = NAVOReasoningEngine(memory_layer=self.memory_layer)
        
        # Initialize Enterprise GPT client
        openai_config = config.get("openai", {})
        self.enterprise_gpt = EnterpriseGPTClient(
            api_key=openai_config.get("api_key"),
            organization_id=openai_config.get("organization_id"),
            model=openai_config.get("model", "gpt-4")
        )
        
        logger.info("NAVO Engine initialized with enhanced memory and reasoning capabilities")
    
    async def process_query(self, query: str, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhanced query processing with memory and reasoning capabilities.
        """
        start_time = datetime.now()
        
        try:
            # Check cache first
            cache_key = f"query:{user_id}:{hash(query)}"
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached result for query: {query[:50]}...")
                return cached_result
            
            # Process query with enhanced capabilities
            processed_query = await self.query_processor.process(query, user_id, context)
            
            # Check permissions
            if not await self.permission_manager.can_access_knowledge(user_id, processed_query.get("intent")):
                return {
                    "success": False,
                    "error": "Insufficient permissions for this query",
                    "query": query,
                    "timestamp": start_time.isoformat()
                }
            
            # Get available documents from integrations
            available_documents = await self._gather_documents(processed_query, user_id)
            
            # Apply reasoning engine for intelligent document selection
            reasoning_result = self.reasoning_engine.reason_about_query(
                query=query,
                user_id=user_id,
                available_documents=available_documents,
                context=context
            )
            
            # Generate enhanced response using Enterprise GPT
            response = await self._generate_enhanced_response(
                query=query,
                reasoning_result=reasoning_result,
                user_id=user_id
            )
            
            # Store successful interactions in memory
            if response.get("success") and reasoning_result.recommendations:
                await self._store_interaction_memory(query, user_id, reasoning_result)
            
            # Cache the result
            await self.cache_manager.set(cache_key, response, ttl=3600)  # 1 hour TTL
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Processed query in {execution_time:.2f}s with confidence {reasoning_result.final_confidence:.3f}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "timestamp": start_time.isoformat()
            }
    
    async def _gather_documents(self, processed_query: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
        """Gather documents from all available sources."""
        documents = []
        
        # Get documents from Confluence
        try:
            confluence_docs = await self._get_confluence_documents(processed_query, user_id)
            documents.extend(confluence_docs)
        except Exception as e:
            logger.warning(f"Failed to get Confluence documents: {e}")
        
        # Get documents from SharePoint
        try:
            sharepoint_docs = await self._get_sharepoint_documents(processed_query, user_id)
            documents.extend(sharepoint_docs)
        except Exception as e:
            logger.warning(f"Failed to get SharePoint documents: {e}")
        
        # Get memory-based recommendations
        try:
            memory_docs = self.memory_layer.get_document_recommendations(
                query=processed_query.get("original_query", ""),
                user_id=user_id,
                limit=10
            )
            # Convert memory recommendations to document format
            for mem_doc in memory_docs:
                documents.append({
                    "url": mem_doc["document_url"],
                    "title": mem_doc["document_title"],
                    "source_type": "memory",
                    "confidence": mem_doc["confidence_score"],
                    "type": "recommendation"
                })
        except Exception as e:
            logger.warning(f"Failed to get memory recommendations: {e}")
        
        return documents
    
    async def _get_confluence_documents(self, processed_query: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
        """Get documents from Confluence integration."""
        # This would integrate with the actual Confluence client
        # For now, return mock data structure
        return [
            {
                "url": "https://yourcompany.atlassian.net/wiki/spaces/ENG/pages/123456",
                "title": "Engineering Best Practices",
                "content": "Guidelines for engineering teams...",
                "source_type": "confluence",
                "type": "guide",
                "last_updated": "2025-06-15"
            }
        ]
    
    async def _get_sharepoint_documents(self, processed_query: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
        """Get documents from SharePoint integration."""
        # This would integrate with the actual SharePoint client
        # For now, return mock data structure
        return [
            {
                "url": "https://yourcompany.sharepoint.com/sites/Documentation/doc123",
                "title": "API Documentation",
                "content": "Complete API reference...",
                "source_type": "sharepoint",
                "type": "reference",
                "last_updated": "2025-06-14"
            }
        ]
    
    async def _generate_enhanced_response(self, query: str, reasoning_result, user_id: str) -> Dict[str, Any]:
        """Generate enhanced response using Enterprise GPT and reasoning results."""
        try:
            # Prepare context for Enterprise GPT
            context = {
                "query": query,
                "reasoning_summary": reasoning_result.reasoning_summary,
                "recommendations": reasoning_result.recommendations[:5],  # Top 5 recommendations
                "confidence": reasoning_result.final_confidence
            }
            
            # Generate response using Enterprise GPT
            gpt_response = await self.enterprise_gpt.generate_knowledge_response(context)
            
            # Combine with reasoning results
            response = {
                "success": True,
                "query": query,
                "response": gpt_response.get("response", ""),
                "recommendations": reasoning_result.recommendations,
                "reasoning": {
                    "summary": reasoning_result.reasoning_summary,
                    "confidence": reasoning_result.final_confidence,
                    "reasoning_id": reasoning_result.reasoning_id,
                    "execution_time_ms": reasoning_result.execution_time_ms
                },
                "sources": self._extract_sources(reasoning_result),
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced response: {e}")
            # Fallback to basic response
            return {
                "success": True,
                "query": query,
                "response": f"Found {len(reasoning_result.recommendations)} relevant documents for your query.",
                "recommendations": reasoning_result.recommendations,
                "reasoning": {
                    "summary": reasoning_result.reasoning_summary,
                    "confidence": reasoning_result.final_confidence,
                    "reasoning_id": reasoning_result.reasoning_id
                },
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
    
    def _extract_sources(self, reasoning_result) -> List[Dict[str, Any]]:
        """Extract source information from reasoning result."""
        sources = []
        
        for step in reasoning_result.steps:
            for source in step.sources:
                sources.append({
                    "source_type": source.source_type,
                    "source_id": source.source_id,
                    "confidence": source.confidence,
                    "metadata": source.metadata
                })
        
        # Remove duplicates and sort by confidence
        unique_sources = {}
        for source in sources:
            key = f"{source['source_type']}:{source['source_id']}"
            if key not in unique_sources or source['confidence'] > unique_sources[key]['confidence']:
                unique_sources[key] = source
        
        return sorted(unique_sources.values(), key=lambda x: x['confidence'], reverse=True)
    
    async def _store_interaction_memory(self, query: str, user_id: str, reasoning_result):
        """Store successful interaction in memory for future learning."""
        try:
            # Store successful documents
            successful_docs = [
                rec["document_url"] for rec in reasoning_result.recommendations[:3]  # Top 3
                if rec.get("confidence_score", 0) > 0.5
            ]
            
            if successful_docs:
                # Store query pattern
                self.memory_layer.store_query_pattern(
                    query=query,
                    user_id=user_id,
                    successful_documents=successful_docs
                )
                
                # Store individual document memories
                for rec in reasoning_result.recommendations[:3]:
                    if rec.get("confidence_score", 0) > 0.5:
                        self.memory_layer.store_document_memory(
                            document_url=rec["document_url"],
                            document_title=rec.get("document_title", ""),
                            query_context=query,
                            user_id=user_id,
                            relevance_score=rec.get("confidence_score", 0.5)
                        )
                
                logger.info(f"Stored interaction memory for query: {query[:50]}...")
                
        except Exception as e:
            logger.warning(f"Failed to store interaction memory: {e}")
    
    async def provide_feedback(self, reasoning_id: str, document_url: str, 
                              was_helpful: bool, user_id: str) -> Dict[str, Any]:
        """Process user feedback to improve future recommendations."""
        try:
            # Find the reasoning result
            reasoning_history = self.reasoning_engine.get_reasoning_history(user_id=user_id)
            reasoning_result = None
            
            for result in reasoning_history:
                if result.reasoning_id == reasoning_id:
                    reasoning_result = result
                    break
            
            if not reasoning_result:
                return {"success": False, "error": "Reasoning session not found"}
            
            # Find the specific recommendation
            recommendation = None
            for rec in reasoning_result.recommendations:
                if rec.get("document_url") == document_url:
                    recommendation = rec
                    break
            
            if not recommendation:
                return {"success": False, "error": "Document recommendation not found"}
            
            # Update memory based on feedback
            memory_id = recommendation.get("memory_id")
            if memory_id:
                self.memory_layer.update_document_success(memory_id, was_helpful)
            
            # Store feedback for future learning
            feedback_memory_id = self.memory_layer.store_memory({
                "id": f"feedback_{reasoning_id}_{document_url}",
                "memory_type": "usage",
                "content": {
                    "reasoning_id": reasoning_id,
                    "document_url": document_url,
                    "was_helpful": was_helpful,
                    "query": reasoning_result.query
                },
                "context": {"user_id": user_id},
                "confidence": 1.0 if was_helpful else 0.0,
                "timestamp": datetime.now(),
                "user_id": user_id
            })
            
            logger.info(f"Processed feedback for document {document_url}: helpful={was_helpful}")
            
            return {
                "success": True,
                "message": "Feedback processed successfully",
                "feedback_id": feedback_memory_id
            }
            
        except Exception as e:
            logger.error(f"Failed to process feedback: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics about NAVO usage and performance."""
        try:
            # Get reasoning history
            reasoning_history = self.reasoning_engine.get_reasoning_history(user_id=user_id, limit=100)
            
            if not reasoning_history:
                return {"success": True, "analytics": {"total_queries": 0}}
            
            # Calculate analytics
            total_queries = len(reasoning_history)
            avg_confidence = sum(r.final_confidence for r in reasoning_history) / total_queries
            avg_execution_time = sum(r.execution_time_ms for r in reasoning_history) / total_queries
            
            # Get memory statistics
            memory_stats = {
                "document_memories": len(self.memory_layer.retrieve_memories(memory_type="document")),
                "query_memories": len(self.memory_layer.retrieve_memories(memory_type="query")),
                "total_memories": len(self.memory_layer.retrieve_memories())
            }
            
            analytics = {
                "total_queries": total_queries,
                "average_confidence": round(avg_confidence, 3),
                "average_execution_time_ms": round(avg_execution_time, 1),
                "memory_statistics": memory_stats,
                "recent_queries": [
                    {
                        "query": r.query[:50] + "..." if len(r.query) > 50 else r.query,
                        "confidence": r.final_confidence,
                        "timestamp": r.timestamp.isoformat(),
                        "recommendations_count": len(r.recommendations)
                    }
                    for r in reasoning_history[:10]
                ]
            }
            
            return {"success": True, "analytics": analytics}
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {"success": False, "error": str(e)}
    
    async def cleanup_expired_data(self):
        """Clean up expired data from memory and cache."""
        try:
            # Cleanup expired memories
            expired_count = self.memory_layer.cleanup_expired_memories()
            
            # Cleanup cache (if supported)
            cache_cleaned = await self.cache_manager.cleanup_expired()
            
            logger.info(f"Cleanup completed: {expired_count} expired memories, cache cleaned: {cache_cleaned}")
            
            return {
                "success": True,
                "expired_memories_cleaned": expired_count,
                "cache_cleaned": cache_cleaned
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
            return {"success": False, "error": str(e)}

