"""
Repository Manager for PAKA

Handles repository management for different package managers including
PPA management, DNF repositories, and Pacman repositories with GPG key handling.
"""

import os
import subprocess
import requests
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re
import json

from .base import BaseRepositoryManager


class RepositoryManager(BaseRepositoryManager):
    """Unified repository manager for multiple package managers"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # Package manager specific handlers
        self.handlers = {
            'apt': APTRepositoryHandler(),
            'dnf': DNFRepositoryHandler(),
            'pacman': PacmanRepositoryHandler(),
            'zypper': ZypperRepositoryHandler()
        }
        
        # Load existing repositories
        self._load_repositories()
    
    def initialize(self) -> bool:
        """Initialize the repository manager"""
        try:
            # Detect available package managers
            self._detect_package_managers()
            self.logger.info("Repository manager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize repository manager: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        self._save_repositories()
    
    def add_repository(self, name: str, url: str, **kwargs) -> bool:
        """Add a new repository"""
        package_manager = kwargs.get('package_manager', 'auto')
        
        if package_manager == 'auto':
            package_manager = self._detect_package_manager_from_url(url)
        
        if package_manager not in self.handlers:
            self.logger.error(f"Unsupported package manager: {package_manager}")
            return False
        
        try:
            handler = self.handlers[package_manager]
            
            # Validate repository
            is_valid, message = self.validate_repository(url)
            if not is_valid:
                self.logger.error(f"Invalid repository: {message}")
                return False
            
            # Add repository using appropriate handler
            success = handler.add_repository(name, url, **kwargs)
            
            if success:
                # Store repository info
                self.repositories[name] = {
                    'name': name,
                    'url': url,
                    'package_manager': package_manager,
                    'enabled': True,
                    'added_by': 'paka',
                    **kwargs
                }
                
                self.logger.info(f"Added {package_manager} repository: {name}")
                return True
            else:
                self.logger.error(f"Failed to add repository: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding repository {name}: {e}")
            return False
    
    def remove_repository(self, name: str) -> bool:
        """Remove a repository"""
        if name not in self.repositories:
            self.logger.error(f"Repository not found: {name}")
            return False
        
        repo_info = self.repositories[name]
        package_manager = repo_info['package_manager']
        
        if package_manager not in self.handlers:
            self.logger.error(f"Unsupported package manager: {package_manager}")
            return False
        
        try:
            handler = self.handlers[package_manager]
            success = handler.remove_repository(name, repo_info)
            
            if success:
                del self.repositories[name]
                self.logger.info(f"Removed repository: {name}")
                return True
            else:
                self.logger.error(f"Failed to remove repository: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing repository {name}: {e}")
            return False
    
    def enable_repository(self, name: str) -> bool:
        """Enable a repository"""
        if name not in self.repositories:
            self.logger.error(f"Repository not found: {name}")
            return False
        
        repo_info = self.repositories[name]
        package_manager = repo_info['package_manager']
        
        if package_manager not in self.handlers:
            self.logger.error(f"Unsupported package manager: {package_manager}")
            return False
        
        try:
            handler = self.handlers[package_manager]
            success = handler.enable_repository(name, repo_info)
            
            if success:
                self.repositories[name]['enabled'] = True
                self.logger.info(f"Enabled repository: {name}")
                return True
            else:
                self.logger.error(f"Failed to enable repository: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enabling repository {name}: {e}")
            return False
    
    def disable_repository(self, name: str) -> bool:
        """Disable a repository"""
        if name not in self.repositories:
            self.logger.error(f"Repository not found: {name}")
            return False
        
        repo_info = self.repositories[name]
        package_manager = repo_info['package_manager']
        
        if package_manager not in self.handlers:
            self.logger.error(f"Unsupported package manager: {package_manager}")
            return False
        
        try:
            handler = self.handlers[package_manager]
            success = handler.disable_repository(name, repo_info)
            
            if success:
                self.repositories[name]['enabled'] = False
                self.logger.info(f"Disabled repository: {name}")
                return True
            else:
                self.logger.error(f"Failed to disable repository: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error disabling repository {name}: {e}")
            return False
    
    def list_repositories(self) -> List[Dict[str, Any]]:
        """List all repositories"""
        return list(self.repositories.values())
    
    def import_gpg_key(self, key_url: str, key_id: Optional[str] = None) -> bool:
        """Import a GPG key"""
        try:
            # Download the key
            response = requests.get(key_url, timeout=10)
            response.raise_for_status()
            
            key_data = response.content
            
            # Try to import to all available package managers
            success = False
            
            for package_manager, handler in self.handlers.items():
                if hasattr(handler, 'import_gpg_key'):
                    try:
                        if handler.import_gpg_key(key_data, key_id):
                            self.logger.info(f"Imported GPG key to {package_manager}")
                            success = True
                    except Exception as e:
                        self.logger.warning(f"Failed to import GPG key to {package_manager}: {e}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error importing GPG key: {e}")
            return False
    
    def remove_gpg_key(self, key_id: str) -> bool:
        """Remove a GPG key"""
        success = False
        
        for package_manager, handler in self.handlers.items():
            if hasattr(handler, 'remove_gpg_key'):
                try:
                    if handler.remove_gpg_key(key_id):
                        self.logger.info(f"Removed GPG key from {package_manager}")
                        success = True
                except Exception as e:
                    self.logger.warning(f"Failed to remove GPG key from {package_manager}: {e}")
        
        return success
    
    def validate_repository(self, url: str) -> Tuple[bool, str]:
        """Validate a repository URL"""
        try:
            # Basic URL validation
            if not url.startswith(('http://', 'https://', 'ppa:', 'deb ')):
                return False, "Invalid URL format"
            
            # Try to access the repository
            if url.startswith('http'):
                response = requests.head(url, timeout=5)
                if response.status_code != 200:
                    return False, f"Repository not accessible (HTTP {response.status_code})"
            
            return True, "Repository appears valid"
            
        except Exception as e:
            return False, f"Validation failed: {e}"
    
    def test_repository(self, name: str) -> Tuple[bool, str]:
        """Test if a repository is working"""
        if name not in self.repositories:
            return False, "Repository not found"
        
        repo_info = self.repositories[name]
        package_manager = repo_info['package_manager']
        
        if package_manager not in self.handlers:
            return False, f"Unsupported package manager: {package_manager}"
        
        try:
            handler = self.handlers[package_manager]
            if hasattr(handler, 'test_repository'):
                return handler.test_repository(name, repo_info)
            else:
                return True, "Repository testing not implemented for this package manager"
                
        except Exception as e:
            return False, f"Test failed: {e}"
    
    def _detect_package_manager_from_url(self, url: str) -> str:
        """Detect package manager from repository URL"""
        if url.startswith('ppa:'):
            return 'apt'
        elif url.startswith('deb '):
            return 'apt'
        elif url.endswith('.repo'):
            return 'dnf'
        elif 'rpm' in url.lower():
            return 'dnf'
        elif 'pacman' in url.lower() or 'arch' in url.lower():
            return 'pacman'
        elif 'zypper' in url.lower() or 'suse' in url.lower():
            return 'zypper'
        else:
            # Default to apt for unknown URLs
            return 'apt'
    
    def _detect_package_managers(self):
        """Detect available package managers on the system"""
        available_managers = []
        
        for manager, handler in self.handlers.items():
            if handler.is_available():
                available_managers.append(manager)
                self.logger.info(f"Detected package manager: {manager}")
        
        return available_managers
    
    def _load_repositories(self):
        """Load repository information from disk"""
        # This could load from a configuration file
        pass
    
    def _save_repositories(self):
        """Save repository information to disk"""
        # This could save to a configuration file
        pass


class APTRepositoryHandler:
    """Handler for APT repositories (PPAs, deb repositories)"""
    
    def is_available(self) -> bool:
        """Check if APT is available"""
        return shutil.which('apt') is not None
    
    def add_repository(self, name: str, url: str, **kwargs) -> bool:
        """Add APT repository"""
        try:
            if url.startswith('ppa:'):
                # Handle PPA
                cmd = ['add-apt-repository', url]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Update package lists
                subprocess.run(['apt', 'update'], check=True)
                return True
                
            elif url.startswith('deb '):
                # Handle deb repository
                sources_file = Path('/etc/apt/sources.list.d') / f"{name}.list"
                
                with open(sources_file, 'w') as f:
                    f.write(f"{url}\n")
                
                # Update package lists
                subprocess.run(['apt', 'update'], check=True)
                return True
                
            else:
                # Handle regular repository
                cmd = ['add-apt-repository', url]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Update package lists
                subprocess.run(['apt', 'update'], check=True)
                return True
                
        except subprocess.CalledProcessError as e:
            print(f"Error adding APT repository: {e}")
            return False
    
    def remove_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Remove APT repository"""
        try:
            url = repo_info['url']
            
            if url.startswith('ppa:'):
                # Remove PPA
                cmd = ['add-apt-repository', '--remove', url]
                subprocess.run(cmd, check=True)
                
            else:
                # Remove from sources.list.d
                sources_file = Path('/etc/apt/sources.list.d') / f"{name}.list"
                if sources_file.exists():
                    sources_file.unlink()
            
            # Update package lists
            subprocess.run(['apt', 'update'], check=True)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error removing APT repository: {e}")
            return False
    
    def enable_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Enable APT repository"""
        # APT repositories are enabled by default when added
        return True
    
    def disable_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Disable APT repository"""
        try:
            # Rename the sources file to disable it
            sources_file = Path('/etc/apt/sources.list.d') / f"{name}.list"
            disabled_file = Path('/etc/apt/sources.list.d') / f"{name}.list.disabled"
            
            if sources_file.exists():
                sources_file.rename(disabled_file)
                subprocess.run(['apt', 'update'], check=True)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error disabling APT repository: {e}")
            return False
    
    def import_gpg_key(self, key_data: bytes, key_id: Optional[str] = None) -> bool:
        """Import GPG key for APT"""
        try:
            # Write key to temporary file
            key_file = Path('/tmp/paka_gpg_key.asc')
            with open(key_file, 'wb') as f:
                f.write(key_data)
            
            # Import key
            subprocess.run(['apt-key', 'add', str(key_file)], check=True)
            
            # Clean up
            key_file.unlink()
            return True
            
        except Exception as e:
            print(f"Error importing GPG key for APT: {e}")
            return False
    
    def remove_gpg_key(self, key_id: str) -> bool:
        """Remove GPG key for APT"""
        try:
            subprocess.run(['apt-key', 'del', key_id], check=True)
            return True
        except Exception as e:
            print(f"Error removing GPG key for APT: {e}")
            return False


class DNFRepositoryHandler:
    """Handler for DNF repositories"""
    
    def is_available(self) -> bool:
        """Check if DNF is available"""
        return shutil.which('dnf') is not None
    
    def add_repository(self, name: str, url: str, **kwargs) -> bool:
        """Add DNF repository"""
        try:
            # Add repository
            cmd = ['dnf', 'config-manager', '--add-repo', url]
            subprocess.run(cmd, check=True)
            
            # Import GPG key if provided
            gpg_key = kwargs.get('gpg_key')
            if gpg_key:
                subprocess.run(['rpm', '--import', gpg_key], check=True)
            
            # Update package lists
            subprocess.run(['dnf', 'makecache'], check=True)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error adding DNF repository: {e}")
            return False
    
    def remove_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Remove DNF repository"""
        try:
            # Remove repository file
            repo_file = Path('/etc/yum.repos.d') / f"{name}.repo"
            if repo_file.exists():
                repo_file.unlink()
            
            # Update package lists
            subprocess.run(['dnf', 'makecache'], check=True)
            return True
            
        except Exception as e:
            print(f"Error removing DNF repository: {e}")
            return False
    
    def enable_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Enable DNF repository"""
        try:
            subprocess.run(['dnf', 'config-manager', '--enable', name], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error enabling DNF repository: {e}")
            return False
    
    def disable_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Disable DNF repository"""
        try:
            subprocess.run(['dnf', 'config-manager', '--disable', name], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error disabling DNF repository: {e}")
            return False


class PacmanRepositoryHandler:
    """Handler for Pacman repositories"""
    
    def is_available(self) -> bool:
        """Check if Pacman is available"""
        return shutil.which('pacman') is not None
    
    def add_repository(self, name: str, url: str, **kwargs) -> bool:
        """Add Pacman repository"""
        try:
            # Add to pacman.conf
            pacman_conf = Path('/etc/pacman.conf')
            
            with open(pacman_conf, 'r') as f:
                content = f.read()
            
            # Add repository section
            repo_section = f"\n[{name}]\nServer = {url}\n"
            content += repo_section
            
            with open(pacman_conf, 'w') as f:
                f.write(content)
            
            # Import GPG key if provided
            gpg_key = kwargs.get('gpg_key')
            if gpg_key:
                subprocess.run(['pacman-key', '--add', gpg_key], check=True)
                subprocess.run(['pacman-key', '--lsign-key', gpg_key], check=True)
            
            # Update package database
            subprocess.run(['pacman', '-Sy'], check=True)
            return True
            
        except Exception as e:
            print(f"Error adding Pacman repository: {e}")
            return False
    
    def remove_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Remove Pacman repository"""
        try:
            # Remove from pacman.conf
            pacman_conf = Path('/etc/pacman.conf')
            
            with open(pacman_conf, 'r') as f:
                lines = f.readlines()
            
            # Remove repository section
            new_lines = []
            skip_section = False
            
            for line in lines:
                if line.strip() == f'[{name}]':
                    skip_section = True
                    continue
                elif line.startswith('[') and skip_section:
                    skip_section = False
                    new_lines.append(line)
                elif not skip_section:
                    new_lines.append(line)
            
            with open(pacman_conf, 'w') as f:
                f.writelines(new_lines)
            
            # Update package database
            subprocess.run(['pacman', '-Sy'], check=True)
            return True
            
        except Exception as e:
            print(f"Error removing Pacman repository: {e}")
            return False
    
    def enable_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Enable Pacman repository"""
        # Pacman repositories are enabled by default when added
        return True
    
    def disable_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Disable Pacman repository"""
        # Same as remove for Pacman
        return self.remove_repository(name, repo_info)


class ZypperRepositoryHandler:
    """Handler for Zypper repositories"""
    
    def is_available(self) -> bool:
        """Check if Zypper is available"""
        return shutil.which('zypper') is not None
    
    def add_repository(self, name: str, url: str, **kwargs) -> bool:
        """Add Zypper repository"""
        try:
            cmd = ['zypper', 'addrepo', url, name]
            subprocess.run(cmd, check=True)
            
            # Refresh repositories
            subprocess.run(['zypper', 'refresh'], check=True)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error adding Zypper repository: {e}")
            return False
    
    def remove_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Remove Zypper repository"""
        try:
            cmd = ['zypper', 'removerepo', name]
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error removing Zypper repository: {e}")
            return False
    
    def enable_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Enable Zypper repository"""
        try:
            cmd = ['zypper', 'modifyrepo', '--enable', name]
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error enabling Zypper repository: {e}")
            return False
    
    def disable_repository(self, name: str, repo_info: Dict[str, Any]) -> bool:
        """Disable Zypper repository"""
        try:
            cmd = ['zypper', 'modifyrepo', '--disable', name]
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error disabling Zypper repository: {e}")
            return False 