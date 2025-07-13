#!/usr/bin/env python3
"""
Snap Package Manager Implementation
"""

from typing import Dict, List, Any
from .base import BasePackageManager, PackageResult


class SnapManager(BasePackageManager):
    """Snap package manager implementation"""
    
    def install(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Install packages using Snap"""
        args = ['install'] + packages
        
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
        """Remove packages using Snap"""
        args = ['remove'] + packages
        
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
        """Purge packages using Snap"""
        args = ['remove', '--purge'] + packages
        
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
        """Update package lists using Snap"""
        try:
            result = self._run_command(['refresh'])
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
        """Upgrade packages using Snap"""
        args = ['refresh']
        
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
        """Search for packages using Snap"""
        try:
            result = self._run_command(['search', query])
            if result.returncode == 0:
                packages = self._parse_snap_search_output(result.stdout)
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
    
    def _parse_snap_search_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse Snap search output"""
        packages = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip() and ' ' in line:
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1] if len(parts) > 1 else ''
                    description = ' '.join(parts[2:]) if len(parts) > 2 else ''
                    
                    packages.append({
                        'name': name,
                        'version': version,
                        'description': description,
                        'manager': 'snap'
                    })
        
        return packages 