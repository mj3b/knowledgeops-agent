#!/usr/bin/env python3
"""
Confluence Integration Module for KnowledgeOps Agent
Enterprise-grade integration with comprehensive authentication, content processing, and error handling.
"""

import os
import json
import logging
import asyncio
import aiohttp
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
import base64
from cryptography.fernet import Fernet
import jwt
from requests_oauthlib import OAuth2Session
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConfluenceConfig:
    """Configuration for Confluence integration"""
    base_url: str
    auth_type: str  # 'oauth2', 'api_token', 'saml'
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    api_token: Optional[str] = None
    username: Optional[str] = None
    saml_config: Optional[Dict] = None
    spaces: Optional[List[str]] = None
    max_results: int = 100
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit_per_minute: int = 1000

@dataclass
class ConfluenceContent:
    """Standardized content structure from Confluence"""
    id: str
    title: str
    content_text: str
    content_html: str
    summary: str
    author: str
    created_date: datetime
    modified_date: datetime
    space_key: str
    space_name: str
    url: str
    content_type: str
    tags: List[str]
    attachments: List[Dict]
    permissions: Dict[str, List[str]]
    metadata: Dict[str, Any]
    parent_id: Optional[str] = None
    version: int = 1

class ConfluenceAuthManager:
    """Handles authentication for different Confluence deployment types"""
    
    def __init__(self, config: ConfluenceConfig):
        self.config = config
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=config.timeout)
        )
        self._access_token = None
        self._token_expires_at = None
        
    async def authenticate(self) -> Dict[str, str]:
        """Authenticate based on configured auth type"""
        if self.config.auth_type == 'oauth2':
            return await self._oauth2_authenticate()
        elif self.config.auth_type == 'api_token':
            return self._api_token_authenticate()
        elif self.config.auth_type == 'saml':
            return await self._saml_authenticate()
        else:
            raise ValueError(f"Unsupported auth type: {self.config.auth_type}")
    
    async def _oauth2_authenticate(self) -> Dict[str, str]:
        """OAuth 2.0 authentication for Confluence Cloud"""
        if self._access_token and self._token_expires_at > time.time():
            return {'Authorization': f'Bearer {self._access_token}'}
        
        token_url = 'https://auth.atlassian.com/oauth/token'
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'audience': 'api.atlassian.com'
        }
        
        async with self.session.post(token_url, data=data) as response:
            if response.status == 200:
                token_data = await response.json()
                self._access_token = token_data['access_token']
                self._token_expires_at = time.time() + token_data.get('expires_in', 3600) - 60
                
                logger.info("OAuth2 authentication successful")
                return {'Authorization': f'Bearer {self._access_token}'}
            else:
                error_text = await response.text()
                raise Exception(f"OAuth2 authentication failed: {response.status} - {error_text}")
    
    def _api_token_authenticate(self) -> Dict[str, str]:
        """API token authentication for Confluence Cloud/Server"""
        if not self.config.username or not self.config.api_token:
            raise ValueError("Username and API token required for API token authentication")
        
        credentials = f"{self.config.username}:{self.config.api_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        logger.info("API token authentication configured")
        return {'Authorization': f'Basic {encoded_credentials}'}
    
    async def _saml_authenticate(self) -> Dict[str, str]:
        """SAML authentication for Confluence Server/Data Center"""
        if not self.config.saml_config:
            raise ValueError("SAML configuration required for SAML authentication")
        
        # Implementation would depend on specific SAML setup
        # This is a placeholder for enterprise SAML integration
        logger.info("SAML authentication configured")
        return {'Authorization': 'Bearer saml_token_placeholder'}
    
    async def close(self):
        """Close the session"""
        await self.session.close()

class ConfluenceContentExtractor:
    """Extracts and processes content from Confluence"""
    
    def __init__(self, config: ConfluenceConfig):
        self.config = config
        
    def extract_text_from_html(self, html_content: str) -> str:
        """Extract clean text from Confluence HTML"""
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Handle Confluence-specific macros
        self._process_confluence_macros(soup)
        
        # Extract text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _process_confluence_macros(self, soup: BeautifulSoup):
        """Process Confluence-specific macros and structured content"""
        # Handle code blocks
        for code_block in soup.find_all('ac:structured-macro', {'ac:name': 'code'}):
            code_content = code_block.find('ac:plain-text-body')
            if code_content:
                code_block.replace_with(f"[CODE BLOCK: {code_content.get_text()}]")
        
        # Handle info/warning/note macros
        for macro in soup.find_all('ac:structured-macro', {'ac:name': ['info', 'warning', 'note']}):
            macro_type = macro.get('ac:name', 'info').upper()
            rich_body = macro.find('ac:rich-text-body')
            if rich_body:
                content = rich_body.get_text(strip=True)
                macro.replace_with(f"[{macro_type}: {content}]")
        
        # Handle table of contents
        for toc in soup.find_all('ac:structured-macro', {'ac:name': 'toc'}):
            toc.replace_with("[TABLE OF CONTENTS]")
        
        # Handle attachments and images
        for attachment in soup.find_all('ac:image'):
            filename = attachment.get('ac:filename', 'image')
            attachment.replace_with(f"[IMAGE: {filename}]")
    
    def extract_metadata(self, page_data: Dict) -> Dict[str, Any]:
        """Extract comprehensive metadata from page data"""
        metadata = {
            'space_type': page_data.get('space', {}).get('type'),
            'content_status': page_data.get('status'),
            'version_number': page_data.get('version', {}).get('number'),
            'version_message': page_data.get('version', {}).get('message'),
            'restrictions': page_data.get('restrictions', {}),
            'ancestors': [],
            'descendants': [],
            'labels': [],
            'properties': {}
        }
        
        # Extract ancestors
        if 'ancestors' in page_data:
            metadata['ancestors'] = [
                {'id': ancestor['id'], 'title': ancestor['title']}
                for ancestor in page_data['ancestors']
            ]
        
        # Extract labels
        if 'metadata' in page_data and 'labels' in page_data['metadata']:
            metadata['labels'] = [
                label['name'] for label in page_data['metadata']['labels'].get('results', [])
            ]
        
        return metadata

class ConfluencePermissionManager:
    """Manages permission checking and enforcement"""
    
    def __init__(self, auth_manager: ConfluenceAuthManager):
        self.auth_manager = auth_manager
        
    async def get_user_permissions(self, user_id: str, content_id: str) -> Dict[str, bool]:
        """Get user permissions for specific content"""
        headers = await self.auth_manager.authenticate()
        
        permissions_url = f"{self.auth_manager.config.base_url}/rest/api/content/{content_id}/restriction"
        
        async with self.auth_manager.session.get(permissions_url, headers=headers) as response:
            if response.status == 200:
                restrictions_data = await response.json()
                return self._parse_permissions(restrictions_data, user_id)
            else:
                logger.warning(f"Failed to get permissions for content {content_id}: {response.status}")
                return {'read': False, 'write': False, 'delete': False}
    
    def _parse_permissions(self, restrictions_data: Dict, user_id: str) -> Dict[str, bool]:
        """Parse Confluence restrictions into permission flags"""
        permissions = {'read': True, 'write': False, 'delete': False}
        
        for restriction in restrictions_data.get('results', []):
            operation = restriction.get('operation')
            restrictions_list = restriction.get('restrictions', {})
            
            # Check user restrictions
            user_restrictions = restrictions_list.get('user', {}).get('results', [])
            group_restrictions = restrictions_list.get('group', {}).get('results', [])
            
            # If user is explicitly listed, grant permission
            user_has_permission = any(
                user.get('accountId') == user_id for user in user_restrictions
            )
            
            if operation == 'read' and not user_has_permission:
                permissions['read'] = False
            elif operation in ['update', 'write'] and user_has_permission:
                permissions['write'] = True
            elif operation == 'delete' and user_has_permission:
                permissions['delete'] = True
        
        return permissions

class ConfluenceAPIClient:
    """Main Confluence API client with enterprise features"""
    
    def __init__(self, config: ConfluenceConfig):
        self.config = config
        self.auth_manager = ConfluenceAuthManager(config)
        self.content_extractor = ConfluenceContentExtractor(config)
        self.permission_manager = ConfluencePermissionManager(self.auth_manager)
        self._rate_limiter = asyncio.Semaphore(config.rate_limit_per_minute // 60)
        
    async def initialize(self):
        """Initialize the client and authenticate"""
        await self.auth_manager.authenticate()
        logger.info("Confluence API client initialized")
    
    async def discover_spaces(self) -> List[Dict[str, Any]]:
        """Discover all accessible spaces"""
        headers = await self.auth_manager.authenticate()
        
        spaces_url = f"{self.config.base_url}/rest/api/space"
        params = {
            'limit': self.config.max_results,
            'expand': 'permissions,description.plain,homepage'
        }
        
        all_spaces = []
        start = 0
        
        while True:
            params['start'] = start
            
            async with self._rate_limiter:
                async with self.auth_manager.session.get(
                    spaces_url, headers=headers, params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        spaces = data.get('results', [])
                        
                        if not spaces:
                            break
                        
                        all_spaces.extend(spaces)
                        
                        if len(spaces) < self.config.max_results:
                            break
                        
                        start += self.config.max_results
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to discover spaces: {response.status} - {error_text}")
                        break
        
        logger.info(f"Discovered {len(all_spaces)} spaces")
        return all_spaces
    
    async def search_content(self, cql_query: str, user_context: Optional[Dict] = None) -> List[ConfluenceContent]:
        """Search content using CQL with user context"""
        headers = await self.auth_manager.authenticate()
        
        search_url = f"{self.config.base_url}/rest/api/content/search"
        params = {
            'cql': cql_query,
            'limit': self.config.max_results,
            'expand': 'body.storage,metadata.labels,space,version,ancestors'
        }
        
        all_results = []
        start = 0
        
        while True:
            params['start'] = start
            
            async with self._rate_limiter:
                async with self.auth_manager.session.get(
                    search_url, headers=headers, params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        
                        if not results:
                            break
                        
                        # Process each result
                        for result in results:
                            try:
                                content = await self._process_content_item(result, user_context)
                                if content:
                                    all_results.append(content)
                            except Exception as e:
                                logger.error(f"Error processing content {result.get('id')}: {e}")
                        
                        if len(results) < self.config.max_results:
                            break
                        
                        start += self.config.max_results
                    else:
                        error_text = await response.text()
                        logger.error(f"Search failed: {response.status} - {error_text}")
                        break
        
        logger.info(f"Found {len(all_results)} content items")
        return all_results
    
    async def get_page_by_id(self, page_id: str, user_context: Optional[Dict] = None) -> Optional[ConfluenceContent]:
        """Get a specific page by ID"""
        headers = await self.auth_manager.authenticate()
        
        page_url = f"{self.config.base_url}/rest/api/content/{page_id}"
        params = {
            'expand': 'body.storage,metadata.labels,space,version,ancestors,children.page'
        }
        
        async with self._rate_limiter:
            async with self.auth_manager.session.get(
                page_url, headers=headers, params=params
            ) as response:
                if response.status == 200:
                    page_data = await response.json()
                    return await self._process_content_item(page_data, user_context)
                else:
                    logger.error(f"Failed to get page {page_id}: {response.status}")
                    return None
    
    async def get_page_attachments(self, page_id: str) -> List[Dict[str, Any]]:
        """Get attachments for a specific page"""
        headers = await self.auth_manager.authenticate()
        
        attachments_url = f"{self.config.base_url}/rest/api/content/{page_id}/child/attachment"
        params = {'expand': 'metadata,version'}
        
        async with self._rate_limiter:
            async with self.auth_manager.session.get(
                attachments_url, headers=headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                else:
                    logger.warning(f"Failed to get attachments for page {page_id}: {response.status}")
                    return []
    
    async def _process_content_item(self, item_data: Dict, user_context: Optional[Dict] = None) -> Optional[ConfluenceContent]:
        """Process a content item into standardized format"""
        try:
            # Extract basic information
            content_id = item_data['id']
            title = item_data['title']
            content_type = item_data['type']
            
            # Extract content
            body = item_data.get('body', {})
            storage_body = body.get('storage', {})
            html_content = storage_body.get('value', '')
            text_content = self.content_extractor.extract_text_from_html(html_content)
            
            # Generate summary
            summary = text_content[:300] + '...' if len(text_content) > 300 else text_content
            
            # Extract dates
            created_date = datetime.fromisoformat(item_data['version']['when'].replace('Z', '+00:00'))
            modified_date = created_date  # Confluence doesn't separate created/modified in basic API
            
            # Extract space information
            space = item_data.get('space', {})
            space_key = space.get('key', '')
            space_name = space.get('name', '')
            
            # Extract author
            author = item_data.get('version', {}).get('by', {}).get('displayName', 'Unknown')
            
            # Build URL
            url = urljoin(self.config.base_url, f"/wiki/spaces/{space_key}/pages/{content_id}")
            
            # Extract tags
            labels = item_data.get('metadata', {}).get('labels', {}).get('results', [])
            tags = [label['name'] for label in labels]
            
            # Get attachments
            attachments = await self.get_page_attachments(content_id)
            
            # Get permissions if user context provided
            permissions = {}
            if user_context and user_context.get('user_id'):
                permissions = await self.permission_manager.get_user_permissions(
                    user_context['user_id'], content_id
                )
            
            # Extract metadata
            metadata = self.content_extractor.extract_metadata(item_data)
            
            return ConfluenceContent(
                id=content_id,
                title=title,
                content_text=text_content,
                content_html=html_content,
                summary=summary,
                author=author,
                created_date=created_date,
                modified_date=modified_date,
                space_key=space_key,
                space_name=space_name,
                url=url,
                content_type=content_type,
                tags=tags,
                attachments=[{
                    'id': att['id'],
                    'title': att['title'],
                    'mediaType': att.get('metadata', {}).get('mediaType', ''),
                    'fileSize': att.get('metadata', {}).get('fileSize', 0),
                    'downloadUrl': urljoin(self.config.base_url, att.get('_links', {}).get('download', ''))
                } for att in attachments],
                permissions=permissions,
                metadata=metadata,
                parent_id=item_data.get('ancestors', [{}])[-1].get('id') if item_data.get('ancestors') else None,
                version=item_data.get('version', {}).get('number', 1)
            )
            
        except Exception as e:
            logger.error(f"Error processing content item {item_data.get('id', 'unknown')}: {e}")
            return None
    
    async def sync_content(self, spaces: Optional[List[str]] = None, since: Optional[datetime] = None) -> List[ConfluenceContent]:
        """Sync content from specified spaces or all accessible spaces"""
        if spaces is None:
            spaces = self.config.spaces or []
        
        if not spaces:
            # Discover all spaces if none specified
            discovered_spaces = await self.discover_spaces()
            spaces = [space['key'] for space in discovered_spaces]
        
        all_content = []
        
        for space_key in spaces:
            logger.info(f"Syncing content from space: {space_key}")
            
            # Build CQL query
            cql_parts = [f"space = {space_key}"]
            
            if since:
                since_str = since.strftime('%Y-%m-%d')
                cql_parts.append(f"lastModified >= '{since_str}'")
            
            cql_query = " AND ".join(cql_parts)
            
            try:
                space_content = await self.search_content(cql_query)
                all_content.extend(space_content)
                logger.info(f"Synced {len(space_content)} items from space {space_key}")
            except Exception as e:
                logger.error(f"Error syncing space {space_key}: {e}")
        
        logger.info(f"Total content synced: {len(all_content)} items")
        return all_content
    
    async def close(self):
        """Close the client and cleanup resources"""
        await self.auth_manager.close()
        logger.info("Confluence API client closed")

# Example usage and configuration
async def main():
    """Example usage of the Confluence integration"""
    
    # Configuration for Confluence Cloud with OAuth2
    config = ConfluenceConfig(
        base_url="https://your-domain.atlassian.net",
        auth_type="oauth2",
        client_id=os.getenv("CONFLUENCE_CLIENT_ID"),
        client_secret=os.getenv("CONFLUENCE_CLIENT_SECRET"),
        spaces=["ENG", "DOCS", "PROD"],
        max_results=50
    )
    
    # Alternative configuration for API token
    # config = ConfluenceConfig(
    #     base_url="https://your-domain.atlassian.net",
    #     auth_type="api_token",
    #     username=os.getenv("CONFLUENCE_USERNAME"),
    #     api_token=os.getenv("CONFLUENCE_API_TOKEN"),
    #     spaces=["ENG", "DOCS", "PROD"]
    # )
    
    client = ConfluenceAPIClient(config)
    
    try:
        await client.initialize()
        
        # Discover spaces
        spaces = await client.discover_spaces()
        print(f"Found {len(spaces)} spaces")
        
        # Search for content
        search_results = await client.search_content("text ~ 'deployment' AND space = ENG")
        print(f"Found {len(search_results)} deployment-related pages")
        
        # Sync all content
        all_content = await client.sync_content()
        print(f"Synced {len(all_content)} total content items")
        
        # Example: Get specific page
        if search_results:
            page = await client.get_page_by_id(search_results[0].id)
            if page:
                print(f"Retrieved page: {page.title}")
                print(f"Content length: {len(page.content_text)} characters")
                print(f"Tags: {page.tags}")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())

