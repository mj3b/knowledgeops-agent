"""
NAVO - Navigate + Ops
"NAVO knows where it's written."

Enterprise knowledge discovery platform with OpenAI Enterprise integration.
"""

__version__ = "2.0.0"
__author__ = "NAVO Team"
__description__ = "Enterprise knowledge discovery platform with OpenAI Enterprise integration"
__tagline__ = "NAVO knows where it's written."

from .core.navo_engine import NAVOEngine
from .core.query_processor import QueryProcessor
from .core.response_generator import ResponseGenerator
from .integrations.openai.enterprise_client import OpenAIEnterpriseClient

__all__ = [
    "NAVOEngine",
    "QueryProcessor", 
    "ResponseGenerator",
    "OpenAIEnterpriseClient"
]

