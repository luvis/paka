#!/usr/bin/env python3
"""
Docker Package Manager for PAKA

Treats Docker containers as packages, allowing users to search, install, and manage
Docker containers through PAKA's unified interface.
"""

import subprocess
import json
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.core.advanced_plugins.base import BasePackageManager


class DockerPackageManager(BasePackageManager):
    """Docker container package manager"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.docker_command = 'docker'
        self.registries = config.get('registries', ['docker.io'])
        self.installed_containers = set()
        self._load_installed_containers()
    
    def initialize(self) -> bool:
        """Initialize the Docker package manager"""
        if not self._is_docker_available():
            self.logger.warning("Docker not available")
            return False
        
        try:
            # Test Docker connection
            result = subprocess.run([self.docker_command, 'version'], 
                                  capture_output=True, text=True, check=True)
            self.logger.info("Docker package manager initialized successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to initialize Docker: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        pass
    
    def search(self, query: str, options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for Docker containers"""
        if not self._is_docker_available():
            return []
        
        options = options or {}
        results = []
        
        # Search Docker Hub
        try:
            result = subprocess.run([
                self.docker_command, 'search', query, '--format', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            container_info = json.loads(line)
                            results.append({
                                'name': container_info.get('Name', ''),
                                'description': container_info.get('Description', ''),
                                'stars': container_info.get('StarCount', 0),
                                'official': container_info.get('IsOfficial', False),
                                'automated': container_info.get('IsAutomated', False),
                                'manager': 'docker',
                                'version': 'latest',
                                'size': 'Unknown',
                                'installed': container_info.get('Name', '') in self.installed_containers
                            })
                        except json.JSONDecodeError:
                            continue
        except subprocess.TimeoutExpired:
            self.logger.warning("Docker search timed out")
        except Exception as e:
            self.logger.error(f"Error searching Docker: {e}")
        
        return results
    
    def install(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> bool:
        """Install Docker containers"""
        if not self._is_docker_available():
            return False
        
        options = options or {}
        success = True
        
        for package in packages:
            try:
                # Pull the container
                self.logger.info(f"Pulling Docker container: {package}")
                result = subprocess.run([
                    self.docker_command, 'pull', package
                ], capture_output=True, text=True, check=True)
                
                # Update installed containers list
                self.installed_containers.add(package)
                self._save_installed_containers()
                
                self.logger.info(f"Successfully installed Docker container: {package}")
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to install Docker container {package}: {e.stderr}")
                success = False
        
        return success
    
    def remove(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> bool:
        """Remove Docker containers"""
        if not self._is_docker_available():
            return False
        
        options = options or {}
        success = True
        
        for package in packages:
            try:
                # Remove the container image
                self.logger.info(f"Removing Docker container: {package}")
                result = subprocess.run([
                    self.docker_command, 'rmi', package
                ], capture_output=True, text=True, check=True)
                
                # Update installed containers list
                if package in self.installed_containers:
                    self.installed_containers.remove(package)
                    self._save_installed_containers()
                
                self.logger.info(f"Successfully removed Docker container: {package}")
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to remove Docker container {package}: {e.stderr}")
                success = False
        
        return success
    
    def update(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Update Docker container lists (no-op for Docker)"""
        return True
    
    def upgrade(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Upgrade installed Docker containers"""
        if not self._is_docker_available():
            return False
        
        options = options or {}
        success = True
        
        for container in list(self.installed_containers):
            try:
                # Pull latest version
                self.logger.info(f"Upgrading Docker container: {container}")
                result = subprocess.run([
                    self.docker_command, 'pull', container
                ], capture_output=True, text=True, check=True)
                
                self.logger.info(f"Successfully upgraded Docker container: {container}")
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to upgrade Docker container {container}: {e.stderr}")
                success = False
        
        return success
    
    def list_installed(self, options: Optional[Dict[str, Any]] = None) -> List[str]:
        """List installed Docker containers"""
        return list(self.installed_containers)
    
    def get_package_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a Docker container"""
        if not self._is_docker_available():
            return None
        
        try:
            # Get container information
            result = subprocess.run([
                self.docker_command, 'inspect', package_name
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                container_data = json.loads(result.stdout)
                if container_data:
                    info = container_data[0]
                    return {
                        'name': package_name,
                        'id': info.get('Id', ''),
                        'created': info.get('Created', ''),
                        'size': info.get('Size', 0),
                        'architecture': info.get('Architecture', ''),
                        'os': info.get('Os', ''),
                        'tags': info.get('RepoTags', []),
                        'manager': 'docker'
                    }
        except Exception as e:
            self.logger.error(f"Error getting package info for {package_name}: {e}")
        
        return None
    
    def check_updates(self) -> List[Dict[str, Any]]:
        """Check for available updates to Docker containers"""
        if not self._is_docker_available():
            return []
        
        updates = []
        
        for container in self.installed_containers:
            try:
                # Check if there's a newer version available
                result = subprocess.run([
                    self.docker_command, 'pull', container
                ], capture_output=True, text=True)
                
                if "Image is up to date" not in result.stdout:
                    updates.append({
                        'name': container,
                        'current_version': 'latest',
                        'available_version': 'latest',
                        'manager': 'docker'
                    })
            except Exception as e:
                self.logger.error(f"Error checking updates for {container}: {e}")
        
        return updates
    
    def _is_docker_available(self) -> bool:
        """Check if Docker is available on the system"""
        return shutil.which(self.docker_command) is not None
    
    def _load_installed_containers(self):
        """Load list of installed containers from storage"""
        try:
            storage_file = Path.home() / '.local/share/paka/docker_containers.json'
            if storage_file.exists():
                with open(storage_file, 'r') as f:
                    data = json.load(f)
                    self.installed_containers = set(data.get('containers', []))
        except Exception as e:
            self.logger.error(f"Error loading installed containers: {e}")
            self.installed_containers = set()
    
    def _save_installed_containers(self):
        """Save list of installed containers to storage"""
        try:
            storage_file = Path.home() / '.local/share/paka/docker_containers.json'
            storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(storage_file, 'w') as f:
                json.dump({
                    'containers': list(self.installed_containers)
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving installed containers: {e}")


def register_handlers(plugin):
    """Register event handlers for this plugin"""
    # This plugin doesn't need event handlers as it's a package manager
    pass 