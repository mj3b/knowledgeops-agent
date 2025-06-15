"""
NAVO Permission Manager
Manages user permissions and access control across integrated systems.
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for resources."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class UserPermission:
    """Represents a user's permission for a specific resource."""
    user_id: str
    resource_type: str  # confluence, sharepoint, etc.
    resource_id: str
    permission_level: PermissionLevel
    granted_by: str
    granted_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class PermissionContext:
    """Context for permission evaluation."""
    user_id: str
    resource_type: str
    resource_id: Optional[str] = None
    action: str = "read"
    additional_context: Optional[Dict[str, Any]] = None


class PermissionManager:
    """
    Manages user permissions and access control for NAVO.
    
    Integrates with source systems to respect their permission models
    while providing unified access control.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize permission manager.
        
        Args:
            config: Permission configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Permission settings
        self.enforce_source_permissions = config.get("enforce_source_permissions", True)
        self.cache_permissions = config.get("cache_permissions", True)
        self.permission_cache_ttl = config.get("permission_cache_ttl", 3600)  # 1 hour
        
        # Default permissions
        self.default_permissions = config.get("default_permissions", {
            "confluence": PermissionLevel.READ,
            "sharepoint": PermissionLevel.READ
        })
        
        # Admin users
        self.admin_users = set(config.get("admin_users", []))
        
        # Permission cache
        self.permission_cache = {}
        
        self.logger.info("Permission manager initialized")
    
    async def get_user_permissions(
        self, 
        user_id: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive permissions for a user.
        
        Args:
            user_id: User identifier
            context: Additional context for permission evaluation
            
        Returns:
            Dictionary containing user permissions for all systems
        """
        self.logger.debug(f"Getting permissions for user: {user_id}")
        
        try:
            # Check cache first
            cache_key = f"user_perms:{user_id}"
            if self.cache_permissions and cache_key in self.permission_cache:
                cached_entry = self.permission_cache[cache_key]
                if self._is_cache_valid(cached_entry):
                    return cached_entry["permissions"]
            
            permissions = {}
            
            # Check if user is admin
            is_admin = user_id in self.admin_users
            
            # Get Confluence permissions
            confluence_perms = await self._get_confluence_permissions(user_id, is_admin)
            if confluence_perms:
                permissions["confluence"] = confluence_perms
            
            # Get SharePoint permissions
            sharepoint_perms = await self._get_sharepoint_permissions(user_id, is_admin)
            if sharepoint_perms:
                permissions["sharepoint"] = sharepoint_perms
            
            # Add system-level permissions
            permissions["system"] = {
                "enabled": True,
                "is_admin": is_admin,
                "can_query": True,
                "can_view_sources": True,
                "can_export": not is_admin  # Regular users can export, admins have separate controls
            }
            
            # Cache permissions
            if self.cache_permissions:
                self.permission_cache[cache_key] = {
                    "permissions": permissions,
                    "timestamp": datetime.utcnow()
                }
            
            return permissions
            
        except Exception as e:
            self.logger.error(f"Error getting user permissions: {str(e)}")
            
            # Return minimal permissions on error
            return {
                "system": {
                    "enabled": True,
                    "is_admin": False,
                    "can_query": True,
                    "can_view_sources": False,
                    "can_export": False
                }
            }
    
    async def check_permission(
        self, 
        user_id: str, 
        resource_type: str, 
        resource_id: str, 
        action: str = "read"
    ) -> bool:
        """
        Check if a user has permission for a specific resource and action.
        
        Args:
            user_id: User identifier
            resource_type: Type of resource (confluence, sharepoint, etc.)
            resource_id: Specific resource identifier
            action: Action to check (read, write, admin)
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Get user permissions
            user_permissions = await self.get_user_permissions(user_id)
            
            # Check if user has access to the resource type
            resource_perms = user_permissions.get(resource_type, {})
            if not resource_perms.get("enabled", False):
                return False
            
            # Admin users have all permissions
            if user_permissions.get("system", {}).get("is_admin", False):
                return True
            
            # Check specific resource permissions
            if resource_type == "confluence":
                return await self._check_confluence_permission(
                    user_id, resource_id, action, resource_perms
                )
            elif resource_type == "sharepoint":
                return await self._check_sharepoint_permission(
                    user_id, resource_id, action, resource_perms
                )
            
            # Default to checking if user has general access
            return resource_perms.get("enabled", False)
            
        except Exception as e:
            self.logger.error(f"Error checking permission: {str(e)}")
            return False
    
    async def filter_documents_by_permissions(
        self, 
        user_id: str, 
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of documents based on user permissions.
        
        Args:
            user_id: User identifier
            documents: List of documents to filter
            
        Returns:
            Filtered list of documents the user can access
        """
        if not self.enforce_source_permissions:
            return documents
        
        filtered_docs = []
        
        for doc in documents:
            try:
                resource_type = doc.get("source", "").lower()
                resource_id = doc.get("id") or doc.get("url", "")
                
                if await self.check_permission(user_id, resource_type, resource_id):
                    filtered_docs.append(doc)
                else:
                    self.logger.debug(
                        f"Filtered out document {resource_id} for user {user_id}"
                    )
                    
            except Exception as e:
                self.logger.warning(f"Error checking document permission: {str(e)}")
                # On error, exclude the document to be safe
                continue
        
        self.logger.info(
            f"Filtered {len(documents)} documents to {len(filtered_docs)} "
            f"for user {user_id}"
        )
        
        return filtered_docs
    
    async def _get_confluence_permissions(
        self, 
        user_id: str, 
        is_admin: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Get Confluence permissions for a user.
        
        Args:
            user_id: User identifier
            is_admin: Whether user is a system admin
            
        Returns:
            Confluence permissions dictionary
        """
        try:
            # In a real implementation, this would query Confluence API
            # to get the user's actual permissions
            
            base_permissions = {
                "enabled": True,
                "spaces": [],  # List of accessible spaces
                "permission_level": self.default_permissions.get(
                    "confluence", PermissionLevel.READ
                ).value
            }
            
            if is_admin:
                base_permissions.update({
                    "permission_level": PermissionLevel.ADMIN.value,
                    "spaces": ["*"]  # Access to all spaces
                })
            else:
                # For demo purposes, grant access to common spaces
                base_permissions["spaces"] = ["ENG", "PRODUCT", "SUPPORT"]
            
            return base_permissions
            
        except Exception as e:
            self.logger.error(f"Error getting Confluence permissions: {str(e)}")
            return None
    
    async def _get_sharepoint_permissions(
        self, 
        user_id: str, 
        is_admin: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Get SharePoint permissions for a user.
        
        Args:
            user_id: User identifier
            is_admin: Whether user is a system admin
            
        Returns:
            SharePoint permissions dictionary
        """
        try:
            # In a real implementation, this would query Microsoft Graph API
            # to get the user's actual SharePoint permissions
            
            base_permissions = {
                "enabled": True,
                "sites": [],  # List of accessible sites
                "permission_level": self.default_permissions.get(
                    "sharepoint", PermissionLevel.READ
                ).value
            }
            
            if is_admin:
                base_permissions.update({
                    "permission_level": PermissionLevel.ADMIN.value,
                    "sites": ["*"]  # Access to all sites
                })
            else:
                # For demo purposes, grant access to common sites
                base_permissions["sites"] = ["Engineering", "Documentation"]
            
            return base_permissions
            
        except Exception as e:
            self.logger.error(f"Error getting SharePoint permissions: {str(e)}")
            return None
    
    async def _check_confluence_permission(
        self, 
        user_id: str, 
        resource_id: str, 
        action: str, 
        resource_perms: Dict[str, Any]
    ) -> bool:
        """
        Check specific Confluence permission.
        
        Args:
            user_id: User identifier
            resource_id: Confluence resource ID (page, space, etc.)
            action: Action to check
            resource_perms: User's Confluence permissions
            
        Returns:
            True if user has permission
        """
        # Check if user has access to all spaces
        if "*" in resource_perms.get("spaces", []):
            return True
        
        # Extract space key from resource_id if possible
        # This is a simplified implementation
        space_key = self._extract_confluence_space(resource_id)
        
        if space_key and space_key in resource_perms.get("spaces", []):
            return True
        
        return False
    
    async def _check_sharepoint_permission(
        self, 
        user_id: str, 
        resource_id: str, 
        action: str, 
        resource_perms: Dict[str, Any]
    ) -> bool:
        """
        Check specific SharePoint permission.
        
        Args:
            user_id: User identifier
            resource_id: SharePoint resource ID (site, document, etc.)
            action: Action to check
            resource_perms: User's SharePoint permissions
            
        Returns:
            True if user has permission
        """
        # Check if user has access to all sites
        if "*" in resource_perms.get("sites", []):
            return True
        
        # Extract site name from resource_id if possible
        site_name = self._extract_sharepoint_site(resource_id)
        
        if site_name and site_name in resource_perms.get("sites", []):
            return True
        
        return False
    
    def _extract_confluence_space(self, resource_id: str) -> Optional[str]:
        """
        Extract Confluence space key from resource ID.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Space key if found
        """
        # Simple extraction - in practice this would be more sophisticated
        if "/spaces/" in resource_id:
            parts = resource_id.split("/spaces/")
            if len(parts) > 1:
                space_part = parts[1].split("/")[0]
                return space_part
        
        return None
    
    def _extract_sharepoint_site(self, resource_id: str) -> Optional[str]:
        """
        Extract SharePoint site name from resource ID.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Site name if found
        """
        # Simple extraction - in practice this would be more sophisticated
        if "/sites/" in resource_id:
            parts = resource_id.split("/sites/")
            if len(parts) > 1:
                site_part = parts[1].split("/")[0]
                return site_part
        
        return None
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """
        Check if a cached permission entry is still valid.
        
        Args:
            cache_entry: Cached entry to check
            
        Returns:
            True if valid, False if expired
        """
        timestamp = cache_entry.get("timestamp")
        if not timestamp:
            return False
        
        age = (datetime.utcnow() - timestamp).total_seconds()
        return age < self.permission_cache_ttl
    
    async def invalidate_user_permissions(self, user_id: str):
        """
        Invalidate cached permissions for a user.
        
        Args:
            user_id: User identifier
        """
        cache_key = f"user_perms:{user_id}"
        if cache_key in self.permission_cache:
            del self.permission_cache[cache_key]
            self.logger.info(f"Invalidated permissions cache for user: {user_id}")
    
    async def add_admin_user(self, user_id: str):
        """
        Add a user to the admin list.
        
        Args:
            user_id: User identifier
        """
        self.admin_users.add(user_id)
        await self.invalidate_user_permissions(user_id)
        self.logger.info(f"Added admin user: {user_id}")
    
    async def remove_admin_user(self, user_id: str):
        """
        Remove a user from the admin list.
        
        Args:
            user_id: User identifier
        """
        self.admin_users.discard(user_id)
        await self.invalidate_user_permissions(user_id)
        self.logger.info(f"Removed admin user: {user_id}")

