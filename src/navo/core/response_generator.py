"""
NAVO Response Generator
Generates intelligent responses using OpenAI Enterprise.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from ..integrations.openai.enterprise_client import OpenAIEnterpriseClient, OpenAIMessage

logger = logging.getLogger(__name__)


@dataclass
class GeneratedResponse:
    """Represents a generated response from NAVO."""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    reasoning: Optional[str] = None
    follow_up_questions: Optional[List[str]] = None


class ResponseGenerator:
    """
    Generates intelligent, context-aware responses using OpenAI Enterprise
    and retrieved knowledge sources.
    """
    
    def __init__(self, openai_client: OpenAIEnterpriseClient, config: Dict[str, Any]):
        """
        Initialize the response generator.
        
        Args:
            openai_client: OpenAI Enterprise client instance
            config: Configuration dictionary
        """
        self.openai_client = openai_client
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Response generation settings
        self.max_context_length = config.get("max_context_length", 8000)
        self.include_sources = config.get("include_sources", True)
        self.generate_follow_ups = config.get("generate_follow_ups", True)
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        
        self.logger.info("Response generator initialized")
    
    async def generate_response(
        self, 
        processed_query, 
        relevant_docs: List[Dict[str, Any]]
    ) -> GeneratedResponse:
        """
        Generate an intelligent response based on the query and relevant documents.
        
        Args:
            processed_query: ProcessedQuery object with query analysis
            relevant_docs: List of relevant documents from knowledge sources
            
        Returns:
            GeneratedResponse with the answer and metadata
        """
        self.logger.info(f"Generating response for intent: {processed_query.intent.value}")
        
        try:
            # Build context from relevant documents
            context = self._build_context(relevant_docs)
            
            # Create system prompt based on query intent
            system_prompt = self._create_system_prompt(processed_query)
            
            # Create user prompt with context
            user_prompt = self._create_user_prompt(processed_query, context)
            
            # Generate response using OpenAI Enterprise
            messages = [
                OpenAIMessage(role="system", content=system_prompt),
                OpenAIMessage(role="user", content=user_prompt)
            ]
            
            openai_response = await self.openai_client.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=self.config.get("max_response_tokens", 1000)
            )
            
            # Parse and structure the response
            structured_response = self._structure_response(
                openai_response.content, 
                relevant_docs,
                processed_query
            )
            
            # Generate follow-up questions if enabled
            follow_ups = None
            if self.generate_follow_ups:
                follow_ups = await self._generate_follow_up_questions(
                    processed_query, structured_response["answer"]
                )
            
            # Calculate confidence score
            confidence = self._calculate_response_confidence(
                processed_query, relevant_docs, openai_response
            )
            
            return GeneratedResponse(
                answer=structured_response["answer"],
                sources=self._format_sources(relevant_docs),
                confidence=confidence,
                reasoning=structured_response.get("reasoning"),
                follow_up_questions=follow_ups
            )
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            
            # Return fallback response
            return GeneratedResponse(
                answer="I apologize, but I encountered an error while generating a response. Please try rephrasing your question or contact support.",
                sources=[],
                confidence=0.0
            )
    
    def _build_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """
        Build context string from relevant documents.
        
        Args:
            relevant_docs: List of relevant documents
            
        Returns:
            Formatted context string
        """
        if not relevant_docs:
            return "No specific documents found. Please provide a general response based on your knowledge."
        
        context_parts = []
        total_length = 0
        
        for i, doc in enumerate(relevant_docs):
            # Format document information
            doc_info = f"Document {i+1}:\n"
            doc_info += f"Title: {doc.get('title', 'Unknown')}\n"
            doc_info += f"Source: {doc.get('source', 'Unknown')}\n"
            
            if doc.get('url'):
                doc_info += f"URL: {doc['url']}\n"
            
            content = doc.get('content', doc.get('summary', ''))
            if content:
                # Truncate content if too long
                max_content_length = 1000
                if len(content) > max_content_length:
                    content = content[:max_content_length] + "..."
                
                doc_info += f"Content: {content}\n"
            
            doc_info += "\n"
            
            # Check if adding this document would exceed context length
            if total_length + len(doc_info) > self.max_context_length:
                break
            
            context_parts.append(doc_info)
            total_length += len(doc_info)
        
        return "\n".join(context_parts)
    
    def _create_system_prompt(self, processed_query) -> str:
        """
        Create system prompt based on query intent.
        
        Args:
            processed_query: ProcessedQuery object
            
        Returns:
            System prompt string
        """
        base_prompt = """You are NAVO, an enterprise knowledge assistant. Your tagline is "NAVO knows where it's written."

You help users find and understand information from their organization's knowledge base. You have access to documents from various sources including Confluence, SharePoint, and other enterprise systems.

Guidelines:
1. Provide accurate, helpful responses based on the provided context
2. If you don't have enough information, say so clearly
3. Always cite your sources when possible
4. Be concise but comprehensive
5. Use a professional but friendly tone
6. If asked about procedures, provide step-by-step instructions
7. For technical questions, include relevant details and examples"""
        
        # Add intent-specific instructions
        intent_prompts = {
            "search": "\n\nThe user is looking for specific information. Help them find what they need and suggest related resources.",
            "question": "\n\nThe user has a specific question. Provide a direct, informative answer.",
            "summary": "\n\nThe user wants a summary. Provide a concise overview of the key points.",
            "comparison": "\n\nThe user wants to compare options. Present a clear comparison with pros and cons.",
            "procedure": "\n\nThe user needs step-by-step instructions. Provide a clear, actionable procedure.",
            "troubleshooting": "\n\nThe user has a problem to solve. Provide diagnostic steps and solutions.",
            "definition": "\n\nThe user wants to understand a concept. Provide a clear definition with context."
        }
        
        intent_addition = intent_prompts.get(processed_query.intent.value, "")
        
        return base_prompt + intent_addition
    
    def _create_user_prompt(self, processed_query, context: str) -> str:
        """
        Create user prompt with query and context.
        
        Args:
            processed_query: ProcessedQuery object
            context: Context string from relevant documents
            
        Returns:
            User prompt string
        """
        prompt = f"User Query: {processed_query.original_text}\n\n"
        
        # Add extracted entities if any
        if processed_query.entities:
            entities_text = ", ".join([f"{e.text} ({e.type})" for e in processed_query.entities])
            prompt += f"Detected Entities: {entities_text}\n\n"
        
        # Add context
        prompt += f"Relevant Information:\n{context}\n\n"
        
        # Add specific instructions based on intent
        if processed_query.intent.value == "procedure":
            prompt += "Please provide step-by-step instructions."
        elif processed_query.intent.value == "troubleshooting":
            prompt += "Please provide troubleshooting steps and potential solutions."
        elif processed_query.intent.value == "comparison":
            prompt += "Please provide a clear comparison with advantages and disadvantages."
        
        return prompt
    
    def _structure_response(
        self, 
        raw_response: str, 
        relevant_docs: List[Dict[str, Any]],
        processed_query
    ) -> Dict[str, str]:
        """
        Structure the raw response from OpenAI.
        
        Args:
            raw_response: Raw response from OpenAI
            relevant_docs: Relevant documents used
            processed_query: ProcessedQuery object
            
        Returns:
            Structured response dictionary
        """
        # For now, return the response as-is
        # In the future, we could parse structured responses
        return {
            "answer": raw_response.strip(),
            "reasoning": None  # Could be extracted if OpenAI provides reasoning
        }
    
    def _format_sources(self, relevant_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format source documents for the response.
        
        Args:
            relevant_docs: List of relevant documents
            
        Returns:
            Formatted sources list
        """
        if not self.include_sources:
            return []
        
        sources = []
        for doc in relevant_docs:
            source = {
                "title": doc.get("title", "Unknown Document"),
                "source": doc.get("source", "Unknown Source"),
                "relevance_score": doc.get("relevance_score", 0.0)
            }
            
            if doc.get("url"):
                source["url"] = doc["url"]
            
            if doc.get("last_modified"):
                source["last_modified"] = doc["last_modified"]
            
            sources.append(source)
        
        return sources
    
    async def _generate_follow_up_questions(
        self, 
        processed_query, 
        answer: str
    ) -> List[str]:
        """
        Generate relevant follow-up questions.
        
        Args:
            processed_query: ProcessedQuery object
            answer: Generated answer
            
        Returns:
            List of follow-up questions
        """
        try:
            prompt = f"""Based on this query and answer, suggest 3 relevant follow-up questions that the user might want to ask:

Original Query: {processed_query.original_text}
Answer: {answer[:500]}...

Generate 3 concise, relevant follow-up questions:"""

            messages = [
                OpenAIMessage(
                    role="system", 
                    content="You are a helpful assistant that generates relevant follow-up questions. Keep questions concise and directly related to the topic."
                ),
                OpenAIMessage(role="user", content=prompt)
            ]
            
            response = await self.openai_client.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=200
            )
            
            # Parse follow-up questions
            questions = []
            for line in response.content.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                    # Clean up the question
                    question = line.lstrip('-123. ').strip()
                    if question and question.endswith('?'):
                        questions.append(question)
            
            return questions[:3]  # Limit to 3 questions
            
        except Exception as e:
            self.logger.warning(f"Error generating follow-up questions: {str(e)}")
            return []
    
    def _calculate_response_confidence(
        self, 
        processed_query, 
        relevant_docs: List[Dict[str, Any]], 
        openai_response
    ) -> float:
        """
        Calculate confidence score for the generated response.
        
        Args:
            processed_query: ProcessedQuery object
            relevant_docs: Relevant documents used
            openai_response: OpenAI response object
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.0
        
        # Base confidence from query processing
        confidence += 0.3 * processed_query.confidence
        
        # Confidence from document relevance
        if relevant_docs:
            avg_relevance = sum(doc.get("relevance_score", 0) for doc in relevant_docs) / len(relevant_docs)
            confidence += 0.4 * avg_relevance
        else:
            confidence += 0.1  # Lower confidence without sources
        
        # Confidence from response quality indicators
        response_length = len(openai_response.content)
        if response_length > 50:  # Reasonable response length
            confidence += 0.2
        
        # Check if response indicates uncertainty
        uncertainty_phrases = [
            "i don't know", "i'm not sure", "i don't have", 
            "unclear", "uncertain", "might be", "possibly"
        ]
        
        if any(phrase in openai_response.content.lower() for phrase in uncertainty_phrases):
            confidence *= 0.7  # Reduce confidence for uncertain responses
        
        # Bonus for citing sources
        if relevant_docs and "document" in openai_response.content.lower():
            confidence += 0.1
        
        return min(confidence, 1.0)

