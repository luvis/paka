#!/usr/bin/env python3
"""
Package Manager Registry Module

This module provides backward compatibility by importing from the new
modular package manager structure.
"""

from .package_managers.base import BasePackageManager, PackageResult
from .package_managers.registry import PackageManagerRegistry

__all__ = ['BasePackageManager', 'PackageResult', 'PackageManagerRegistry'] 