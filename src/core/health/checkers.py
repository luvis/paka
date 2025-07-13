#!/usr/bin/env python3
"""
Health Checkers Module

Contains all the health check logic for different aspects of the system.
"""

import subprocess
import shutil
import logging
from typing import Dict, List, Any
from pathlib import Path

from .base import HealthCheck
from ..config import ConfigManager


class HealthCheckers:
    """Contains all health check logic"""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize health checkers"""
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def check_package_caches(self) -> List[HealthCheck]:
        """Check package manager caches safely"""
        checks = []
        
        # Check for large package caches across all package managers
        cache_dirs = [
            ('/var/cache/apt', 'apt'),
            ('/var/cache/dnf', 'dnf'),
            ('/var/cache/pacman', 'pacman'),
            ('/var/cache/zypper', 'zypper'),
            ('/var/cache/flatpak', 'flatpak'),
            ('/var/cache/apk', 'apk'),
            ('/var/cache/xbps', 'xbps'),
            ('/var/cache/emerge', 'emerge'),
            ('/var/cache/slackpkg', 'slackpkg'),
            ('/var/cache/nix', 'nix')
        ]
        
        for cache_dir, manager in cache_dirs:
            if Path(cache_dir).exists():
                try:
                    result = subprocess.run(['du', '-sh', cache_dir], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        size_str = result.stdout.split()[0]
                        # Extract size in MB/GB
                        if 'G' in size_str:
                            size_gb = float(size_str.replace('G', ''))
                            if size_gb > 5:  # More than 5GB
                                checks.append(HealthCheck(
                                    name=f"Large {manager} Cache",
                                    status="warning",
                                    message=f"{manager} cache is {size_str}",
                                    fix_command=f"{manager} clean all",
                                    fix_description=f"Clean large {manager} cache"
                                ))
                except Exception:
                    pass
        
        return checks
    
    def check_package_databases(self) -> List[HealthCheck]:
        """Check package manager database health safely"""
        checks = []
        
        # Check for lock files across all package managers
        lock_files = [
            ('/var/lib/dnf/rpmdb_lock', 'DNF'),
            ('/var/lib/pacman/db.lck', 'Pacman'),
            ('/var/lib/apt/lists/lock', 'APT'),
            ('/var/lib/dpkg/lock', 'DPKG'),
            ('/var/lib/dpkg/lock-frontend', 'DPKG'),
            ('/var/lib/zypp/lock', 'Zypper'),
            ('/var/lib/portage/world.lock', 'Portage'),
            ('/var/lib/xbps/.xbps-lock', 'XBPS'),
            ('/var/lib/apk/lock', 'APK'),
            ('/var/lib/flatpak/.lock', 'Flatpak')
        ]
        
        for lock_file, manager in lock_files:
            if Path(lock_file).exists():
                checks.append(HealthCheck(
                    name=f"{manager} Lock File",
                    status="warning",
                    message=f"{manager} lock file exists: {Path(lock_file).name}",
                    fix_command=f"rm -f {lock_file}",
                    fix_description=f"Remove {manager} lock file (package manager may be running)"
                ))
        
        # Check for partial installations
        partial_dirs = [
            ('/var/lib/dnf/transaction', 'DNF'),
            ('/var/lib/apt/lists/partial', 'APT'),
            ('/var/lib/pacman/db.lck', 'Pacman')
        ]
        
        for partial_dir, manager in partial_dirs:
            if Path(partial_dir).exists():
                try:
                    files = list(Path(partial_dir).glob('*'))
                    if files:
                        checks.append(HealthCheck(
                            name=f"{manager} Partial Installation",
                            status="error",
                            message=f"{manager} has incomplete transaction files",
                            fix_command=f"rm -rf {partial_dir}/*",
                            fix_description=f"Clean {manager} partial installation files"
                        ))
                except Exception:
                    pass
        
        return checks
    
    def check_package_managers(self) -> List[HealthCheck]:
        """Check package manager health"""
        checks = []
        config = self.config_manager.load_config()
        
        for manager_name, manager_config in config['package_managers'].items():
            if not manager_config.get('enabled', True):
                continue
            
            command = manager_config.get('command')
            if not command or not shutil.which(command):
                continue  # Skip unavailable package managers
            
            # Check package manager specific health
            checks.extend(self._check_manager_health(manager_name, manager_config))
        
        return checks
    
    def _check_manager_health(self, manager_name: str, config: Dict[str, Any]) -> List[HealthCheck]:
        """Check health of a specific package manager"""
        checks = []
        command = config.get('command')
        
        if not command:
            return checks
        
        # Check all supported package managers for actual problems
        manager_checks = {
            'dnf': self._check_dnf_health,
            'apt': self._check_apt_health,
            'pacman': self._check_pacman_health,
            'flatpak': self._check_flatpak_health,
            'snap': self._check_snap_health,
            'zypper': self._check_zypper_health,
            'emerge': self._check_emerge_health,
            'yay': self._check_yay_health,
            'slackpkg': self._check_slackpkg_health,
            'apk': self._check_apk_health,
            'xbps': self._check_xbps_health,
            'apx': self._check_apx_health,
            'nix': self._check_nix_health,
            'slpkg': self._check_slpkg_health
        }
        
        if manager_name in manager_checks:
            try:
                checks.extend(manager_checks[manager_name](command))
            except Exception as e:
                self.logger.error(f"Error checking {manager_name} health: {e}")
        
        return checks
    
    def _check_dnf_health(self, command: str) -> List[HealthCheck]:
        """Check DNF health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, 'check'], capture_output=True, text=True)
            if result.returncode != 0 and 'broken' in result.stderr.lower():
                checks.append(HealthCheck(
                    name="DNF Broken Packages",
                    status="error",
                    message="DNF has broken packages that need fixing",
                    fix_command="dnf check-update && dnf upgrade",
                    fix_description="Fix broken DNF packages"
                ))
        except Exception:
            pass
        
        # Check for corrupted RPM database
        try:
            result = subprocess.run([command, 'check-update'], capture_output=True, text=True)
            if result.returncode != 0 and 'rpmdb' in result.stderr.lower():
                checks.append(HealthCheck(
                    name="DNF Corrupted Database",
                    status="error",
                    message="DNF RPM database is corrupted",
                    fix_command="dnf clean all && dnf makecache",
                    fix_description="Rebuild DNF database"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_apt_health(self, command: str) -> List[HealthCheck]:
        """Check APT health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, 'check'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="APT Broken Packages",
                    status="error",
                    message="APT has broken packages that need fixing",
                    fix_command="apt --fix-broken install",
                    fix_description="Fix broken APT packages"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_pacman_health(self, command: str) -> List[HealthCheck]:
        """Check Pacman health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, '-Qk'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Pacman Broken Packages",
                    status="error",
                    message="Pacman has broken packages that need fixing",
                    fix_command="pacman -Syu",
                    fix_description="Fix broken Pacman packages"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_flatpak_health(self, command: str) -> List[HealthCheck]:
        """Check Flatpak health"""
        checks = []
        
        # Check for broken installations
        try:
            result = subprocess.run([command, 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Flatpak Broken Installation",
                    status="error",
                    message="Flatpak installation is broken",
                    fix_command="flatpak repair",
                    fix_description="Repair Flatpak installation"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_snap_health(self, command: str) -> List[HealthCheck]:
        """Check Snap health"""
        checks = []
        
        # Check for broken snaps
        try:
            result = subprocess.run([command, 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Snap Broken Installation",
                    status="error",
                    message="Snap installation is broken",
                    fix_command="snap refresh",
                    fix_description="Refresh Snap installation"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_zypper_health(self, command: str) -> List[HealthCheck]:
        """Check Zypper health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, 'verify'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Zypper Broken Packages",
                    status="error",
                    message="Zypper has broken packages that need fixing",
                    fix_command="zypper dup",
                    fix_description="Fix broken Zypper packages"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_emerge_health(self, command: str) -> List[HealthCheck]:
        """Check Emerge health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, '--check-news'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Emerge Broken Packages",
                    status="error",
                    message="Emerge has broken packages that need fixing",
                    fix_command="emerge --sync && emerge -u world",
                    fix_description="Fix broken Emerge packages"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_yay_health(self, command: str) -> List[HealthCheck]:
        """Check Yay health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, '-Q'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Yay Broken Packages",
                    status="error",
                    message="Yay has broken packages that need fixing",
                    fix_command="yay -Syu",
                    fix_description="Fix broken Yay packages"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_slackpkg_health(self, command: str) -> List[HealthCheck]:
        """Check Slackpkg health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, 'check-updates'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Slackpkg Broken Packages",
                    status="error",
                    message="Slackpkg has broken packages that need fixing",
                    fix_command="slackpkg update && slackpkg upgrade-all",
                    fix_description="Fix broken Slackpkg packages"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_apk_health(self, command: str) -> List[HealthCheck]:
        """Check APK health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, 'version'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="APK Broken Packages",
                    status="error",
                    message="APK has broken packages that need fixing",
                    fix_command="apk update && apk upgrade",
                    fix_description="Fix broken APK packages"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_xbps_health(self, command: str) -> List[HealthCheck]:
        """Check XBPS health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, '-S'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="XBPS Broken Packages",
                    status="error",
                    message="XBPS has broken packages that need fixing",
                    fix_command="xbps-install -Su",
                    fix_description="Fix broken XBPS packages"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_apx_health(self, command: str) -> List[HealthCheck]:
        """Check APX health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="APX Broken Packages",
                    status="error",
                    message="APX has broken packages that need fixing",
                    fix_command="apx update",
                    fix_description="Fix broken APX packages"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_nix_health(self, command: str) -> List[HealthCheck]:
        """Check Nix health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, 'store', 'verify'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Nix Broken Store",
                    status="error",
                    message="Nix store is corrupted",
                    fix_command="nix-store --verify --check-contents",
                    fix_description="Verify and fix Nix store"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_slpkg_health(self, command: str) -> List[HealthCheck]:
        """Check Slpkg health"""
        checks = []
        
        # Check for broken packages
        try:
            result = subprocess.run([command, 'check'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Slpkg Broken Packages",
                    status="error",
                    message="Slpkg has broken packages that need fixing",
                    fix_command="slpkg update",
                    fix_description="Fix broken Slpkg packages"
                ))
        except Exception:
            pass
        
        return checks
    
    def check_third_party_repos(self) -> List[HealthCheck]:
        """Check third-party repository health"""
        checks = []
        
        # Check for broken repositories across all package managers
        checks.extend(self._check_dnf_repos())
        checks.extend(self._check_apt_repos())
        checks.extend(self._check_pacman_repos())
        checks.extend(self._check_zypper_repos())
        checks.extend(self._check_emerge_repos())
        checks.extend(self._check_flatpak_remotes())
        
        return checks
    
    def _check_dnf_repos(self) -> List[HealthCheck]:
        """Check DNF repositories"""
        checks = []
        
        try:
            result = subprocess.run(['dnf', 'repolist'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'error' in line.lower() or 'failed' in line.lower():
                        checks.append(HealthCheck(
                            name="DNF Repository Error",
                            status="warning",
                            message=f"Repository error: {line.strip()}",
                            fix_command="dnf clean all && dnf makecache",
                            fix_description="Clean and rebuild DNF cache"
                        ))
        except Exception:
            pass
        
        return checks
    
    def _check_apt_repos(self) -> List[HealthCheck]:
        """Check APT repositories"""
        checks = []
        
        try:
            result = subprocess.run(['apt', 'update'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="APT Repository Error",
                    status="warning",
                    message="APT repository update failed",
                    fix_command="apt update --fix-missing",
                    fix_description="Fix APT repository issues"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_pacman_repos(self) -> List[HealthCheck]:
        """Check Pacman repositories"""
        checks = []
        
        try:
            result = subprocess.run(['pacman', '-Sy'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Pacman Repository Error",
                    status="warning",
                    message="Pacman repository sync failed",
                    fix_command="pacman -Syy",
                    fix_description="Force Pacman repository sync"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_zypper_repos(self) -> List[HealthCheck]:
        """Check Zypper repositories"""
        checks = []
        
        try:
            result = subprocess.run(['zypper', 'refresh'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Zypper Repository Error",
                    status="warning",
                    message="Zypper repository refresh failed",
                    fix_command="zypper refresh --force",
                    fix_description="Force Zypper repository refresh"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_emerge_repos(self) -> List[HealthCheck]:
        """Check Emerge repositories"""
        checks = []
        
        try:
            result = subprocess.run(['emerge', '--sync'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Emerge Repository Error",
                    status="warning",
                    message="Emerge repository sync failed",
                    fix_command="emerge --sync --quiet",
                    fix_description="Fix Emerge repository sync"
                ))
        except Exception:
            pass
        
        return checks
    
    def _check_flatpak_remotes(self) -> List[HealthCheck]:
        """Check Flatpak remotes"""
        checks = []
        
        try:
            result = subprocess.run(['flatpak', 'remotes'], capture_output=True, text=True)
            if result.returncode != 0:
                checks.append(HealthCheck(
                    name="Flatpak Remote Error",
                    status="warning",
                    message="Flatpak remote configuration error",
                    fix_command="flatpak repair",
                    fix_description="Repair Flatpak remotes"
                ))
        except Exception:
            pass
        
        return checks
    
    def check_disk_bloat(self) -> List[HealthCheck]:
        """Check for package manager cache bloat and cleanup opportunities"""
        checks = []
        
        # Check for large package manager caches
        cache_dirs = [
            ('/var/cache/apt', 'apt'),
            ('/var/cache/dnf', 'dnf'),
            ('/var/cache/pacman', 'pacman'),
            ('/var/cache/zypper', 'zypper'),
            ('/var/cache/flatpak', 'flatpak'),
            ('/var/cache/apk', 'apk'),
            ('/var/cache/xbps', 'xbps'),
            ('/var/cache/emerge', 'emerge'),
            ('/var/cache/slackpkg', 'slackpkg'),
            ('/var/cache/nix', 'nix')
        ]
        
        for cache_dir, manager in cache_dirs:
            if Path(cache_dir).exists():
                try:
                    result = subprocess.run(['du', '-sh', cache_dir], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        size_str = result.stdout.split()[0]
                        # Extract size in MB/GB
                        if 'G' in size_str:
                            size_gb = float(size_str.replace('G', ''))
                            if size_gb > 5:  # More than 5GB
                                checks.append(HealthCheck(
                                    name=f"Large {manager} Cache",
                                    status="warning",
                                    message=f"{manager} cache is {size_str}",
                                    fix_command=f"{manager} clean all",
                                    fix_description=f"Clean large {manager} cache"
                                ))
                        elif 'M' in size_str:
                            size_mb = float(size_str.replace('M', ''))
                            if size_mb > 1000:  # More than 1GB
                                checks.append(HealthCheck(
                                    name=f"Large {manager} Cache",
                                    status="warning",
                                    message=f"{manager} cache is {size_str}",
                                    fix_command=f"{manager} clean all",
                                    fix_description=f"Clean large {manager} cache"
                                ))
                except Exception:
                    pass
        
        return checks
    
    def check_partial_installations(self) -> List[HealthCheck]:
        """Check for partial installations"""
        checks = []
        
        # Check for interrupted installations
        partial_dirs = [
            '/var/lib/dnf/transaction',
            '/var/lib/apt/lists/partial',
            '/var/lib/pacman/db.lck'
        ]
        
        for partial_dir in partial_dirs:
            if Path(partial_dir).exists():
                try:
                    files = list(Path(partial_dir).glob('*'))
                    if files:
                        checks.append(HealthCheck(
                            name="Partial Installation Files",
                            status="error",
                            message=f"Found partial installation files in {partial_dir}",
                            fix_command=f"rm -rf {partial_dir}/*",
                            fix_description="Clean partial installation files"
                        ))
                except Exception:
                    pass
        
        return checks
    
    def check_purge_history(self) -> List[HealthCheck]:
        """Check purge history and orphaned packages"""
        checks = []
        
        # Check for orphaned packages in different package managers
        orphan_checks = [
            ('dnf', 'dnf autoremove --dry-run', 'DNF orphaned packages'),
            ('apt', 'apt autoremove --dry-run', 'APT orphaned packages'),
            ('pacman', 'pacman -Qdt', 'Pacman orphaned packages'),
            ('zypper', 'zypper packages --orphaned', 'Zypper orphaned packages')
        ]
        
        for manager, command, description in orphan_checks:
            if shutil.which(manager):
                try:
                    result = subprocess.run(command.split(), capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        checks.append(HealthCheck(
                            name=description,
                            status="warning",
                            message=f"Found orphaned packages for {manager}",
                            fix_command=f"{manager} autoremove",
                            fix_description=f"Remove orphaned {manager} packages"
                        ))
                except Exception:
                    pass
        
        return checks 