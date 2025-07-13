#!/usr/bin/env python3
"""
Package Manager Registry

This module provides a registry of available package managers and handles
loading and managing them.
"""

from .registry import PackageManagerRegistry
from .base import BasePackageManager
from .dnf import DNFManager
from .apt import APTManager
from .pacman import PacmanManager
from .flatpak import FlatpakManager
from .snap import SnapManager

# Advanced plugin system
from ..advanced_plugins import AppImagePackageManager, RepositoryManager

__all__ = [
    'PackageManagerRegistry',
    'BasePackageManager',
    'DNFManager',
    'APTManager',
    'PacmanManager',
    'FlatpakManager',
    'SnapManager',
    'AppImagePackageManager',
    'RepositoryManager'
] 