#!/usr/bin/env python3
"""
Directory Management Module

Implements XDG Base Directory specification and system-wide directory standards for PAKA.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any


class DirectoryManager:
    """Manages PAKA directories according to XDG and system-wide standards"""
    
    def __init__(self):
        """Initialize directory manager"""
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        # Create user directories
        self.get_user_config_dir().mkdir(parents=True, exist_ok=True)
        self.get_user_plugins_dir().mkdir(parents=True, exist_ok=True)
        self.get_user_history_dir().mkdir(parents=True, exist_ok=True)
        self.get_user_log_dir().mkdir(parents=True, exist_ok=True)
        
        # System directories are created by package installation or admin
        # We don't create them here to avoid permission issues
    
    def get_user_config_dir(self) -> Path:
        """Get user configuration directory (XDG compliant)"""
        xdg_config = os.getenv('XDG_CONFIG_HOME')
        if xdg_config:
            return Path(xdg_config) / 'paka'
        else:
            return Path.home() / '.config' / 'paka'
    
    def get_system_config_dir(self) -> Path:
        """Get system configuration directory"""
        return Path('/etc/paka')
    
    def get_user_plugins_dir(self) -> Path:
        """Get user plugins directory (XDG compliant)"""
        xdg_data = os.getenv('XDG_DATA_HOME')
        if xdg_data:
            return Path(xdg_data) / 'paka' / 'plugins'
        else:
            return Path.home() / '.local' / 'share' / 'paka' / 'plugins'
    
    def get_system_plugins_dir(self) -> Path:
        """Get system plugins directory"""
        return Path('/usr/share/paka/plugins')
    
    def get_user_history_dir(self) -> Path:
        """Get user history directory (XDG compliant)"""
        xdg_data = os.getenv('XDG_DATA_HOME')
        if xdg_data:
            return Path(xdg_data) / 'paka'
        else:
            return Path.home() / '.local' / 'share' / 'paka'
    
    def get_system_history_dir(self) -> Path:
        """Get system history directory"""
        return Path('/var/lib/paka')
    
    def get_user_log_dir(self) -> Path:
        """Get user log directory (XDG compliant)"""
        xdg_data = os.getenv('XDG_DATA_HOME')
        if xdg_data:
            return Path(xdg_data) / 'paka' / 'logs'
        else:
            return Path.home() / '.local' / 'share' / 'paka' / 'logs'
    
    def get_system_log_dir(self) -> Path:
        """Get system log directory"""
        return Path('/var/log/paka')
    
    def get_config_file(self, scope: str = 'user') -> Path:
        """Get configuration file path"""
        if scope == 'system':
            return self.get_system_config_dir() / 'config.json'
        else:
            return self.get_user_config_dir() / 'config.json'
    
    def get_history_file(self, scope: str = 'user') -> Path:
        """Get history file path"""
        if scope == 'system':
            return self.get_system_history_dir() / 'history.json'
        else:
            return self.get_user_history_dir() / 'history.json'
    
    def get_session_file(self, scope: str = 'user') -> Path:
        """Get session file path"""
        if scope == 'system':
            return self.get_system_history_dir() / 'session.json'
        else:
            return self.get_user_history_dir() / 'session.json'
    
    def get_plugin_directories(self, scope: str = 'all') -> Dict[str, Path]:
        """Get plugin directories for specified scope"""
        directories = {}
        
        if scope in ['user', 'all']:
            directories['user'] = self.get_user_plugins_dir()
        
        if scope in ['system', 'all']:
            directories['system'] = self.get_system_plugins_dir()
        
        return directories
    
    def get_plugin_path(self, plugin_name: str, scope: str = 'user') -> Path:
        """Get specific plugin directory path"""
        if scope == 'system':
            return self.get_system_plugins_dir() / plugin_name
        else:
            return self.get_user_plugins_dir() / plugin_name
    
    def can_write_to_directory(self, directory: Path) -> bool:
        """Check if current user can write to directory"""
        try:
            # Check if directory exists and is writable
            if directory.exists():
                return os.access(directory, os.W_OK)
            else:
                # Check if parent directory is writable
                return os.access(directory.parent, os.W_OK)
        except Exception:
            return False
    
    def get_effective_config_dir(self) -> Path:
        """Get effective config directory (user if available, system as fallback)"""
        user_config = self.get_user_config_dir()
        system_config = self.get_system_config_dir()
        
        # Prefer user config if it exists or can be created
        if user_config.exists() or self.can_write_to_directory(user_config):
            return user_config
        elif system_config.exists():
            return system_config
        else:
            # Default to user config
            return user_config
    
    def get_effective_plugins_dir(self) -> Path:
        """Get effective plugins directory (user if available, system as fallback)"""
        user_plugins = self.get_user_plugins_dir()
        system_plugins = self.get_system_plugins_dir()
        
        # Prefer user plugins if it exists or can be created
        if user_plugins.exists() or self.can_write_to_directory(user_plugins):
            return user_plugins
        elif system_plugins.exists():
            return system_plugins
        else:
            # Default to user plugins
            return user_plugins
    
    def get_directory_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all PAKA directories"""
        info = {}
        
        # User directories
        user_dirs = {
            'config': self.get_user_config_dir(),
            'plugins': self.get_user_plugins_dir(),
            'history': self.get_user_history_dir(),
            'logs': self.get_user_log_dir()
        }
        
        for name, path in user_dirs.items():
            info[f'user_{name}'] = {
                'path': str(path),
                'exists': path.exists(),
                'writable': self.can_write_to_directory(path),
                'scope': 'user'
            }
        
        # System directories
        system_dirs = {
            'config': self.get_system_config_dir(),
            'plugins': self.get_system_plugins_dir(),
            'history': self.get_system_history_dir(),
            'logs': self.get_system_log_dir()
        }
        
        for name, path in system_dirs.items():
            info[f'system_{name}'] = {
                'path': str(path),
                'exists': path.exists(),
                'writable': self.can_write_to_directory(path),
                'scope': 'system'
            }
        
        return info
    
    def ensure_directory(self, directory: Path) -> bool:
        """Ensure a directory exists, creating it if necessary"""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False 