#!/usr/bin/env python3
"""
Package Manager Registry Module

Manages different package managers and provides unified interface.
"""

import logging
from typing import Dict, List, Any, Optional
from .base import BasePackageManager
from .dnf import DNFManager
from .apt import APTManager
from .pacman import PacmanManager
from .flatpak import FlatpakManager
from .snap import SnapManager

# Advanced plugin system
try:
    from ..advanced_plugins import AppImagePackageManager
    APPIMAGE_AVAILABLE = True
except ImportError:
    APPIMAGE_AVAILABLE = False

try:
    from ..advanced_plugins import DockerPackageManager
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

from ..config import ConfigManager


class PackageManagerRegistry:
    """Registry for package managers"""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize package manager registry"""
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.managers: Dict[str, BasePackageManager] = {}
        self._load_managers()
    
    def _load_managers(self):
        """Load all package managers"""
        config = self.config_manager.load_config()
        managers_config = config.get('package_managers', {})
        
        # Define manager classes (only the ones we've created)
        manager_classes = {
            'dnf': DNFManager,
            'apt': APTManager,
            'pacman': PacmanManager,
            'flatpak': FlatpakManager,
            'snap': SnapManager,
        }
        
        # Add AppImage manager if available
        if APPIMAGE_AVAILABLE:
            manager_classes['appimage'] = AppImagePackageManager
        
        # Add Docker manager if available
        if DOCKER_AVAILABLE:
            manager_classes['docker'] = DockerPackageManager
        
        # Create manager instances
        for name, manager_class in manager_classes.items():
            if name in managers_config:
                try:
                    self.managers[name] = manager_class(name, managers_config[name])
                    self.logger.debug(f"Loaded package manager: {name}")
                except Exception as e:
                    self.logger.error(f"Failed to load package manager {name}: {e}")
            else:
                # Create with default config
                default_config = {
                    'name': name,
                    'enabled': True,
                    'command': name,
                    'priority': 0
                }
                try:
                    self.managers[name] = manager_class(name, default_config)
                    self.logger.debug(f"Loaded package manager with default config: {name}")
                except Exception as e:
                    self.logger.error(f"Failed to load package manager {name} with default config: {e}")
    
    def get_available_managers(self) -> Dict[str, BasePackageManager]:
        """Get all available package managers"""
        return self.managers
    
    def get_enabled_managers(self) -> Dict[str, BasePackageManager]:
        """Get only enabled package managers"""
        return {name: manager for name, manager in self.managers.items() 
                if manager.is_enabled()}
    
    def get_manager(self, name: str) -> Optional[BasePackageManager]:
        """Get a specific package manager by name"""
        return self.managers.get(name)
    
    def list_managers(self) -> List[Dict[str, Any]]:
        """List all package managers with their status"""
        result = []
        for name, manager in self.managers.items():
            result.append({
                'name': name,
                'enabled': manager.is_enabled(),
                'available': manager.is_available(),
                'command': manager.command
            })
        return result 