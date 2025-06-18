"""
NAVO Teams Bot
Handles Microsoft Teams conversations and routes queries to knowledge sources
"""

import logging
from typing import Dict, Any
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes

from query_processor import QueryProcessor
from adaptive_cards import create_response_card

logger = logging.getLogger(__name__)


class NAVOBot(ActivityHandler):
    """
    NAVO Teams Bot that processes natural language queries
    and returns knowledge from Confluence and SharePoint
    """
    
    def __init__(self):
        super().__init__()
        self.query_processor = QueryProcessor()
        logger.info("NAVO Teams Bot initialized")
    
    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle incoming messages from Teams
        """
        try:
            user_query = turn_context.activity.text.strip()
            user_name = turn_context.activity.from_property.name
            
            logger.info(f"Processing query from {user_name}: {user_query}")
            
            # Process the query
            response = await self.query_processor.process_query(user_query)
            
            # Create adaptive card response
            card = create_response_card(
                query=user_query,
                answer=response["answer"],
                sources=response["sources"],
                confidence=response["confidence"]
            )
            
            # Send response
            card_activity = MessageFactory.attachment(card)
            await turn_context.send_activity(card_activity)
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            error_message = "Sorry, I encountered an error processing your request. Please try again."
            await turn_context.send_activity(MessageFactory.text(error_message))
    
    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        """
        Welcome message when bot is added to a conversation
        """
        welcome_text = (
            "👋 Hi! I'm NAVO, your knowledge discovery assistant.\n\n"
            "Ask me questions about your documentation and I'll search "
            "Confluence and SharePoint to find the answers.\n\n"
            "Try asking: *Where's the API documentation?*"
        )
        
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(MessageFactory.text(welcome_text))

