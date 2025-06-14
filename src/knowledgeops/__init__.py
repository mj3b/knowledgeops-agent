"""
KnowledgeOps Agent - Enterprise Knowledge Discovery Platform

A comprehensive solution for intelligent knowledge discovery across Confluence and SharePoint platforms.
Provides AI-powered search, semantic understanding, and unified content access for enterprise environments.
"""

__version__ = "1.0.0"
__author__ = "KnowledgeOps Team"
__email__ = "support@knowledgeops.com"

from .core.unified_knowledge_manager import UnifiedKnowledgeManager, SearchQuery, SearchResult
from .confluence.confluence_integration import ConfluenceAPIClient, ConfluenceConfig
from .sharepoint.sharepoint_integration import SharePointAPIClient, SharePointConfig

__all__ = [
    "UnifiedKnowledgeManager",
    "SearchQuery", 
    "SearchResult",
    "ConfluenceAPIClient",
    "ConfluenceConfig",
    "SharePointAPIClient", 
    "SharePointConfig"
]

