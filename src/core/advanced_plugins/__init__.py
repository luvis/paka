"""
Advanced Plugin System for PAKA

This module provides the framework for creating advanced Python-based plugins
that can implement custom package managers, repository managers, and other
complex functionality.
"""

from .base import BasePackageManager, BaseRepositoryManager, BasePlugin
from .appimage_manager import AppImagePackageManager
from .repo_manager import RepositoryManager

# Try to import Docker plugin
try:
    from plugins.paka.docker.docker_manager import DockerPackageManager
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    DockerPackageManager = None

__all__ = [
    'BasePackageManager',
    'BaseRepositoryManager', 
    'BasePlugin',
    'AppImagePackageManager',
    'RepositoryManager',
    'DockerPackageManager'
] 