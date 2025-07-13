#!/usr/bin/env python3
"""
Flatpak Package Manager Implementation
"""

from typing import Dict, List, Any
from .base import BasePackageManager, PackageResult


class FlatpakManager(BasePackageManager):
    """Flatpak package manager implementation"""
    
    def install(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Install packages using Flatpak"""
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
        """Remove packages using Flatpak"""
        args = ['uninstall', '-y'] + packages
        
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
        """Purge packages using Flatpak (same as remove)"""
        return self.remove(packages, options)
    
    def update(self, options: Dict[str, Any]) -> PackageResult:
        """Update package lists using Flatpak"""
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
        """Upgrade packages using Flatpak"""
        args = ['update', '-y']
        
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
        """Search for packages using Flatpak"""
        try:
            result = self._run_command(['search', query])
            if result.returncode == 0:
                packages = self._parse_flatpak_search_output(result.stdout)
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
    
    def _parse_flatpak_search_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse Flatpak search output"""
        packages = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip() and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 3:
                    name = parts[0].strip()
                    version = parts[1].strip()
                    description = parts[2].strip()
                    
                    packages.append({
                        'name': name,
                        'version': version,
                        'description': description,
                        'manager': 'flatpak'
                    })
        
        return packages 