"""
NAVO Main Application Entry Point
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
import yaml
import uvicorn
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from navo.api.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('navo.log')
    ]
)

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Override with environment variables
        config = override_with_env_vars(config)
        
        logger.info(f"Configuration loaded from {config_path}")
        return config
        
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found, using defaults")
        return get_default_config()
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return get_default_config()


def override_with_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Override configuration with environment variables.
    
    Args:
        config: Base configuration
        
    Returns:
        Updated configuration
    """
    # OpenAI Enterprise settings
    if os.getenv("OPENAI_API_KEY"):
        config.setdefault("openai", {})["api_key"] = os.getenv("OPENAI_API_KEY")
    
    if os.getenv("OPENAI_ORGANIZATION_ID"):
        config.setdefault("openai", {})["organization_id"] = os.getenv("OPENAI_ORGANIZATION_ID")
    
    # Confluence settings
    if os.getenv("CONFLUENCE_BASE_URL"):
        config.setdefault("integrations", {}).setdefault("confluence", {})["base_url"] = os.getenv("CONFLUENCE_BASE_URL")
    
    if os.getenv("CONFLUENCE_USERNAME"):
        config.setdefault("integrations", {}).setdefault("confluence", {})["username"] = os.getenv("CONFLUENCE_USERNAME")
    
    if os.getenv("CONFLUENCE_API_TOKEN"):
        config.setdefault("integrations", {}).setdefault("confluence", {})["api_token"] = os.getenv("CONFLUENCE_API_TOKEN")
    
    # SharePoint settings
    if os.getenv("SHAREPOINT_TENANT_ID"):
        config.setdefault("integrations", {}).setdefault("sharepoint", {})["tenant_id"] = os.getenv("SHAREPOINT_TENANT_ID")
    
    if os.getenv("SHAREPOINT_CLIENT_ID"):
        config.setdefault("integrations", {}).setdefault("sharepoint", {})["client_id"] = os.getenv("SHAREPOINT_CLIENT_ID")
    
    if os.getenv("SHAREPOINT_CLIENT_SECRET"):
        config.setdefault("integrations", {}).setdefault("sharepoint", {})["client_secret"] = os.getenv("SHAREPOINT_CLIENT_SECRET")
    
    # Redis settings
    if os.getenv("REDIS_URL"):
        config.setdefault("cache", {})["redis_url"] = os.getenv("REDIS_URL")
    
    # Server settings
    if os.getenv("PORT"):
        config.setdefault("server", {})["port"] = int(os.getenv("PORT"))
    
    if os.getenv("HOST"):
        config.setdefault("server", {})["host"] = os.getenv("HOST")
    
    return config


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration.
    
    Returns:
        Default configuration dictionary
    """
    return {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "organization_id": os.getenv("OPENAI_ORGANIZATION_ID", ""),
            "default_model": "gpt-4o",
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 60
        },
        "integrations": {
            "confluence": {
                "enabled": bool(os.getenv("CONFLUENCE_BASE_URL")),
                "base_url": os.getenv("CONFLUENCE_BASE_URL", ""),
                "username": os.getenv("CONFLUENCE_USERNAME", ""),
                "api_token": os.getenv("CONFLUENCE_API_TOKEN", ""),
                "spaces_to_sync": [],
                "spaces_to_exclude": [],
                "max_results_per_request": 50,
                "respect_permissions": True
            },
            "sharepoint": {
                "enabled": bool(os.getenv("SHAREPOINT_TENANT_ID")),
                "tenant_id": os.getenv("SHAREPOINT_TENANT_ID", ""),
                "client_id": os.getenv("SHAREPOINT_CLIENT_ID", ""),
                "client_secret": os.getenv("SHAREPOINT_CLIENT_SECRET", ""),
                "site_urls": [],
                "sites_to_exclude": [],
                "file_types": [".docx", ".pdf", ".txt", ".md"],
                "max_file_size_mb": 50,
                "respect_permissions": True
            }
        },
        "cache": {
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "redis_db": 0,
            "default_ttl": 3600,
            "query_cache_ttl": 1800,
            "document_cache_ttl": 7200,
            "max_cache_size": 10000,
            "memory_cache_max_size": 1000
        },
        "query_processing": {
            "max_keywords": 10,
            "confidence_threshold": 0.7
        },
        "response_generation": {
            "max_context_length": 8000,
            "include_sources": True,
            "generate_follow_ups": True,
            "max_response_tokens": 1000
        },
        "permissions": {
            "enforce_source_permissions": True,
            "cache_permissions": True,
            "permission_cache_ttl": 3600,
            "admin_users": [],
            "default_permissions": {
                "confluence": "read",
                "sharepoint": "read"
            }
        },
        "server": {
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", 8000)),
            "workers": 1,
            "reload": False
        },
        "cors": {
            "allowed_origins": ["*"]
        },
        "rate_limiting": {
            "enabled": True,
            "requests_per_minute": 60,
            "burst_size": 10
        },
        "authentication": {
            "enabled": False,
            "jwt_secret": os.getenv("JWT_SECRET", "your-secret-key"),
            "token_expiry_hours": 24
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration.
    
    Args:
        config: Configuration to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Check required OpenAI settings
    if not config.get("openai", {}).get("api_key"):
        logger.error("OpenAI API key is required")
        return False
    
    # Validate integration settings
    confluence_config = config.get("integrations", {}).get("confluence", {})
    if confluence_config.get("enabled", False):
        required_confluence = ["base_url", "username", "api_token"]
        for field in required_confluence:
            if not confluence_config.get(field):
                logger.error(f"Confluence {field} is required when Confluence is enabled")
                return False
    
    sharepoint_config = config.get("integrations", {}).get("sharepoint", {})
    if sharepoint_config.get("enabled", False):
        required_sharepoint = ["tenant_id", "client_id", "client_secret"]
        for field in required_sharepoint:
            if not sharepoint_config.get(field):
                logger.error(f"SharePoint {field} is required when SharePoint is enabled")
                return False
    
    logger.info("Configuration validation passed")
    return True


def main():
    """Main application entry point."""
    logger.info("Starting NAVO - Navigate + Ops")
    logger.info("NAVO knows where it's written.")
    
    # Load configuration
    config = load_config()
    
    # Validate configuration
    if not validate_config(config):
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    # Create FastAPI app
    app = create_app(config)
    
    # Get server configuration
    server_config = config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    workers = server_config.get("workers", 1)
    reload = server_config.get("reload", False)
    
    logger.info(f"Starting NAVO server on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()

