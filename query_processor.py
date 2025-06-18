"""
Query Processor
Handles natural language queries and coordinates with knowledge sources
"""

import os
import logging
from typing import Dict, List, Any
import asyncio
from openai import AsyncOpenAI

from confluence_client import ConfluenceClient
from sharepoint_client import SharePointClient

logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Processes user queries and retrieves relevant information
    from Confluence and SharePoint using Enterprise GPT
    """
    
    def __init__(self):
        # Initialize Enterprise GPT client
        self.openai_client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE")
        )
        
        # Initialize knowledge source clients
        self.confluence = ConfluenceClient()
        self.sharepoint = SharePointClient()
        
        logger.info("Query processor initialized")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query and return structured response
        """
        try:
            # Search both knowledge sources concurrently
            confluence_task = self.confluence.search(query)
            sharepoint_task = self.sharepoint.search(query)
            
            confluence_results, sharepoint_results = await asyncio.gather(
                confluence_task, sharepoint_task, return_exceptions=True
            )
            
            # Handle search exceptions
            if isinstance(confluence_results, Exception):
                logger.warning(f"Confluence search failed: {confluence_results}")
                confluence_results = []
            
            if isinstance(sharepoint_results, Exception):
                logger.warning(f"SharePoint search failed: {sharepoint_results}")
                sharepoint_results = []
            
            # Combine and rank results
            all_results = confluence_results + sharepoint_results
            
            if not all_results:
                return {
                    "answer": "I couldn't find any relevant documentation for your query. Please try rephrasing your question or check if the documents exist in Confluence or SharePoint.",
                    "sources": [],
                    "confidence": 0.0
                }
            
            # Generate AI response using Enterprise GPT
            ai_response = await self._generate_ai_response(query, all_results)
            
            return {
                "answer": ai_response["answer"],
                "sources": self._format_sources(all_results[:3]),  # Top 3 sources
                "confidence": ai_response["confidence"]
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": "I encountered an error while processing your query. Please try again.",
                "sources": [],
                "confidence": 0.0
            }
    
    async def _generate_ai_response(self, query: str, search_results: List[Dict]) -> Dict[str, Any]:
        """
        Generate AI response using Enterprise GPT
        """
        try:
            # Prepare context from search results
            context = self._prepare_context(search_results)
            
            # Create prompt for Enterprise GPT
            prompt = f"""
You are NAVO, a knowledge discovery assistant. Answer the user's question based on the provided documentation context.

User Question: {query}

Documentation Context:
{context}

Instructions:
- Provide a clear, concise answer based on the documentation
- If the information is incomplete, say so
- Include specific details when available
- Be helpful and professional

Answer:"""

            # Call Enterprise GPT
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are NAVO, a helpful knowledge discovery assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Calculate confidence based on context quality
            confidence = min(0.9, len(search_results) * 0.2 + 0.3)
            
            return {
                "answer": answer,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return {
                "answer": "I found some relevant documentation but couldn't generate a complete response. Please check the source links below.",
                "confidence": 0.5
            }
    
    def _prepare_context(self, search_results: List[Dict]) -> str:
        """
        Prepare context string from search results
        """
        context_parts = []
        
        for i, result in enumerate(search_results[:5], 1):  # Top 5 results
            title = result.get("title", "Untitled")
            content = result.get("content", "")[:500]  # Limit content length
            source = result.get("source", "Unknown")
            
            context_parts.append(f"{i}. {title} ({source})\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _format_sources(self, search_results: List[Dict]) -> List[Dict]:
        """
        Format sources for response card
        """
        sources = []
        
        for result in search_results:
            sources.append({
                "title": result.get("title", "Untitled"),
                "url": result.get("url", ""),
                "source": result.get("source", "Unknown"),
                "last_modified": result.get("last_modified", "Unknown"),
                "excerpt": result.get("content", "")[:150] + "..." if result.get("content") else ""
            })
        
        return sources

