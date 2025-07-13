#!/usr/bin/env python3
"""
Base Package Manager Module

Defines the base class and common functionality for all package managers.
"""

import logging
import subprocess
import shutil
from typing import Dict, List, Any, Optional, NamedTuple
from abc import ABC, abstractmethod


class PackageResult(NamedTuple):
    """Result of a package manager operation"""
    success: bool
    error: Optional[str] = None
    packages: Optional[List[Dict[str, Any]]] = None
    details: Optional[Dict[str, Any]] = None


class BasePackageManager(ABC):
    """Base class for package managers"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize package manager"""
        self.name = name
        self.config = config
        self.command = config.get('command', name)
        self.enabled = config.get('enabled', True)
        self.logger = logging.getLogger(f"paka.{name}")
    
    def is_enabled(self) -> bool:
        """Check if package manager is enabled"""
        return self.enabled and shutil.which(self.command) is not None
    
    def is_available(self) -> bool:
        """Check if package manager is available on system"""
        return shutil.which(self.command) is not None
    
    @abstractmethod
    def install(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Install packages"""
        pass
    
    @abstractmethod
    def remove(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Remove packages"""
        pass
    
    @abstractmethod
    def purge(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Purge packages and configuration"""
        pass
    
    @abstractmethod
    def update(self, options: Dict[str, Any]) -> PackageResult:
        """Update package lists"""
        pass
    
    @abstractmethod
    def upgrade(self, options: Dict[str, Any]) -> PackageResult:
        """Upgrade packages"""
        pass
    
    @abstractmethod
    def search(self, query: str, options: Dict[str, Any]) -> PackageResult:
        """Search for packages"""
        pass
    
    def _run_command(self, args: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result"""
        try:
            return subprocess.run(
                [self.command] + args,
                capture_output=capture_output,
                text=True,
                timeout=300  # 5 minute timeout
            )
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {self.command} {' '.join(args)}")
            raise
        except Exception as e:
            self.logger.error(f"Command failed: {self.command} {' '.join(args)} - {e}")
            raise 