"""
NAVO Teams Bot
Microsoft Teams bot that provides AI-powered knowledge discovery
from Confluence and SharePoint using Enterprise GPT
"""

import logging
from typing import Dict, Any, List
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory, CardFactory
from botbuilder.core.conversation_state import ConversationState
from botbuilder.core.user_state import UserState
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes, Attachment

from query_processor import QueryProcessor
from adaptive_cards import create_response_card, create_error_card

logger = logging.getLogger(__name__)


class NAVOBot(ActivityHandler):
    """
    NAVO Teams Bot - AI-powered knowledge discovery bot
    
    Handles Microsoft Teams conversations and routes queries to 
    Confluence and SharePoint knowledge sources using Enterprise GPT.
    
    Compliant with Microsoft Teams Bot Framework guidelines.
    """
    
    def __init__(self, conversation_state: ConversationState = None, user_state: UserState = None):
        super().__init__()
        self.query_processor = QueryProcessor()
        self.conversation_state = conversation_state
        self.user_state = user_state
        logger.info("NAVO Teams Bot initialized with Microsoft Bot Framework")
    
    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle incoming messages from Teams users
        
        Processes natural language queries and returns AI-powered responses
        with source attribution from Confluence and SharePoint.
        
        Args:
            turn_context: The context object for this turn
        """
        try:
            user_query = turn_context.activity.text.strip()
            user_name = turn_context.activity.from_property.name or "User"
            
            logger.info(f"Processing query from {user_name}: {user_query}")
            
            # Handle bot mentions in Teams
            if turn_context.activity.text and turn_context.activity.text.startswith('<at>'):
                # Remove bot mention from query
                mention_text = turn_context.activity.text
                # Extract actual query after mention
                import re
                clean_query = re.sub(r'<at>.*?</at>\s*', '', mention_text).strip()
                if clean_query:
                    user_query = clean_query
                else:
                    # If no query after mention, show help
                    await self._send_help_message(turn_context)
                    return
            
            # Process the query through NAVO's knowledge discovery engine
            response = await self.query_processor.process_query(user_query)
            
            # Create and send adaptive card response
            if response["sources"]:
                card = create_response_card(
                    query=user_query,
                    answer=response["answer"],
                    sources=response["sources"],
                    confidence=response["confidence"]
                )
                card_activity = MessageFactory.attachment(card)
                await turn_context.send_activity(card_activity)
            else:
                # Send simple text response if no sources found
                await turn_context.send_activity(
                    MessageFactory.text(response["answer"])
                )
            
            # Save conversation state
            if self.conversation_state:
                await self.conversation_state.save_changes(turn_context)
            if self.user_state:
                await self.user_state.save_changes(turn_context)
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            error_card = create_error_card(
                "I encountered an error processing your request. Please try again or rephrase your question."
            )
            error_activity = MessageFactory.attachment(error_card)
            await turn_context.send_activity(error_activity)
    
    async def on_members_added_activity(
        self, 
        members_added: List[ChannelAccount], 
        turn_context: TurnContext
    ):
        """
        Welcome message when bot is added to a conversation
        
        Provides introduction and usage instructions for new users.
        Compliant with Microsoft Teams bot onboarding best practices.
        
        Args:
            members_added: List of members added to the conversation
            turn_context: The context object for this turn
        """
        welcome_card = self._create_welcome_card()
        
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_activity = MessageFactory.attachment(welcome_card)
                await turn_context.send_activity(welcome_activity)
    
    async def on_teams_members_added_activity(
        self,
        teams_members_added: List[ChannelAccount],
        team_info: Dict[str, Any],
        turn_context: TurnContext
    ):
        """
        Handle Teams-specific member addition events
        
        Args:
            teams_members_added: List of Teams members added
            team_info: Information about the team
            turn_context: The context object for this turn
        """
        await self.on_members_added_activity(teams_members_added, turn_context)
    
    async def _send_help_message(self, turn_context: TurnContext):
        """Send help message with usage instructions"""
        help_text = (
            "👋 **How to use NAVO:**\n\n"
            "• Ask questions about your documentation\n"
            "• I'll search Confluence and SharePoint for answers\n"
            "• Get AI-powered responses with source links\n\n"
            "**Examples:**\n"
            "• *Where's the API documentation?*\n"
            "• *How do I configure the deployment pipeline?*\n"
            "• *What's our troubleshooting guide?*"
        )
        await turn_context.send_activity(MessageFactory.text(help_text))
    
    def _create_welcome_card(self) -> Attachment:
        """
        Create welcome adaptive card for new users
        
        Returns:
            Attachment: Welcome card with NAVO introduction
        """
        card_content = {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "Container",
                    "style": "emphasis",
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
                                            "url": "https://img.icons8.com/fluency/48/artificial-intelligence.png",
                                            "size": "medium"
                                        }
                                    ]
                                },
                                {
                                    "type": "Column",
                                    "width": "stretch",
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": "Welcome to NAVO!",
                                            "weight": "bolder",
                                            "size": "large"
                                        },
                                        {
                                            "type": "TextBlock",
                                            "text": "Your AI-powered knowledge discovery assistant",
                                            "isSubtle": True
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "I help you find information from your Confluence and SharePoint documentation using natural language queries.",
                            "wrap": True
                        },
                        {
                            "type": "TextBlock",
                            "text": "**Try asking me:**",
                            "weight": "bolder",
                            "spacing": "medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": "• Where's the API documentation?\n• How do I configure the deployment pipeline?\n• What's our troubleshooting guide for production issues?",
                            "wrap": True
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Ask a Question",
                    "data": {
                        "action": "help"
                    }
                }
            ]
        }
        
        return CardFactory.adaptive_card(card_content)

