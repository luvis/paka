"""
Base classes for advanced PAKA plugins
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import logging


class BasePlugin(ABC):
    """Base class for all advanced PAKA plugins"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"paka.plugin.{name}")
        self.enabled = config.get('enabled', False)
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup plugin resources"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'type': self.__class__.__name__,
            'description': self.config.get('description', ''),
            'version': self.config.get('version', '1.0.0')
        }


class BasePackageManager(BasePlugin):
    """Base class for custom package managers"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.package_cache = {}
        self.installed_packages = set()
        self.repositories = config.get('repositories', {})
    
    @abstractmethod
    def search(self, query: str, options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for packages"""
        pass
    
    @abstractmethod
    def install(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> bool:
        """Install packages"""
        pass
    
    @abstractmethod
    def remove(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> bool:
        """Remove packages"""
        pass
    
    @abstractmethod
    def update(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Update package lists"""
        pass
    
    @abstractmethod
    def upgrade(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Upgrade installed packages"""
        pass
    
    @abstractmethod
    def list_installed(self, options: Optional[Dict[str, Any]] = None) -> List[str]:
        """List installed packages"""
        pass
    
    def get_package_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a package"""
        return None
    
    def check_updates(self) -> List[Dict[str, Any]]:
        """Check for available updates"""
        return []
    
    def add_repository(self, name: str, url: str, **kwargs) -> bool:
        """Add a new repository"""
        self.repositories[name] = {
            'url': url,
            'enabled': True,
            **kwargs
        }
        return True
    
    def remove_repository(self, name: str) -> bool:
        """Remove a repository"""
        if name in self.repositories:
            del self.repositories[name]
            return True
        return False
    
    def list_repositories(self) -> Dict[str, Dict[str, Any]]:
        """List all repositories"""
        return self.repositories.copy()


class BaseRepositoryManager(BasePlugin):
    """Base class for repository managers"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.package_manager = config.get('package_manager', 'unknown')
        self.repositories = {}
        self.gpg_keys = {}
    
    @abstractmethod
    def add_repository(self, name: str, url: str, **kwargs) -> bool:
        """Add a new repository"""
        pass
    
    @abstractmethod
    def remove_repository(self, name: str) -> bool:
        """Remove a repository"""
        pass
    
    @abstractmethod
    def enable_repository(self, name: str) -> bool:
        """Enable a repository"""
        pass
    
    @abstractmethod
    def disable_repository(self, name: str) -> bool:
        """Disable a repository"""
        pass
    
    @abstractmethod
    def list_repositories(self) -> List[Dict[str, Any]]:
        """List all repositories"""
        pass
    
    @abstractmethod
    def import_gpg_key(self, key_url: str, key_id: Optional[str] = None) -> bool:
        """Import a GPG key"""
        pass
    
    @abstractmethod
    def remove_gpg_key(self, key_id: str) -> bool:
        """Remove a GPG key"""
        pass
    
    def validate_repository(self, url: str) -> Tuple[bool, str]:
        """Validate a repository URL"""
        # Default implementation - override in subclasses
        return True, "Repository appears valid"
    
    def test_repository(self, name: str) -> Tuple[bool, str]:
        """Test if a repository is working"""
        # Default implementation - override in subclasses
        return True, "Repository is accessible" 