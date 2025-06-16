"""
NAVO Enhanced Memory Layer
Inspired by JUNO's memory architecture, adapted for knowledge management
"""

import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class KnowledgeMemoryType(Enum):
    """Types of knowledge memory stored in NAVO."""
    DOCUMENT = "document"        # Specific documents and their metadata
    QUERY = "query"             # User query patterns and preferences  
    SEMANTIC = "semantic"       # Learned relationships between concepts
    CONTEXTUAL = "contextual"   # Conversation context and working memory
    USAGE = "usage"             # Document usage patterns and effectiveness

class ConfidenceLevel(Enum):
    """Confidence levels for knowledge recommendations."""
    VERY_LOW = "very_low"       # 0.0 - 0.3
    LOW = "low"                 # 0.3 - 0.5
    MEDIUM = "medium"           # 0.5 - 0.7
    HIGH = "high"               # 0.7 - 0.9
    VERY_HIGH = "very_high"     # 0.9 - 1.0

@dataclass
class KnowledgeMemoryEntry:
    """Represents a single knowledge memory entry in NAVO."""
    id: str
    memory_type: KnowledgeMemoryType
    content: Dict[str, Any]
    context: Dict[str, Any]
    confidence: float
    timestamp: datetime
    expires_at: Optional[datetime] = None
    tags: List[str] = None
    source: str = "navo"
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class NAVOMemoryLayer:
    """
    Enhanced memory layer for NAVO knowledge management.
    Provides persistent storage and retrieval of knowledge patterns.
    """
    
    def __init__(self, db_path: str = "navo_memory.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize the knowledge memory database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_memories (
                id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                context TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL,
                expires_at TEXT,
                tags TEXT,
                source TEXT DEFAULT 'navo',
                user_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for efficient querying
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_type ON knowledge_memories(memory_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON knowledge_memories(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON knowledge_memories(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_confidence ON knowledge_memories(confidence)
        """)
        
        conn.commit()
        conn.close()
        
    def store_memory(self, memory: KnowledgeMemoryEntry) -> bool:
        """Store a knowledge memory entry."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO knowledge_memories 
                (id, memory_type, content, context, confidence, timestamp, expires_at, tags, source, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.memory_type.value,
                json.dumps(memory.content),
                json.dumps(memory.context),
                memory.confidence,
                memory.timestamp.isoformat(),
                memory.expires_at.isoformat() if memory.expires_at else None,
                json.dumps(memory.tags),
                memory.source,
                memory.user_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored knowledge memory: {memory.id} ({memory.memory_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store knowledge memory: {e}")
            return False
    
    def retrieve_memories(self, 
                         memory_type: Optional[KnowledgeMemoryType] = None,
                         user_id: Optional[str] = None,
                         min_confidence: float = 0.0,
                         limit: int = 100) -> List[KnowledgeMemoryEntry]:
        """Retrieve knowledge memories based on criteria."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT id, memory_type, content, context, confidence, timestamp, expires_at, tags, source, user_id
                FROM knowledge_memories 
                WHERE confidence >= ?
                AND (expires_at IS NULL OR expires_at > ?)
            """
            params = [min_confidence, datetime.now().isoformat()]
            
            if memory_type:
                query += " AND memory_type = ?"
                params.append(memory_type.value)
                
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
                
            query += " ORDER BY confidence DESC, timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            memories = []
            for row in rows:
                memory = KnowledgeMemoryEntry(
                    id=row[0],
                    memory_type=KnowledgeMemoryType(row[1]),
                    content=json.loads(row[2]),
                    context=json.loads(row[3]),
                    confidence=row[4],
                    timestamp=datetime.fromisoformat(row[5]),
                    expires_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    tags=json.loads(row[7]),
                    source=row[8],
                    user_id=row[9]
                )
                memories.append(memory)
                
            return memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve knowledge memories: {e}")
            return []
    
    def store_document_memory(self, document_url: str, document_title: str, 
                            query_context: str, user_id: str, 
                            relevance_score: float) -> str:
        """Store memory of a document access for future recommendations."""
        memory_id = hashlib.md5(f"{document_url}_{user_id}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        memory = KnowledgeMemoryEntry(
            id=memory_id,
            memory_type=KnowledgeMemoryType.DOCUMENT,
            content={
                "document_url": document_url,
                "document_title": document_title,
                "relevance_score": relevance_score,
                "access_count": 1
            },
            context={
                "query_context": query_context,
                "user_context": user_id
            },
            confidence=relevance_score,
            timestamp=datetime.now(),
            expires_at=datetime.now() + timedelta(days=90),  # Documents expire after 90 days
            tags=["document_access"],
            user_id=user_id
        )
        
        self.store_memory(memory)
        return memory_id
    
    def store_query_pattern(self, query: str, user_id: str, 
                          successful_documents: List[str]) -> str:
        """Store successful query patterns for future optimization."""
        memory_id = hashlib.md5(f"query_{query}_{user_id}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        memory = KnowledgeMemoryEntry(
            id=memory_id,
            memory_type=KnowledgeMemoryType.QUERY,
            content={
                "query": query,
                "successful_documents": successful_documents,
                "query_tokens": query.lower().split(),
                "success_count": len(successful_documents)
            },
            context={
                "user_id": user_id,
                "query_length": len(query),
                "query_complexity": len(query.split())
            },
            confidence=min(1.0, len(successful_documents) / 5.0),  # Higher confidence with more successful docs
            timestamp=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30),  # Query patterns expire after 30 days
            tags=["query_pattern"],
            user_id=user_id
        )
        
        self.store_memory(memory)
        return memory_id
    
    def get_document_recommendations(self, query: str, user_id: str, 
                                   limit: int = 5) -> List[Dict[str, Any]]:
        """Get document recommendations based on stored memories."""
        # Get similar query patterns
        query_memories = self.retrieve_memories(
            memory_type=KnowledgeMemoryType.QUERY,
            user_id=user_id,
            min_confidence=0.3,
            limit=20
        )
        
        # Get document access patterns
        doc_memories = self.retrieve_memories(
            memory_type=KnowledgeMemoryType.DOCUMENT,
            user_id=user_id,
            min_confidence=0.5,
            limit=50
        )
        
        recommendations = []
        query_tokens = set(query.lower().split())
        
        # Score documents based on query similarity and past success
        for doc_memory in doc_memories:
            score = 0.0
            
            # Check if this document was successful for similar queries
            for query_memory in query_memories:
                query_tokens_stored = set(query_memory.content.get("query_tokens", []))
                similarity = len(query_tokens.intersection(query_tokens_stored)) / len(query_tokens.union(query_tokens_stored))
                
                if doc_memory.content["document_url"] in query_memory.content.get("successful_documents", []):
                    score += similarity * query_memory.confidence
            
            # Add base relevance score
            score += doc_memory.content.get("relevance_score", 0.0) * 0.3
            
            if score > 0.1:  # Minimum threshold
                recommendations.append({
                    "document_url": doc_memory.content["document_url"],
                    "document_title": doc_memory.content["document_title"],
                    "confidence_score": min(1.0, score),
                    "reason": "Based on your previous successful searches",
                    "memory_id": doc_memory.id
                })
        
        # Sort by confidence and return top results
        recommendations.sort(key=lambda x: x["confidence_score"], reverse=True)
        return recommendations[:limit]
    
    def update_document_success(self, memory_id: str, was_helpful: bool):
        """Update document memory based on user feedback."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current memory
            cursor.execute("SELECT content, confidence FROM knowledge_memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            
            if row:
                content = json.loads(row[0])
                current_confidence = row[1]
                
                # Update access count and confidence
                content["access_count"] = content.get("access_count", 0) + 1
                
                if was_helpful:
                    # Increase confidence for helpful documents
                    new_confidence = min(1.0, current_confidence + 0.1)
                    content["helpful_count"] = content.get("helpful_count", 0) + 1
                else:
                    # Decrease confidence for unhelpful documents
                    new_confidence = max(0.0, current_confidence - 0.1)
                    content["unhelpful_count"] = content.get("unhelpful_count", 0) + 1
                
                cursor.execute("""
                    UPDATE knowledge_memories 
                    SET content = ?, confidence = ? 
                    WHERE id = ?
                """, (json.dumps(content), new_confidence, memory_id))
                
                conn.commit()
                logger.info(f"Updated document memory {memory_id}: helpful={was_helpful}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update document success: {e}")
    
    def cleanup_expired_memories(self):
        """Remove expired memories from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM knowledge_memories 
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (datetime.now().isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} expired knowledge memories")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired memories: {e}")
            return 0

