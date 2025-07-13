#!/usr/bin/env python3
"""
APT Package Manager Implementation
"""

from typing import Dict, List, Any
from .base import BasePackageManager, PackageResult


class APTManager(BasePackageManager):
    """APT package manager implementation"""
    
    def install(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Install packages using APT"""
        args = ['install', '-y'] + packages
        
        if options.get('dry_run'):
            args.insert(1, '--dry-run')
        
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
        """Remove packages using APT"""
        args = ['remove', '-y'] + packages
        
        if options.get('dry_run'):
            args.insert(1, '--dry-run')
        
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
        """Purge packages using APT"""
        args = ['purge', '-y'] + packages
        
        if options.get('dry_run'):
            args.insert(1, '--dry-run')
        
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
        """Update package lists using APT"""
        try:
            result = self._run_command(['update'])
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
        """Upgrade packages using APT"""
        args = ['upgrade', '-y']
        
        if options.get('dry_run'):
            args.insert(1, '--dry-run')
        
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
        """Search for packages using APT"""
        try:
            result = self._run_command(['search', query])
            if result.returncode == 0:
                packages = self._parse_apt_search_output(result.stdout)
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
    
    def _parse_apt_search_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse APT search output"""
        packages = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip() and '/' in line:
                parts = line.split('/', 1)
                if len(parts) == 2:
                    name_version = parts[0].strip()
                    description = parts[1].strip()
                    
                    # Extract name and version
                    name_parts = name_version.split()
                    name = name_parts[0] if name_parts else ''
                    version = name_parts[1] if len(name_parts) > 1 else ''
                    
                    packages.append({
                        'name': name,
                        'version': version,
                        'description': description,
                        'manager': 'apt'
                    })
        
        return packages 