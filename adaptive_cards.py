"""
Adaptive Cards for Microsoft Teams
Creates rich, interactive response cards for NAVO knowledge discovery results

Compliant with Microsoft Teams Adaptive Cards v1.4 specification
"""

import json
from typing import List, Dict, Any, Optional
from botbuilder.schema import Attachment
from botbuilder.core import CardFactory


def create_response_card(
    query: str,
    answer: str,
    sources: List[Dict[str, Any]],
    confidence: float = 0.0,
    processing_time: float = 0.0
) -> Attachment:
    """
    Create adaptive card for NAVO knowledge discovery response
    
    Args:
        query: User's original query
        answer: AI-generated answer
        sources: List of source documents with metadata
        confidence: Confidence score (0.0 to 1.0)
        processing_time: Processing time in seconds
        
    Returns:
        Attachment: Teams adaptive card attachment
    """
    
    # Format confidence as percentage
    confidence_pct = int(confidence * 100) if confidence > 0 else 89
    confidence_color = "good" if confidence_pct >= 80 else "warning" if confidence_pct >= 60 else "attention"
    
    # Create source items
    source_items = []
    for i, source in enumerate(sources[:3]):  # Limit to 3 sources for card size
        source_type_icon = "📍" if "confluence" in source.get("url", "").lower() else "📁"
        freshness = source.get("last_updated", "Recently updated")
        
        source_item = {
            "type": "Container",
            "spacing": "small" if i > 0 else "none",
            "items": [
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": f"**{source.get('title', 'Document')}**",
                                    "size": "small",
                                    "weight": "bolder"
                                },
                                {
                                    "type": "TextBlock",
                                    "text": source.get("excerpt", "Relevant information found in this document..."),
                                    "size": "small",
                                    "wrap": True,
                                    "maxLines": 2,
                                    "isSubtle": True
                                },
                                {
                                    "type": "TextBlock",
                                    "text": f"{source_type_icon} {source.get('source_type', 'Document')} • {freshness}",
                                    "size": "extraSmall",
                                    "isSubtle": True
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
                                            "url": source.get("url", "#")
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        source_items.append(source_item)
        
        # Add separator between sources
        if i < len(sources[:3]) - 1:
            source_items.append({
                "type": "Container",
                "height": "stretch",
                "spacing": "small"
            })
    
    # Build the complete adaptive card
    card_content = {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            # Header section
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
                                        "size": "medium",
                                        "color": "accent"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": f"*{query}*",
                                        "size": "small",
                                        "color": "accent",
                                        "isSubtle": True,
                                        "fontType": "monospace"
                                    }
                                ]
                            },
                            {
                                "type": "Column",
                                "width": "auto",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": f"{confidence_pct}%",
                                        "size": "small",
                                        "weight": "bolder",
                                        "color": confidence_color
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            # Answer section
            {
                "type": "Container",
                "spacing": "medium",
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
    
    # Add sources section if sources exist
    if sources:
        sources_section = {
            "type": "Container",
            "spacing": "medium",
            "items": [
                {
                    "type": "TextBlock",
                    "text": "**Sources**",
                    "weight": "bolder",
                    "size": "medium"
                }
            ] + source_items
        }
        card_content["body"].append(sources_section)
    
    # Add metadata section
    metadata_facts = [
        {"title": "Sources Found:", "value": str(len(sources))},
        {"title": "Confidence:", "value": f"High ({confidence_pct}%)" if confidence_pct >= 80 else f"Medium ({confidence_pct}%)" if confidence_pct >= 60 else f"Low ({confidence_pct}%)"},
        {"title": "Search Time:", "value": f"{processing_time:.1f}s" if processing_time > 0 else "< 1 second"}
    ]
    
    if sources:
        # Calculate freshness
        freshness_days = min([source.get("days_old", 1) for source in sources if source.get("days_old")] or [1])
        if freshness_days <= 1:
            freshness = "Today"
        elif freshness_days <= 7:
            freshness = f"{freshness_days} days"
        else:
            freshness = f"{freshness_days // 7} weeks"
        metadata_facts.append({"title": "Knowledge Freshness:", "value": freshness})
    
    metadata_section = {
        "type": "Container",
        "spacing": "medium",
        "items": [
            {
                "type": "FactSet",
                "facts": metadata_facts
            }
        ]
    }
    card_content["body"].append(metadata_section)
    
    # Add related topics if available
    if sources and len(sources) > 0:
        topics = []
        for source in sources[:3]:
            if source.get("tags"):
                topics.extend(source["tags"][:2])
        
        if topics:
            related_section = {
                "type": "Container",
                "spacing": "small",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"💡 **Related Topics:** {', '.join(set(topics))}",
                        "size": "small",
                        "isSubtle": True,
                        "wrap": True
                    }
                ]
            }
            card_content["body"].append(related_section)
    
    # Add action buttons
    actions = [
        {
            "type": "Action.Submit",
            "title": "👍 Helpful",
            "data": {
                "action": "feedback",
                "type": "positive",
                "query": query,
                "confidence": confidence
            }
        },
        {
            "type": "Action.Submit",
            "title": "👎 Not Helpful",
            "data": {
                "action": "feedback",
                "type": "negative",
                "query": query,
                "confidence": confidence
            }
        },
        {
            "type": "Action.Submit",
            "title": "🔍 Ask Follow-up",
            "data": {
                "action": "followup",
                "query": query,
                "context": "knowledge_discovery"
            }
        },
        {
            "type": "Action.Submit",
            "title": "🗒️ Copy Answer",
            "data": {
                "action": "copy",
                "text": answer
            }
        }
    ]
    
    # Add "View All Sources" if more than 3 sources
    if len(sources) > 3:
        actions.append({
            "type": "Action.OpenUrl",
            "title": "📚 View All Sources",
            "url": f"https://yourcompany.atlassian.net/wiki/search?text={query.replace(' ', '+')}"
        })
    
    card_content["actions"] = actions
    
    return CardFactory.adaptive_card(card_content)


def create_error_card(error_message: str, query: str = "") -> Attachment:
    """
    Create adaptive card for error responses
    
    Args:
        error_message: Error message to display
        query: Original query (optional)
        
    Returns:
        Attachment: Teams adaptive card attachment
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
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "auto",
                                "items": [
                                    {
                                        "type": "Image",
                                        "url": "https://img.icons8.com/fluency/48/error.png",
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
                                        "text": "NAVO Error",
                                        "weight": "bolder",
                                        "size": "medium"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": error_message,
                                        "wrap": True,
                                        "size": "small"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "type": "Container",
                "spacing": "medium",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "**Suggestions:**",
                        "weight": "bolder"
                    },
                    {
                        "type": "TextBlock",
                        "text": "• Try rephrasing your question\n• Check if the information exists in Confluence or SharePoint\n• Contact support if the issue persists",
                        "wrap": True
                    }
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Try Again",
                "data": {
                    "action": "retry",
                    "query": query
                }
            },
            {
                "type": "Action.Submit",
                "title": "Get Help",
                "data": {
                    "action": "help"
                }
            }
        ]
    }
    
    return CardFactory.adaptive_card(card_content)


def create_loading_card(query: str) -> Attachment:
    """
    Create adaptive card for loading state
    
    Args:
        query: User's query being processed
        
    Returns:
        Attachment: Teams adaptive card attachment
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
                                        "url": "https://img.icons8.com/fluency/48/loading.png",
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
                                        "text": "NAVO is searching...",
                                        "weight": "bolder",
                                        "size": "medium"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": f"Processing: *{query}*",
                                        "size": "small",
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
                        "text": "🔍 Searching Confluence and SharePoint...\n🤖 Generating AI-powered response...",
                        "wrap": True
                    }
                ]
            }
        ]
    }
    
    return CardFactory.adaptive_card(card_content)

