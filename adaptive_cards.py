"""
Adaptive Cards for Microsoft Teams
Creates rich response cards for NAVO bot responses
"""

import logging
from typing import List, Dict, Any
from botbuilder.schema import Attachment

logger = logging.getLogger(__name__)


def create_response_card(query: str, answer: str, sources: List[Dict], confidence: float) -> Attachment:
    """
    Create an adaptive card for NAVO response
    """
    
    # Confidence color coding
    if confidence >= 0.8:
        confidence_color = "good"
        confidence_text = "High"
    elif confidence >= 0.6:
        confidence_color = "warning"
        confidence_text = "Medium"
    else:
        confidence_color = "attention"
        confidence_text = "Low"
    
    # Build sources section
    sources_elements = []
    for i, source in enumerate(sources[:3], 1):  # Limit to 3 sources
        source_element = {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"**{source['title']}**",
                            "size": "small",
                            "weight": "bolder"
                        },
                        {
                            "type": "TextBlock",
                            "text": source.get('excerpt', ''),
                            "size": "small",
                            "wrap": True,
                            "maxLines": 2
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "ActionSet",
                            "actions": [
                                {
                                    "type": "Action.OpenUrl",
                                    "title": "View",
                                    "url": source['url']
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        sources_elements.append(source_element)
        
        # Add separator between sources
        if i < len(sources):
            sources_elements.append({"type": "Container", "height": "stretch"})
    
    # Create the adaptive card
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
                                        "url": "https://img.icons8.com/fluency/48/search.png",
                                        "size": "small"
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
                                        "weight": "bolder",
                                        "size": "medium"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": f"*{query}*",
                                        "size": "small",
                                        "color": "accent"
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
                        "text": "**Summary**",
                        "weight": "bolder",
                        "size": "medium"
                    },
                    {
                        "type": "TextBlock",
                        "text": answer,
                        "wrap": True,
                        "spacing": "small"
                    }
                ]
            }
        ]
    }
    
    # Add sources section if available
    if sources:
        sources_container = {
            "type": "Container",
            "items": [
                {
                    "type": "TextBlock",
                    "text": "**Sources**",
                    "weight": "bolder",
                    "size": "medium"
                }
            ] + sources_elements
        }
        card_content["body"].append(sources_container)
    
    # Add metadata section
    metadata_facts = []
    
    if sources:
        metadata_facts.append({
            "title": "Sources Found:",
            "value": str(len(sources))
        })
    
    metadata_facts.extend([
        {
            "title": "Confidence:",
            "value": f"{confidence_text} ({confidence:.0%})"
        },
        {
            "title": "Search Time:",
            "value": "< 1 second"
        }
    ])
    
    metadata_container = {
        "type": "Container",
        "items": [
            {
                "type": "FactSet",
                "facts": metadata_facts
            }
        ]
    }
    card_content["body"].append(metadata_container)
    
    # Add action buttons
    actions = [
        {
            "type": "Action.Submit",
            "title": "👍 Helpful",
            "data": {
                "action": "feedback",
                "type": "positive",
                "query": query
            }
        },
        {
            "type": "Action.Submit",
            "title": "👎 Not Helpful",
            "data": {
                "action": "feedback",
                "type": "negative",
                "query": query
            }
        }
    ]
    
    card_content["actions"] = actions
    
    # Create attachment
    attachment = Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card_content
    )
    
    return attachment


def create_error_card(error_message: str) -> Attachment:
    """
    Create an error card for when something goes wrong
    """
    card_content = {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "Container",
                "style": "attention",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "⚠️ Error",
                        "weight": "bolder",
                        "size": "medium"
                    },
                    {
                        "type": "TextBlock",
                        "text": error_message,
                        "wrap": True
                    }
                ]
            }
        ]
    }
    
    attachment = Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card_content
    )
    
    return attachment

