"""
NAVO Query Processor
Processes and understands user queries using OpenAI Enterprise.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..integrations.openai.enterprise_client import OpenAIEnterpriseClient, OpenAIMessage

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Enumeration of possible query intents."""
    SEARCH = "search"
    QUESTION = "question"
    SUMMARY = "summary"
    COMPARISON = "comparison"
    PROCEDURE = "procedure"
    TROUBLESHOOTING = "troubleshooting"
    DEFINITION = "definition"
    UNKNOWN = "unknown"


@dataclass
class ExtractedEntity:
    """Represents an extracted entity from a query."""
    text: str
    type: str  # person, organization, location, technology, etc.
    confidence: float


@dataclass
class ProcessedQuery:
    """Represents a processed and analyzed query."""
    original_text: str
    intent: QueryIntent
    entities: List[ExtractedEntity]
    keywords: List[str]
    context: Dict[str, Any]
    confidence: float
    processing_time: float


class QueryProcessor:
    """
    Processes user queries to understand intent, extract entities,
    and prepare them for knowledge retrieval.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the query processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Intent classification patterns
        self.intent_patterns = {
            QueryIntent.SEARCH: [
                r"find", r"search", r"look for", r"locate", r"where is"
            ],
            QueryIntent.QUESTION: [
                r"what is", r"how to", r"why", r"when", r"who", r"which"
            ],
            QueryIntent.SUMMARY: [
                r"summarize", r"overview", r"summary of", r"brief"
            ],
            QueryIntent.COMPARISON: [
                r"compare", r"difference", r"vs", r"versus", r"better"
            ],
            QueryIntent.PROCEDURE: [
                r"how to", r"steps", r"procedure", r"process", r"guide"
            ],
            QueryIntent.TROUBLESHOOTING: [
                r"error", r"problem", r"issue", r"fix", r"troubleshoot", r"not working"
            ],
            QueryIntent.DEFINITION: [
                r"what is", r"define", r"definition", r"meaning", r"explain"
            ]
        }
        
        # Common organizational entities
        self.org_entities = config.get("organizational_entities", {
            "systems": ["confluence", "sharepoint", "jira", "slack"],
            "departments": ["engineering", "product", "marketing", "sales"],
            "technologies": ["python", "javascript", "react", "docker", "kubernetes"]
        })
        
        self.logger.info("Query processor initialized")
    
    async def process(self, query) -> ProcessedQuery:
        """
        Process a user query to understand intent and extract information.
        
        Args:
            query: NAVOQuery object to process
            
        Returns:
            ProcessedQuery with analysis results
        """
        start_time = datetime.utcnow()
        
        self.logger.info(f"Processing query: {query.text[:100]}...")
        
        try:
            # Clean and normalize the query text
            normalized_text = self._normalize_text(query.text)
            
            # Classify intent
            intent = self._classify_intent(normalized_text)
            
            # Extract entities
            entities = await self._extract_entities(normalized_text)
            
            # Extract keywords
            keywords = self._extract_keywords(normalized_text)
            
            # Build context
            context = self._build_context(query, intent, entities, keywords)
            
            # Calculate confidence
            confidence = self._calculate_confidence(intent, entities, keywords)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            processed_query = ProcessedQuery(
                original_text=query.text,
                intent=intent,
                entities=entities,
                keywords=keywords,
                context=context,
                confidence=confidence,
                processing_time=processing_time
            )
            
            self.logger.info(
                f"Query processed: intent={intent.value}, "
                f"entities={len(entities)}, confidence={confidence:.2f}"
            )
            
            return processed_query
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            
            # Return basic processed query on error
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            return ProcessedQuery(
                original_text=query.text,
                intent=QueryIntent.UNKNOWN,
                entities=[],
                keywords=self._extract_keywords(query.text),
                context={"error": str(e)},
                confidence=0.0,
                processing_time=processing_time
            )
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize query text for processing.
        
        Args:
            text: Raw query text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\?\!\.\-]', ' ', text)
        
        return text
    
    def _classify_intent(self, text: str) -> QueryIntent:
        """
        Classify the intent of the query.
        
        Args:
            text: Normalized query text
            
        Returns:
            Classified intent
        """
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1
            intent_scores[intent] = score
        
        # Return intent with highest score, or UNKNOWN if no matches
        if intent_scores and max(intent_scores.values()) > 0:
            return max(intent_scores, key=intent_scores.get)
        
        return QueryIntent.UNKNOWN
    
    async def _extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        Extract named entities from the query text.
        
        Args:
            text: Normalized query text
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Extract organizational entities using patterns
        for entity_type, entity_list in self.org_entities.items():
            for entity in entity_list:
                if entity.lower() in text:
                    entities.append(ExtractedEntity(
                        text=entity,
                        type=entity_type,
                        confidence=0.8
                    ))
        
        # Extract common technical terms
        tech_patterns = {
            "version": r"v?\d+\.\d+(?:\.\d+)?",
            "code": r"[A-Z]{2,}\d{2,}",  # e.g., PROJ01, SYS-KP
            "url": r"https?://[^\s]+",
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        }
        
        for entity_type, pattern in tech_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append(ExtractedEntity(
                    text=match.group(),
                    type=entity_type,
                    confidence=0.9
                ))
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from the query.
        
        Args:
            text: Query text
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction - remove stop words and short words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "have",
            "has", "had", "do", "does", "did", "will", "would", "could", "should",
            "can", "may", "might", "must", "i", "you", "he", "she", "it", "we",
            "they", "this", "that", "these", "those", "what", "where", "when",
            "why", "how"
        }
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [
            word for word in words 
            if len(word) > 2 and word not in stop_words
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:10]  # Limit to top 10 keywords
    
    def _build_context(
        self, 
        query, 
        intent: QueryIntent, 
        entities: List[ExtractedEntity], 
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Build context information for the query.
        
        Args:
            query: Original NAVOQuery object
            intent: Classified intent
            entities: Extracted entities
            keywords: Extracted keywords
            
        Returns:
            Context dictionary
        """
        context = {
            "user_id": query.user_id,
            "timestamp": query.timestamp.isoformat(),
            "intent": intent.value,
            "entity_types": list(set(entity.type for entity in entities)),
            "keyword_count": len(keywords),
            "query_length": len(query.text),
            "has_question_mark": "?" in query.text,
            "has_technical_terms": any(
                entity.type in ["systems", "technologies", "code"] 
                for entity in entities
            )
        }
        
        # Add user-provided context
        if query.context:
            context.update(query.context)
        
        # Add filters
        if query.filters:
            context["filters"] = query.filters
        
        return context
    
    def _calculate_confidence(
        self, 
        intent: QueryIntent, 
        entities: List[ExtractedEntity], 
        keywords: List[str]
    ) -> float:
        """
        Calculate confidence score for the query processing.
        
        Args:
            intent: Classified intent
            entities: Extracted entities
            keywords: Extracted keywords
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.0
        
        # Base confidence from intent classification
        if intent != QueryIntent.UNKNOWN:
            confidence += 0.4
        
        # Confidence from entities
        if entities:
            entity_confidence = sum(entity.confidence for entity in entities) / len(entities)
            confidence += 0.3 * entity_confidence
        
        # Confidence from keywords
        if keywords:
            keyword_score = min(len(keywords) / 5.0, 1.0)  # Normalize to 0-1
            confidence += 0.3 * keyword_score
        
        return min(confidence, 1.0)

