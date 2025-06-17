"""
NAVO Microsoft Teams Integration
Enterprise-grade adaptive card integration for knowledge discovery
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class CardType(Enum):
    """Types of adaptive cards supported by NAVO"""
    SEARCH_RESPONSE = "search_response"
    ERROR_RESPONSE = "error_response"
    FEEDBACK_REQUEST = "feedback_request"
    KNOWLEDGE_SUMMARY = "knowledge_summary"


@dataclass
class DocumentMetadata:
    """Document metadata for Teams card display"""
    page: str
    document: str
    last_modified: str
    confidence: float
    source: str
    url: str


@dataclass
class SearchResponse:
    """Search response data structure"""
    query: str
    summary: str
    metadata: DocumentMetadata
    query_id: str
    timestamp: datetime


class TeamsCardBuilder:
    """Builder class for Microsoft Teams adaptive cards"""
    
    def __init__(self, base_url: str = "https://navo.company.com"):
        self.base_url = base_url
        self.card_version = "1.4"
    
    def create_search_response_card(self, response: SearchResponse) -> Dict[str, Any]:
        """Create adaptive card for search response"""
        return {
            "type": "AdaptiveCard",
            "version": self.card_version,
            "body": [
                self._create_header(),
                self._create_query_section(response.query),
                self._create_summary_section(response.summary),
                self._create_metadata_section(response.metadata)
            ],
            "actions": [
                self._create_view_document_action(response.metadata.url),
                self._create_feedback_action(response.query_id)
            ]
        }
    
    def create_error_response_card(self, error_message: str, query: str = None) -> Dict[str, Any]:
        """Create adaptive card for error responses"""
        return {
            "type": "AdaptiveCard",
            "version": self.card_version,
            "body": [
                self._create_header(),
                {
                    "type": "Container",
                    "style": "attention",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "Error",
                            "weight": "Bolder",
                            "size": "Medium",
                            "color": "Attention"
                        },
                        {
                            "type": "TextBlock",
                            "text": error_message,
                            "wrap": True,
                            "spacing": "Small"
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "Get Help",
                    "url": f"{self.base_url}/help"
                }
            ] if query else []
        }
    
    def create_knowledge_summary_card(self, 
                                    title: str, 
                                    summary: str, 
                                    documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Create adaptive card for knowledge summaries"""
        return {
            "type": "AdaptiveCard",
            "version": self.card_version,
            "body": [
                self._create_header(),
                {
                    "type": "TextBlock",
                    "text": title,
                    "weight": "Bolder",
                    "size": "Large"
                },
                {
                    "type": "TextBlock",
                    "text": summary,
                    "wrap": True,
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": f"Based on {len(documents)} documents",
                    "size": "Small",
                    "color": "Accent",
                    "spacing": "Small"
                }
            ],
            "actions": [
                {
                    "type": "Action.ShowCard",
                    "title": "View Sources",
                    "card": self._create_sources_card(documents)
                }
            ]
        }
    
    def _create_header(self) -> Dict[str, Any]:
        """Create card header with NAVO branding"""
        return {
            "type": "Container",
            "items": [
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": "auto",
                            "items": [
                                {
                                    "type": "Image",
                                    "url": f"{self.base_url}/static/navo-logo.png",
                                    "size": "Small",
                                    "style": "Person"
                                }
                            ]
                        },
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "NAVO Knowledge Discovery",
                                    "weight": "Bolder",
                                    "size": "Medium"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": "AI ASSISTANT",
                                    "spacing": "None",
                                    "color": "Accent",
                                    "size": "Small"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    def _create_query_section(self, query: str) -> Dict[str, Any]:
        """Create query display section"""
        return {
            "type": "Container",
            "style": "emphasis",
            "items": [
                {
                    "type": "TextBlock",
                    "text": f'"{query}"',
                    "wrap": True,
                    "size": "Medium",
                    "spacing": "Medium"
                }
            ]
        }
    
    def _create_summary_section(self, summary: str) -> Dict[str, Any]:
        """Create summary section"""
        return {
            "type": "Container",
            "items": [
                {
                    "type": "TextBlock",
                    "text": "Summary",
                    "weight": "Bolder",
                    "size": "Medium",
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": summary,
                    "wrap": True,
                    "spacing": "Small"
                }
            ]
        }
    
    def _create_metadata_section(self, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Create metadata facts section"""
        return {
            "type": "FactSet",
            "facts": [
                {
                    "title": "Page",
                    "value": metadata.page
                },
                {
                    "title": "Document",
                    "value": metadata.document
                },
                {
                    "title": "Last Modified",
                    "value": metadata.last_modified
                },
                {
                    "title": "Confidence",
                    "value": f"{metadata.confidence:.0%} Match"
                },
                {
                    "title": "Source",
                    "value": metadata.source.title()
                }
            ],
            "spacing": "Medium"
        }
    
    def _create_view_document_action(self, url: str) -> Dict[str, Any]:
        """Create view document action button"""
        return {
            "type": "Action.OpenUrl",
            "title": "View Document",
            "url": url
        }
    
    def _create_feedback_action(self, query_id: str) -> Dict[str, Any]:
        """Create feedback action button"""
        return {
            "type": "Action.Submit",
            "title": "Provide Feedback",
            "data": {
                "action": "feedback",
                "query_id": query_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _create_sources_card(self, documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Create sources detail card"""
        source_items = []
        for i, doc in enumerate(documents[:5]):  # Limit to 5 sources
            source_items.extend([
                {
                    "type": "TextBlock",
                    "text": f"{i+1}. {doc.document}",
                    "weight": "Bolder",
                    "size": "Small"
                },
                {
                    "type": "TextBlock",
                    "text": f"Source: {doc.source.title()} | Modified: {doc.last_modified}",
                    "size": "Small",
                    "color": "Accent",
                    "spacing": "None"
                },
                {
                    "type": "TextBlock",
                    "text": f"Confidence: {doc.confidence:.0%}",
                    "size": "Small",
                    "spacing": "None"
                }
            ])
            if i < len(documents) - 1:
                source_items.append({"type": "TextBlock", "text": "", "spacing": "Small"})
        
        return {
            "type": "AdaptiveCard",
            "version": self.card_version,
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Source Documents",
                    "weight": "Bolder",
                    "size": "Medium"
                }
            ] + source_items
        }


class TeamsWebhookClient:
    """Client for sending messages to Microsoft Teams via webhooks"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_card(self, card: Dict[str, Any]) -> bool:
        """Send adaptive card to Teams channel"""
        try:
            message = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": card
                    }
                ]
            }
            
            async with self.session.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info("Successfully sent card to Teams")
                    return True
                else:
                    logger.error(f"Failed to send card to Teams: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending card to Teams: {str(e)}")
            return False


class TeamsBotFramework:
    """Microsoft Bot Framework integration for NAVO"""
    
    def __init__(self, app_id: str, app_password: str):
        self.app_id = app_id
        self.app_password = app_password
        self.card_builder = TeamsCardBuilder()
    
    async def handle_message(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message from Teams"""
        try:
            message_text = activity.get("text", "").strip()
            user_id = activity.get("from", {}).get("id")
            conversation_id = activity.get("conversation", {}).get("id")
            
            # Log the interaction
            logger.info(
                "teams_message_received",
                user_id=user_id,
                conversation_id=conversation_id,
                message=message_text
            )
            
            # Process the query
            if message_text.lower().startswith("@navo") or "navo" in message_text.lower():
                query = self._extract_query(message_text)
                response = await self._process_query(query, user_id)
                
                if response:
                    card = self.card_builder.create_search_response_card(response)
                else:
                    card = self.card_builder.create_error_response_card(
                        "I couldn't find relevant information for your query. Please try rephrasing your question.",
                        query
                    )
                
                return self._create_card_response(card)
            
            # Handle feedback submissions
            elif activity.get("value", {}).get("action") == "feedback":
                return await self._handle_feedback(activity)
            
            # Default response for unrecognized input
            else:
                return self._create_text_response(
                    "Hi! I'm NAVO, your knowledge discovery assistant. "
                    "Ask me questions about documentation, processes, or technical information."
                )
                
        except Exception as e:
            logger.error(f"Error handling Teams message: {str(e)}")
            error_card = self.card_builder.create_error_response_card(
                "I encountered an error processing your request. Please try again later."
            )
            return self._create_card_response(error_card)
    
    def _extract_query(self, message_text: str) -> str:
        """Extract query from Teams message"""
        # Remove @mentions and clean up the query
        query = message_text.replace("@navo", "").replace("navo", "").strip()
        return query if query else message_text
    
    async def _process_query(self, query: str, user_id: str) -> Optional[SearchResponse]:
        """Process user query and return search response"""
        try:
            # This would integrate with your existing search engine
            from ..core.navo_engine import NAVOEngine
            
            engine = NAVOEngine()
            search_results = await engine.search(query, user_context={"user_id": user_id})
            
            if search_results and search_results.documents:
                best_result = search_results.documents[0]
                
                metadata = DocumentMetadata(
                    page=best_result.metadata.get("page", "Unknown"),
                    document=best_result.title,
                    last_modified=best_result.last_modified.strftime("%B %d, %Y"),
                    confidence=best_result.confidence,
                    source=best_result.source,
                    url=best_result.url
                )
                
                return SearchResponse(
                    query=query,
                    summary=best_result.summary or best_result.content[:500] + "...",
                    metadata=metadata,
                    query_id=search_results.query_id,
                    timestamp=datetime.utcnow()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return None
    
    async def _handle_feedback(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle feedback submission"""
        try:
            feedback_data = activity.get("value", {})
            query_id = feedback_data.get("query_id")
            
            # Store feedback (implement your feedback storage logic)
            logger.info(
                "feedback_received",
                query_id=query_id,
                user_id=activity.get("from", {}).get("id"),
                timestamp=feedback_data.get("timestamp")
            )
            
            return self._create_text_response(
                "Thank you for your feedback! It helps me improve my responses."
            )
            
        except Exception as e:
            logger.error(f"Error handling feedback: {str(e)}")
            return self._create_text_response(
                "Thank you for your feedback!"
            )
    
    def _create_card_response(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """Create Bot Framework response with adaptive card"""
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": card
                }
            ]
        }
    
    def _create_text_response(self, text: str) -> Dict[str, Any]:
        """Create simple text response"""
        return {
            "type": "message",
            "text": text
        }


# Example usage and testing
async def example_usage():
    """Example of how to use the Teams integration"""
    
    # Create card builder
    card_builder = TeamsCardBuilder()
    
    # Sample search response
    metadata = DocumentMetadata(
        page="Automation Standards",
        document="Project Automation Guide",
        last_modified="March 15, 2024",
        confidence=0.94,
        source="confluence",
        url="https://confluence.company.com/pages/123456"
    )
    
    response = SearchResponse(
        query="What is the retry logic for project automation?",
        summary="The retry logic for project automation is based on exponential backoff. Specifically, the process retries failed operations with increasing delays: 1s, 2s, 4s, 8s up to a maximum of 5 attempts before marking as failed.",
        metadata=metadata,
        query_id="uuid-12345",
        timestamp=datetime.utcnow()
    )
    
    # Create adaptive card
    card = card_builder.create_search_response_card(response)
    
    # Send to Teams (example)
    webhook_url = "https://outlook.office.com/webhook/your-webhook-url"
    async with TeamsWebhookClient(webhook_url) as client:
        success = await client.send_card(card)
        print(f"Card sent successfully: {success}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

