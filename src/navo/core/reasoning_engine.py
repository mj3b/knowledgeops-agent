"""
NAVO Enhanced Reasoning Engine
Inspired by JUNO's transparent reasoning framework, adapted for knowledge discovery
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ReasoningType(Enum):
    """Types of reasoning processes in NAVO."""
    ANALYTICAL = "analytical"      # Data-driven document analysis
    PREDICTIVE = "predictive"      # Predicting document relevance
    DIAGNOSTIC = "diagnostic"      # Identifying knowledge gaps
    PRESCRIPTIVE = "prescriptive"  # Recommending specific documents
    COMPARATIVE = "comparative"    # Comparing document relevance

class ConfidenceLevel(Enum):
    """Confidence levels for knowledge recommendations."""
    VERY_LOW = "very_low"       # 0.0 - 0.3
    LOW = "low"                 # 0.3 - 0.5
    MEDIUM = "medium"           # 0.5 - 0.7
    HIGH = "high"               # 0.7 - 0.9
    VERY_HIGH = "very_high"     # 0.9 - 1.0

@dataclass
class KnowledgeSource:
    """Represents a knowledge source used in reasoning."""
    source_type: str            # confluence, sharepoint, memory, etc.
    source_id: str             # Document ID or URL
    confidence: float          # Source reliability (0.0 - 1.0)
    timestamp: datetime        # When source was accessed
    metadata: Dict[str, Any]   # Additional source information
    
@dataclass
class ReasoningStep:
    """Represents a single step in the reasoning process."""
    step_id: str
    reasoning_type: ReasoningType
    description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float
    sources: List[KnowledgeSource]
    timestamp: datetime

@dataclass
class ReasoningResult:
    """Complete reasoning result with audit trail."""
    reasoning_id: str
    query: str
    user_id: str
    steps: List[ReasoningStep]
    final_confidence: float
    recommendations: List[Dict[str, Any]]
    reasoning_summary: str
    timestamp: datetime
    execution_time_ms: int

class NAVOReasoningEngine:
    """
    Enhanced reasoning engine for NAVO knowledge discovery.
    Provides transparent, auditable reasoning for document recommendations.
    """
    
    def __init__(self, memory_layer=None):
        self.memory_layer = memory_layer
        self.reasoning_history = []
        
    def reason_about_query(self, query: str, user_id: str, 
                          available_documents: List[Dict[str, Any]],
                          context: Dict[str, Any] = None) -> ReasoningResult:
        """
        Perform comprehensive reasoning about a knowledge query.
        Returns transparent reasoning with confidence scores and audit trail.
        """
        start_time = datetime.now()
        reasoning_id = str(uuid.uuid4())
        steps = []
        
        # Step 1: Analytical - Parse and understand the query
        analytical_step = self._perform_query_analysis(query, user_id, context)
        steps.append(analytical_step)
        
        # Step 2: Predictive - Predict document relevance
        predictive_step = self._predict_document_relevance(
            query, available_documents, analytical_step.outputs
        )
        steps.append(predictive_step)
        
        # Step 3: Diagnostic - Identify potential knowledge gaps
        diagnostic_step = self._diagnose_knowledge_gaps(
            query, available_documents, predictive_step.outputs
        )
        steps.append(diagnostic_step)
        
        # Step 4: Prescriptive - Generate specific recommendations
        prescriptive_step = self._generate_recommendations(
            query, user_id, predictive_step.outputs, diagnostic_step.outputs
        )
        steps.append(prescriptive_step)
        
        # Step 5: Comparative - Rank and compare recommendations
        comparative_step = self._compare_recommendations(
            prescriptive_step.outputs["recommendations"]
        )
        steps.append(comparative_step)
        
        # Calculate final confidence and execution time
        final_confidence = self._calculate_overall_confidence(steps)
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Generate reasoning summary
        reasoning_summary = self._generate_reasoning_summary(steps, final_confidence)
        
        result = ReasoningResult(
            reasoning_id=reasoning_id,
            query=query,
            user_id=user_id,
            steps=steps,
            final_confidence=final_confidence,
            recommendations=comparative_step.outputs["ranked_recommendations"],
            reasoning_summary=reasoning_summary,
            timestamp=start_time,
            execution_time_ms=execution_time
        )
        
        # Store reasoning for audit trail
        self.reasoning_history.append(result)
        
        logger.info(f"Completed reasoning for query '{query}' in {execution_time}ms with confidence {final_confidence:.3f}")
        
        return result
    
    def _perform_query_analysis(self, query: str, user_id: str, 
                               context: Dict[str, Any]) -> ReasoningStep:
        """Analyze the query to understand intent and extract key concepts."""
        step_id = str(uuid.uuid4())
        
        # Extract key concepts and intent
        query_tokens = query.lower().split()
        key_concepts = [token for token in query_tokens if len(token) > 3]
        
        # Determine query intent
        intent_keywords = {
            "how": "procedural",
            "what": "definitional", 
            "where": "locational",
            "why": "explanatory",
            "when": "temporal"
        }
        
        query_intent = "general"
        for keyword, intent in intent_keywords.items():
            if keyword in query.lower():
                query_intent = intent
                break
        
        # Check for urgency indicators
        urgency_keywords = ["urgent", "asap", "immediately", "critical", "emergency"]
        is_urgent = any(keyword in query.lower() for keyword in urgency_keywords)
        
        outputs = {
            "key_concepts": key_concepts,
            "query_intent": query_intent,
            "is_urgent": is_urgent,
            "query_length": len(query),
            "query_complexity": len(query_tokens),
            "processed_tokens": query_tokens
        }
        
        # Confidence based on query clarity and specificity
        confidence = min(1.0, (len(key_concepts) * 0.2) + (0.3 if query_intent != "general" else 0.1))
        
        return ReasoningStep(
            step_id=step_id,
            reasoning_type=ReasoningType.ANALYTICAL,
            description="Analyzed query to understand intent and extract key concepts",
            inputs={"query": query, "user_id": user_id, "context": context or {}},
            outputs=outputs,
            confidence=confidence,
            sources=[],
            timestamp=datetime.now()
        )
    
    def _predict_document_relevance(self, query: str, documents: List[Dict[str, Any]], 
                                   query_analysis: Dict[str, Any]) -> ReasoningStep:
        """Predict relevance of available documents to the query."""
        step_id = str(uuid.uuid4())
        
        key_concepts = query_analysis["key_concepts"]
        query_intent = query_analysis["query_intent"]
        
        document_scores = []
        sources = []
        
        for doc in documents:
            doc_title = doc.get("title", "").lower()
            doc_content = doc.get("content", "").lower()
            doc_url = doc.get("url", "")
            
            # Calculate relevance score
            title_matches = sum(1 for concept in key_concepts if concept in doc_title)
            content_matches = sum(1 for concept in key_concepts if concept in doc_content)
            
            # Weight title matches higher than content matches
            relevance_score = (title_matches * 0.7) + (content_matches * 0.3)
            
            # Normalize by number of key concepts
            if key_concepts:
                relevance_score = relevance_score / len(key_concepts)
            
            # Boost score for intent-specific documents
            intent_boost = 0.0
            if query_intent == "procedural" and any(word in doc_title for word in ["how", "guide", "tutorial"]):
                intent_boost = 0.2
            elif query_intent == "definitional" and any(word in doc_title for word in ["what", "definition", "overview"]):
                intent_boost = 0.2
            
            final_score = min(1.0, relevance_score + intent_boost)
            
            document_scores.append({
                "document": doc,
                "relevance_score": final_score,
                "title_matches": title_matches,
                "content_matches": content_matches,
                "intent_boost": intent_boost
            })
            
            # Create source for audit trail
            if final_score > 0.1:  # Only track relevant documents
                source = KnowledgeSource(
                    source_type=doc.get("source_type", "unknown"),
                    source_id=doc_url,
                    confidence=final_score,
                    timestamp=datetime.now(),
                    metadata={"title": doc.get("title", ""), "matches": title_matches + content_matches}
                )
                sources.append(source)
        
        # Sort by relevance score
        document_scores.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        outputs = {
            "document_scores": document_scores,
            "total_documents_analyzed": len(documents),
            "relevant_documents_found": len([d for d in document_scores if d["relevance_score"] > 0.1])
        }
        
        # Confidence based on how many relevant documents were found
        confidence = min(1.0, len([d for d in document_scores if d["relevance_score"] > 0.3]) / 5.0)
        
        return ReasoningStep(
            step_id=step_id,
            reasoning_type=ReasoningType.PREDICTIVE,
            description="Predicted relevance of available documents to the query",
            inputs={"query": query, "documents_count": len(documents), "query_analysis": query_analysis},
            outputs=outputs,
            confidence=confidence,
            sources=sources,
            timestamp=datetime.now()
        )
    
    def _diagnose_knowledge_gaps(self, query: str, documents: List[Dict[str, Any]], 
                                prediction_results: Dict[str, Any]) -> ReasoningStep:
        """Identify potential knowledge gaps or missing information."""
        step_id = str(uuid.uuid4())
        
        document_scores = prediction_results["document_scores"]
        relevant_docs = prediction_results["relevant_documents_found"]
        
        gaps_identified = []
        
        # Check for insufficient relevant documents
        if relevant_docs < 3:
            gaps_identified.append({
                "gap_type": "insufficient_coverage",
                "description": f"Only {relevant_docs} relevant documents found, may need broader search",
                "severity": "medium"
            })
        
        # Check for low confidence scores
        max_relevance = max([d["relevance_score"] for d in document_scores]) if document_scores else 0.0
        if max_relevance < 0.5:
            gaps_identified.append({
                "gap_type": "low_relevance",
                "description": f"Highest relevance score is {max_relevance:.2f}, documents may not fully address query",
                "severity": "high"
            })
        
        # Check for missing document types
        doc_types = set(doc["document"].get("type", "unknown") for doc in document_scores)
        expected_types = {"guide", "reference", "tutorial", "api_doc"}
        missing_types = expected_types - doc_types
        
        if missing_types:
            gaps_identified.append({
                "gap_type": "missing_document_types",
                "description": f"Missing document types: {', '.join(missing_types)}",
                "severity": "low"
            })
        
        outputs = {
            "knowledge_gaps": gaps_identified,
            "gap_count": len(gaps_identified),
            "coverage_assessment": "good" if relevant_docs >= 3 and max_relevance >= 0.5 else "poor"
        }
        
        # Confidence inversely related to number of gaps
        confidence = max(0.1, 1.0 - (len(gaps_identified) * 0.2))
        
        return ReasoningStep(
            step_id=step_id,
            reasoning_type=ReasoningType.DIAGNOSTIC,
            description="Identified potential knowledge gaps and coverage issues",
            inputs={"query": query, "prediction_results": prediction_results},
            outputs=outputs,
            confidence=confidence,
            sources=[],
            timestamp=datetime.now()
        )
    
    def _generate_recommendations(self, query: str, user_id: str,
                                 prediction_results: Dict[str, Any],
                                 diagnostic_results: Dict[str, Any]) -> ReasoningStep:
        """Generate specific document recommendations with reasoning."""
        step_id = str(uuid.uuid4())
        
        document_scores = prediction_results["document_scores"]
        knowledge_gaps = diagnostic_results["knowledge_gaps"]
        
        recommendations = []
        
        # Get top relevant documents
        top_documents = [d for d in document_scores if d["relevance_score"] > 0.1][:10]
        
        for i, doc_score in enumerate(top_documents):
            doc = doc_score["document"]
            score = doc_score["relevance_score"]
            
            # Generate reasoning for this recommendation
            reasoning_parts = []
            
            if doc_score["title_matches"] > 0:
                reasoning_parts.append(f"Title contains {doc_score['title_matches']} key concepts")
            
            if doc_score["content_matches"] > 0:
                reasoning_parts.append(f"Content matches {doc_score['content_matches']} query terms")
            
            if doc_score["intent_boost"] > 0:
                reasoning_parts.append("Document type aligns with query intent")
            
            recommendation = {
                "document_url": doc.get("url", ""),
                "document_title": doc.get("title", "Unknown"),
                "confidence_score": score,
                "rank": i + 1,
                "reasoning": "; ".join(reasoning_parts) if reasoning_parts else "General relevance match",
                "document_type": doc.get("type", "unknown"),
                "source": doc.get("source_type", "unknown"),
                "freshness": doc.get("last_updated", "unknown")
            }
            
            recommendations.append(recommendation)
        
        # Add memory-based recommendations if available
        if self.memory_layer:
            try:
                memory_recommendations = self.memory_layer.get_document_recommendations(query, user_id)
                for mem_rec in memory_recommendations:
                    mem_rec["rank"] = len(recommendations) + 1
                    mem_rec["reasoning"] = mem_rec.get("reason", "Based on previous successful searches")
                    recommendations.append(mem_rec)
            except Exception as e:
                logger.warning(f"Failed to get memory recommendations: {e}")
        
        outputs = {
            "recommendations": recommendations,
            "recommendation_count": len(recommendations),
            "memory_recommendations_included": bool(self.memory_layer)
        }
        
        # Confidence based on quality of recommendations
        confidence = min(1.0, len(recommendations) / 5.0) if recommendations else 0.1
        
        return ReasoningStep(
            step_id=step_id,
            reasoning_type=ReasoningType.PRESCRIPTIVE,
            description="Generated specific document recommendations with reasoning",
            inputs={"query": query, "user_id": user_id, "prediction_results": prediction_results},
            outputs=outputs,
            confidence=confidence,
            sources=[],
            timestamp=datetime.now()
        )
    
    def _compare_recommendations(self, recommendations: List[Dict[str, Any]]) -> ReasoningStep:
        """Compare and rank recommendations using multiple criteria."""
        step_id = str(uuid.uuid4())
        
        if not recommendations:
            return ReasoningStep(
                step_id=step_id,
                reasoning_type=ReasoningType.COMPARATIVE,
                description="No recommendations to compare",
                inputs={"recommendations": []},
                outputs={"ranked_recommendations": []},
                confidence=0.0,
                sources=[],
                timestamp=datetime.now()
            )
        
        # Multi-criteria ranking
        for rec in recommendations:
            ranking_score = 0.0
            
            # Base confidence score (40% weight)
            ranking_score += rec.get("confidence_score", 0.0) * 0.4
            
            # Document type preference (20% weight)
            doc_type = rec.get("document_type", "unknown")
            type_scores = {"guide": 0.9, "tutorial": 0.8, "reference": 0.7, "api_doc": 0.6}
            ranking_score += type_scores.get(doc_type, 0.3) * 0.2
            
            # Source reliability (20% weight)
            source = rec.get("source", "unknown")
            source_scores = {"confluence": 0.8, "sharepoint": 0.7, "memory": 0.9}
            ranking_score += source_scores.get(source, 0.5) * 0.2
            
            # Freshness (20% weight)
            freshness = rec.get("freshness", "unknown")
            if freshness != "unknown":
                try:
                    # Simple freshness scoring - could be enhanced
                    ranking_score += 0.2  # Assume fresh if we have timestamp
                except:
                    ranking_score += 0.1  # Partial credit for unknown freshness
            
            rec["ranking_score"] = min(1.0, ranking_score)
        
        # Sort by ranking score
        ranked_recommendations = sorted(recommendations, key=lambda x: x["ranking_score"], reverse=True)
        
        # Add final ranks
        for i, rec in enumerate(ranked_recommendations):
            rec["final_rank"] = i + 1
        
        outputs = {
            "ranked_recommendations": ranked_recommendations,
            "ranking_criteria": ["confidence_score", "document_type", "source_reliability", "freshness"],
            "top_recommendation": ranked_recommendations[0] if ranked_recommendations else None
        }
        
        # Confidence based on score distribution
        if len(ranked_recommendations) > 1:
            top_score = ranked_recommendations[0]["ranking_score"]
            second_score = ranked_recommendations[1]["ranking_score"]
            confidence = min(1.0, top_score - second_score + 0.5)  # Higher confidence if clear winner
        else:
            confidence = ranked_recommendations[0]["ranking_score"] if ranked_recommendations else 0.0
        
        return ReasoningStep(
            step_id=step_id,
            reasoning_type=ReasoningType.COMPARATIVE,
            description="Compared and ranked recommendations using multiple criteria",
            inputs={"recommendations": recommendations},
            outputs=outputs,
            confidence=confidence,
            sources=[],
            timestamp=datetime.now()
        )
    
    def _calculate_overall_confidence(self, steps: List[ReasoningStep]) -> float:
        """Calculate overall confidence based on all reasoning steps."""
        if not steps:
            return 0.0
        
        # Weighted average of step confidences
        weights = {
            ReasoningType.ANALYTICAL: 0.15,
            ReasoningType.PREDICTIVE: 0.30,
            ReasoningType.DIAGNOSTIC: 0.15,
            ReasoningType.PRESCRIPTIVE: 0.25,
            ReasoningType.COMPARATIVE: 0.15
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for step in steps:
            weight = weights.get(step.reasoning_type, 0.1)
            weighted_sum += step.confidence * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _generate_reasoning_summary(self, steps: List[ReasoningStep], 
                                   final_confidence: float) -> str:
        """Generate human-readable summary of the reasoning process."""
        if not steps:
            return "No reasoning steps completed."
        
        summary_parts = []
        
        # Add key insights from each step
        for step in steps:
            if step.reasoning_type == ReasoningType.ANALYTICAL:
                concepts = step.outputs.get("key_concepts", [])
                intent = step.outputs.get("query_intent", "general")
                summary_parts.append(f"Identified {len(concepts)} key concepts with {intent} intent")
            
            elif step.reasoning_type == ReasoningType.PREDICTIVE:
                relevant_count = step.outputs.get("relevant_documents_found", 0)
                total_count = step.outputs.get("total_documents_analyzed", 0)
                summary_parts.append(f"Found {relevant_count} relevant documents out of {total_count} analyzed")
            
            elif step.reasoning_type == ReasoningType.PRESCRIPTIVE:
                rec_count = step.outputs.get("recommendation_count", 0)
                summary_parts.append(f"Generated {rec_count} specific recommendations")
        
        # Add confidence assessment
        confidence_level = "very high" if final_confidence > 0.8 else \
                          "high" if final_confidence > 0.6 else \
                          "medium" if final_confidence > 0.4 else \
                          "low"
        
        summary_parts.append(f"Overall confidence: {confidence_level} ({final_confidence:.2f})")
        
        return ". ".join(summary_parts) + "."
    
    def get_reasoning_history(self, user_id: Optional[str] = None, 
                             limit: int = 10) -> List[ReasoningResult]:
        """Get recent reasoning history for audit purposes."""
        history = self.reasoning_history
        
        if user_id:
            history = [r for r in history if r.user_id == user_id]
        
        # Sort by timestamp (most recent first) and limit
        history.sort(key=lambda x: x.timestamp, reverse=True)
        return history[:limit]

