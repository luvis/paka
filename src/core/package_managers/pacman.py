#!/usr/bin/env python3
"""
Pacman Package Manager Implementation
"""

from typing import Dict, List, Any
from .base import BasePackageManager, PackageResult


class PacmanManager(BasePackageManager):
    """Pacman package manager implementation"""
    
    def install(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Install packages using Pacman"""
        args = ['-S', '--noconfirm'] + packages
        
        if options.get('dry_run'):
            args.insert(1, '--print-uris')
        
        try:
            result = self._run_command(args)
            if result.returncode == 0:
                return PackageResult(
                    success=True,
                    details={'output': result.stdout}
                )
            else:
                return PackageResult(
                    success=False,
                    error=result.stderr
                )
        except Exception as e:
            return PackageResult(
                success=False,
                error=str(e)
            )
    
    def remove(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Remove packages using Pacman"""
        args = ['-R', '--noconfirm'] + packages
        
        if options.get('dry_run'):
            args.insert(1, '--print-uris')
        
        try:
            result = self._run_command(args)
            if result.returncode == 0:
                return PackageResult(
                    success=True,
                    details={'output': result.stdout}
                )
            else:
                return PackageResult(
                    success=False,
                    error=result.stderr
                )
        except Exception as e:
            return PackageResult(
                success=False,
                error=str(e)
            )
    
    def purge(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Purge packages using Pacman"""
        args = ['-Rns', '--noconfirm'] + packages
        
        if options.get('dry_run'):
            args.insert(1, '--print-uris')
        
        try:
            result = self._run_command(args)
            if result.returncode == 0:
                return PackageResult(
                    success=True,
                    details={'output': result.stdout}
                )
            else:
                return PackageResult(
                    success=False,
                    error=result.stderr
                )
        except Exception as e:
            return PackageResult(
                success=False,
                error=str(e)
            )
    
    def update(self, options: Dict[str, Any]) -> PackageResult:
        """Update package lists using Pacman"""
        try:
            result = self._run_command(['-Sy'])
            return PackageResult(
                success=True,
                details={'output': result.stdout}
            )
        except Exception as e:
            return PackageResult(
                success=False,
                error=str(e)
            )
    
    def upgrade(self, options: Dict[str, Any]) -> PackageResult:
        """Upgrade packages using Pacman"""
        args = ['-Syu', '--noconfirm']
        
        if options.get('dry_run'):
            args.insert(1, '--print-uris')
        
        try:
            result = self._run_command(args)
            if result.returncode == 0:
                return PackageResult(
                    success=True,
                    details={'output': result.stdout}
                )
            else:
                return PackageResult(
                    success=False,
                    error=result.stderr
                )
        except Exception as e:
            return PackageResult(
                success=False,
                error=str(e)
            )
    
    def search(self, query: str, options: Dict[str, Any]) -> PackageResult:
        """Search for packages using Pacman"""
        try:
            result = self._run_command(['-Ss', query])
            if result.returncode == 0:
                packages = self._parse_pacman_search_output(result.stdout)
                return PackageResult(
                    success=True,
                    packages=packages,
                    details={'output': result.stdout}
                )
            else:
                return PackageResult(
                    success=False,
                    error=result.stderr
                )
        except Exception as e:
            return PackageResult(
                success=False,
                error=str(e)
            )
    
    def _parse_pacman_search_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse Pacman search output"""
        packages = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip() and line.startswith('extra/') or line.startswith('community/') or line.startswith('core/'):
                parts = line.split()
                if len(parts) >= 2:
                    repo_name = parts[0]
                    name_version = parts[1]
                    description = ' '.join(parts[2:]) if len(parts) > 2 else ''
                    
                    # Extract name and version
                    if '/' in name_version:
                        name = name_version.split('/')[1]
                    else:
                        name = name_version
                    
                    # Extract version if present
                    version = ''
                    if ' ' in name:
                        name_parts = name.split()
                        name = name_parts[0]
                        version = name_parts[1] if len(name_parts) > 1 else ''
                    
                    packages.append({
                        'name': name,
                        'version': version,
                        'description': description,
                        'manager': 'pacman',
                        'repository': repo_name
                    })
        
        return packages 