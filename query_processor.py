"""
Query Processor
Handles natural language queries and coordinates with knowledge sources
using Enterprise GPT for Microsoft Teams integration
"""

import os
import logging
import time
from typing import Dict, List, Any
import asyncio
from openai import AsyncOpenAI

from confluence_client import ConfluenceClient
from sharepoint_client import SharePointClient
from local_docs_client import LocalDocsClient

logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Processes user queries and retrieves relevant information from
    configurable knowledge sources using Enterprise GPT. Sources include
    Confluence, SharePoint, and optional local documentation.
    """
    
    def __init__(self):
        # Initialize Enterprise GPT client
        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE")
        
        if not api_key:
            logger.error("OPENAI_API_KEY not configured")
            raise ValueError("OPENAI_API_KEY is required")
        
        self.openai_client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_base if api_base else None
        )
        
        # Initialize knowledge source clients
        self.confluence = ConfluenceClient()
        self.sharepoint = SharePointClient()
        self.local_docs = LocalDocsClient()

        # Store in a list for easier extensibility
        self.sources = [
            self.confluence,
            self.sharepoint,
            self.local_docs,
        ]
        
        logger.info("Query processor initialized with Enterprise GPT")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query and return structured response
        
        Args:
            query: User's natural language query
            
        Returns:
            Dict containing answer, sources, confidence, and processing time
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {query}")
            
            # Search all configured knowledge sources concurrently
            search_tasks = [
                source.search(query)
                for source in self.sources
                if getattr(source, "enabled", False)
            ]
            
            if not search_tasks:
                return {
                    "answer": (
                        "No knowledge sources are configured. Please check your "
                        "Confluence, SharePoint, or local documentation settings."
                    ),
                    "sources": [],
                    "confidence": 0.0,
                    "processing_time": time.time() - start_time,
                }
            
            # Execute searches concurrently
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results and handle exceptions
            all_results = []
            for result in search_results:
                if isinstance(result, Exception):
                    logger.warning(f"Search failed: {result}")
                elif isinstance(result, list):
                    all_results.extend(result)
            
            if not all_results:
                return {
                    "answer": (
                        "I couldn't find any relevant documentation for your query. "
                        "Try rephrasing or verify that the documents exist in "
                        "Confluence, SharePoint, or the local docs folder."
                    ),
                    "sources": [],
                    "confidence": 0.0,
                    "processing_time": time.time() - start_time
                }
            
            # Generate AI response using Enterprise GPT
            ai_response = await self._generate_ai_response(query, all_results)
            
            processing_time = time.time() - start_time
            
            return {
                "answer": ai_response["answer"],
                "sources": self._format_sources(all_results[:3]),  # Top 3 sources
                "confidence": ai_response["confidence"],
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": "I encountered an error while processing your query. Please try again or contact support if the issue persists.",
                "sources": [],
                "confidence": 0.0,
                "processing_time": time.time() - start_time
            }
    
    async def _generate_ai_response(self, query: str, search_results: List[Dict]) -> Dict[str, Any]:
        """
        Generate AI response using Enterprise GPT
        
        Args:
            query: User's original query
            search_results: Search results from knowledge sources
            
        Returns:
            Dict containing AI-generated answer and confidence score
        """
        try:
            # Prepare context from search results
            context = self._prepare_context(search_results)
            
            # Create prompt for Enterprise GPT
            system_prompt = (
                "You are NAVO, an engineering knowledge assistant. "
                "Use only the provided snippets from Confluence, SharePoint, or local files. "
                "Keep answers concise and reference document titles when relevant. "
                "If the answer is not present in the snippets, politely say so."
            )

            user_prompt = (
                f"Question: {query}\n\n"
                f"Snippets:\n{context}\n\n"
                "Reply in 2-4 sentences. Include a short numbered list of steps if it helps clarify the answer."
            )

            # Call Enterprise GPT
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Calculate confidence based on context quality and result count
            base_confidence = 0.6
            result_bonus = min(0.3, len(search_results) * 0.1)
            context_bonus = min(0.1, len(context) / 2000)  # Bonus for richer context
            
            confidence = min(0.95, base_confidence + result_bonus + context_bonus)
            
            return {
                "answer": answer,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return {
                "answer": "I found some relevant documentation but couldn't generate a complete response. Please check the source links below for more information.",
                "confidence": 0.4
            }
    
    def _prepare_context(self, search_results: List[Dict]) -> str:
        """
        Prepare context string from search results for AI processing
        
        Args:
            search_results: List of search results from knowledge sources
            
        Returns:
            Formatted context string for AI prompt
        """
        context_parts = []
        
        for i, result in enumerate(search_results[:5], 1):  # Top 5 results
            title = result.get("title", "Untitled Document")
            content = result.get("content", "")
            source = result.get("source", "Unknown")
            
            # Limit content length to prevent token overflow
            if len(content) > 800:
                content = content[:800] + "..."
            
            context_part = f"""
Document {i}: {title} (Source: {source})
Content: {content}
---"""
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _format_sources(self, search_results: List[Dict]) -> List[Dict]:
        """
        Format sources for adaptive card display

        Args:
            search_results: Raw search results from knowledge sources

        Returns:
            Formatted sources for Teams adaptive cards. Each entry includes
            ``days_old`` representing how many days ago the document was last
            modified.
        """
        sources = []
        
        for result in search_results:
            # Extract and format source information
            title = result.get("title", "Untitled Document")
            url = result.get("url", "")
            source_type = result.get("source", "Document")
            last_modified = result.get("last_modified", "Unknown")
            content = result.get("content", "")
            
            # Create excerpt for preview
            excerpt = ""
            if content:
                # Clean and truncate content for excerpt
                clean_content = content.replace("\n", " ").strip()
                if len(clean_content) > 150:
                    excerpt = clean_content[:150] + "..."
                else:
                    excerpt = clean_content
            
            # Format last modified date
            formatted_date = self._format_date(last_modified)

            # Calculate how many days old the document is
            days_old = None
            if last_modified and last_modified != "Unknown":
                from datetime import datetime, timezone
                try:
                    if "T" in last_modified:
                        dt = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
                    else:
                        dt = datetime.fromisoformat(last_modified)
                    delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
                    days_old = max(delta.days, 0)
                except Exception:
                    days_old = None
            
            source_info = {
                "title": title,
                "url": url,
                "source_type": source_type,
                "last_updated": formatted_date,
                "excerpt": excerpt or "No preview available",
                "days_old": days_old,
            }
            
            sources.append(source_info)
        
        return sources
    
    def _format_date(self, date_string: str) -> str:
        """
        Format date string for display
        
        Args:
            date_string: Raw date string from API
            
        Returns:
            Human-readable date string
        """
        if not date_string or date_string == "Unknown":
            return "Recently updated"
        
        try:
            # Handle different date formats from APIs
            from datetime import datetime
            
            # Try common ISO format first
            if "T" in date_string:
                dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
                days_ago = (datetime.now() - dt.replace(tzinfo=None)).days
                
                if days_ago == 0:
                    return "Today"
                elif days_ago == 1:
                    return "Yesterday"
                elif days_ago < 7:
                    return f"{days_ago} days ago"
                elif days_ago < 30:
                    weeks = days_ago // 7
                    return f"{weeks} week{'s' if weeks > 1 else ''} ago"
                else:
                    months = days_ago // 30
                    return f"{months} month{'s' if months > 1 else ''} ago"
            
            return date_string
            
        except Exception:
            return "Recently updated"

