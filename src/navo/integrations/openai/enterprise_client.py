"""
OpenAI Enterprise Client for NAVO
Handles all interactions with OpenAI Enterprise API.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OpenAIMessage:
    """Represents a message in OpenAI chat format."""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None


@dataclass
class OpenAIResponse:
    """Represents a response from OpenAI Enterprise."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float


class OpenAIEnterpriseClient:
    """
    Client for OpenAI Enterprise API integration.
    
    Provides enterprise-grade AI capabilities with unlimited access,
    enhanced security, and advanced features.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI Enterprise client.
        
        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config
        self.api_key = config.get("api_key")
        self.organization_id = config.get("organization_id")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.default_model = config.get("default_model", "gpt-4o")
        self.max_tokens = config.get("max_tokens", 4000)
        self.temperature = config.get("temperature", 0.7)
        self.timeout = config.get("timeout", 60)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Session for connection pooling
        self.session = None
        
        if not self.api_key:
            raise ValueError("OpenAI Enterprise API key is required")
        
        self.logger.info("OpenAI Enterprise client initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "NAVO/2.0.0"
            }
            
            if self.organization_id:
                headers["OpenAI-Organization"] = self.organization_id
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        
        return self.session
    
    async def chat_completion(
        self,
        messages: List[OpenAIMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> OpenAIResponse:
        """
        Create a chat completion using OpenAI Enterprise.
        
        Args:
            messages: List of messages in the conversation
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters
            
        Returns:
            OpenAIResponse with the completion
        """
        start_time = datetime.utcnow()
        
        session = await self._get_session()
        
        # Prepare request payload
        payload = {
            "model": model or self.default_model,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {})
                }
                for msg in messages
            ],
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            **kwargs
        }
        
        try:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
                
                result = await response.json()
                
                # Calculate response time
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Extract response data
                choice = result["choices"][0]
                
                return OpenAIResponse(
                    content=choice["message"]["content"],
                    model=result["model"],
                    usage=result.get("usage", {}),
                    finish_reason=choice.get("finish_reason", "unknown"),
                    response_time=response_time
                )
                
        except Exception as e:
            self.logger.error(f"Error in chat completion: {str(e)}")
            raise
    
    async def generate_embeddings(
        self,
        texts: Union[str, List[str]],
        model: str = "text-embedding-3-large"
    ) -> List[List[float]]:
        """
        Generate embeddings for text(s) using OpenAI Enterprise.
        
        Args:
            texts: Text or list of texts to embed
            model: Embedding model to use
            
        Returns:
            List of embedding vectors
        """
        session = await self._get_session()
        
        # Ensure texts is a list
        if isinstance(texts, str):
            texts = [texts]
        
        payload = {
            "model": model,
            "input": texts
        }
        
        try:
            async with session.post(
                f"{self.base_url}/embeddings",
                json=payload
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
                
                result = await response.json()
                
                # Extract embeddings
                embeddings = [item["embedding"] for item in result["data"]]
                
                return embeddings
                
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    async def analyze_document(
        self,
        document_content: str,
        analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        Analyze a document using OpenAI Enterprise advanced data analysis.
        
        Args:
            document_content: The document content to analyze
            analysis_type: Type of analysis (summary, key_points, entities, etc.)
            
        Returns:
            Dictionary containing analysis results
        """
        system_prompts = {
            "summary": "You are an expert document analyzer. Provide a concise, informative summary of the given document, highlighting the main points and key information.",
            "key_points": "You are an expert document analyzer. Extract the key points and important information from the given document. Present them as a structured list.",
            "entities": "You are an expert document analyzer. Extract and categorize named entities from the document (people, organizations, locations, dates, etc.).",
            "questions": "You are an expert document analyzer. Generate relevant questions that this document answers, along with the answers."
        }
        
        messages = [
            OpenAIMessage(
                role="system",
                content=system_prompts.get(analysis_type, system_prompts["summary"])
            ),
            OpenAIMessage(
                role="user",
                content=f"Please analyze the following document:\n\n{document_content}"
            )
        ]
        
        response = await self.chat_completion(
            messages=messages,
            temperature=0.3  # Lower temperature for more consistent analysis
        )
        
        return {
            "analysis_type": analysis_type,
            "result": response.content,
            "model": response.model,
            "processing_time": response.response_time
        }
    
    async def custom_gpt_query(
        self,
        query: str,
        gpt_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> OpenAIResponse:
        """
        Query a custom GPT created for the organization.
        
        Args:
            query: The query to send to the custom GPT
            gpt_id: ID of the custom GPT
            context: Additional context for the query
            
        Returns:
            OpenAIResponse with the custom GPT's response
        """
        # Note: This is a placeholder for custom GPT functionality
        # The actual implementation would depend on OpenAI's custom GPT API
        
        system_message = "You are NAVO, an enterprise knowledge assistant. You have access to organizational knowledge and should provide helpful, accurate responses."
        
        if context:
            system_message += f"\n\nAdditional context: {json.dumps(context, indent=2)}"
        
        messages = [
            OpenAIMessage(role="system", content=system_message),
            OpenAIMessage(role="user", content=query)
        ]
        
        return await self.chat_completion(messages=messages)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on OpenAI Enterprise connection.
        
        Returns:
            Dictionary containing health status
        """
        try:
            # Simple test request to verify connectivity
            test_messages = [
                OpenAIMessage(role="user", content="Hello, this is a health check.")
            ]
            
            response = await self.chat_completion(
                messages=test_messages,
                max_tokens=10
            )
            
            return {
                "status": "healthy",
                "model": response.model,
                "response_time": response.response_time,
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
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

