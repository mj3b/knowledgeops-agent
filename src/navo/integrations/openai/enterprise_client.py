"""
Enterprise GPT Client for NAVO
Handles all interactions with Enterprise GPT API.
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
class EnterpriseGPTMessage:
    """Represents a message in Enterprise GPT chat format."""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None


@dataclass
class EnterpriseGPTResponse:
    """Represents a response from Enterprise GPT."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float


class EnterpriseGPTClient:
    """
    Client for Enterprise GPT API integration.
    
    Provides enterprise-grade AI capabilities with unlimited access,
    enhanced security, and enterprise-specific optimizations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Enterprise GPT client.
        
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
        
        if not self.api_key:
            raise ValueError("Enterprise GPT API key is required")
        
        if not self.organization_id:
            raise ValueError("Enterprise Organization ID is required")
        
        # Headers for Enterprise GPT API
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Organization": self.organization_id,
            "Content-Type": "application/json",
            "User-Agent": "NAVO-Enterprise/2.0.0"
        }
        
        logger.info("Enterprise GPT client initialized")
    
    async def generate_response(
        self,
        messages: List[EnterpriseGPTMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> EnterpriseGPTResponse:
        """
        Generate response using Enterprise GPT.
        
        Args:
            messages: List of messages for the conversation
            model: Model to use (defaults to configured model)
            max_tokens: Maximum tokens in response
            temperature: Response creativity (0.0-1.0)
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        start_time = datetime.now()
        
        try:
            # Prepare request payload
            payload = {
                "model": model or self.default_model,
                "messages": [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ],
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "stream": stream,
                **kwargs
            }
            
            logger.info(f"Generating response with Enterprise GPT model: {payload['model']}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Enterprise GPT API error {response.status}: {error_text}")
                    
                    result = await response.json()
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Extract response data
            choice = result["choices"][0]
            content = choice["message"]["content"]
            
            # Create response object
            gpt_response = EnterpriseGPTResponse(
                content=content,
                model=result["model"],
                usage=result["usage"],
                finish_reason=choice["finish_reason"],
                response_time=response_time
            )
            
            logger.info(f"Enterprise GPT response generated successfully. "
                       f"Tokens: {result['usage']['total_tokens']}, "
                       f"Time: {response_time:.2f}s")
            
            return gpt_response
            
        except Exception as e:
            logger.error(f"Error generating response with Enterprise GPT: {str(e)}")
            raise
    
    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-ada-002"
    ) -> List[List[float]]:
        """
        Generate embeddings using Enterprise GPT.
        
        Args:
            texts: List of texts to embed
            model: Embedding model to use
            
        Returns:
            List of embedding vectors
        """
        try:
            payload = {
                "model": model,
                "input": texts
            }
            
            logger.info(f"Generating embeddings for {len(texts)} texts")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/embeddings",
                    headers=self.headers,
                    json=payload
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Enterprise GPT embeddings error {response.status}: {error_text}")
                    
                    result = await response.json()
            
            embeddings = [item["embedding"] for item in result["data"]]
            
            logger.info(f"Generated {len(embeddings)} embeddings successfully")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Enterprise GPT service health.
        
        Returns:
            Health status information
        """
        try:
            # Simple test query
            test_messages = [
                EnterpriseGPTMessage(
                    role="system",
                    content="You are NAVO, an enterprise knowledge assistant."
                ),
                EnterpriseGPTMessage(
                    role="user", 
                    content="Test connectivity"
                )
            ]
            
            response = await self.generate_response(
                messages=test_messages,
                max_tokens=10
            )
            
            return {
                "status": "healthy",
                "service": "Enterprise GPT",
                "model": self.default_model,
                "organization": self.organization_id,
                "response_time": f"{response.response_time:.2f}s",
                "test_successful": True
            }
            
        except Exception as e:
            logger.error(f"Enterprise GPT health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "service": "Enterprise GPT",
                "error": str(e),
                "test_successful": False
            }
    
    def get_client_info(self) -> Dict[str, Any]:
        """
        Get Enterprise GPT client information.
        
        Returns:
            Client configuration information
        """
        return {
            "service": "Enterprise GPT",
            "model": self.default_model,
            "organization": self.organization_id,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "version": "2.0.0"
        }
    
    async def close(self):
        """Close the client and cleanup resources."""
        logger.info("Enterprise GPT client closed")

