#!/usr/bin/env python3
"""
History Management Module

Tracks package installations and provides rollback capabilities.
"""

import json
import logging
from typing import Dict, List, Any, Optional, NamedTuple
from pathlib import Path
from datetime import datetime
import shutil

from .config import ConfigManager
from .directories import DirectoryManager
from .privilege import PrivilegeManager


class InstallationRecord(NamedTuple):
    """Record of a package installation"""
    timestamp: str
    manager: str
    packages: List[str]
    dependencies: List[str]
    version: str
    size: Optional[int]
    user: str
    scope: str  # 'user' or 'system'


class HistoryManager:
    """Manages installation history and rollback capabilities"""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize history manager"""
        self.config_manager = config_manager
        self.directory_manager = DirectoryManager()
        self.privilege_manager = PrivilegeManager()
        self.logger = logging.getLogger(__name__)
        
        # Load both user and system history
        self.user_history_data = self._load_history('user')
        self.system_history_data = self._load_history('system')
    
    def _load_history(self, scope: str) -> Dict[str, Any]:
        """Load history data from file for specified scope"""
        history_file = self.directory_manager.get_history_file(scope)
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load {scope} history data: {e}")
        
        # Return default history structure
        return {
            'installations': [],
            'rollbacks': [],
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_installations': 0,
                'total_rollbacks': 0,
                'scope': scope
            }
        }
    
    def _save_history(self, scope: str):
        """Save history data to file for specified scope"""
        history_file = self.directory_manager.get_history_file(scope)
        history_data = self.user_history_data if scope == 'user' else self.system_history_data
        
        try:
            history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
        except IOError as e:
            self.logger.error(f"Failed to save {scope} history data: {e}")
    
    def record_install(self, manager: str, packages: List[str], details: Dict[str, Any], scope: str = 'user'):
        """Record a package installation"""
        import getpass
        
        # Create installation record
        record = InstallationRecord(
            timestamp=datetime.now().isoformat(),
            manager=manager,
            packages=packages,
            dependencies=details.get('dependencies', []),
            version=details.get('version', 'unknown'),
            size=details.get('size'),
            user=getpass.getuser(),
            scope=scope
        )
        
        # Add to appropriate history
        if scope == 'system':
            self.system_history_data['installations'].append(record._asdict())
            self.system_history_data['metadata']['total_installations'] += 1
            self.system_history_data['metadata']['last_updated'] = datetime.now().isoformat()
            self._save_history('system')
        else:
            self.user_history_data['installations'].append(record._asdict())
            self.user_history_data['metadata']['total_installations'] += 1
            self.user_history_data['metadata']['last_updated'] = datetime.now().isoformat()
            self._save_history('user')
        
        self.logger.info(f"Recorded {scope} installation: {manager} - {', '.join(packages)}")
    
    def mark_packages_removed(self, manager: str, packages: List[str], scope: str = 'user'):
        """Mark packages as removed in history"""
        history_data = self.system_history_data if scope == 'system' else self.user_history_data
        installations = history_data['installations']
        
        # Find installations that contain any of the specified packages
        for installation in installations:
            if installation['manager'] == manager:
                # Check if any of the packages in this installation match our removal list
                for package in packages:
                    if package in installation['packages']:
                        # Mark this installation as removed
                        installation['removed'] = True
                        installation['removed_timestamp'] = datetime.now().isoformat()
                        installation['removed_packages'] = installation.get('removed_packages', []) + [package]
        
        # Save the updated history
        self._save_history(scope)
        self.logger.info(f"Marked packages as removed in {scope} history: {manager} - {', '.join(packages)}")
    
    def check_package_status(self, package_name: str, manager: str, scope: str = 'user') -> Dict[str, Any]:
        """Check if a package is still installed by querying the package manager"""
        from .package_managers import PackageManagerRegistry
        
        # Get the package manager instance
        config_manager = self.config_manager
        registry = PackageManagerRegistry(config_manager)
        manager_instance = registry.get_manager(manager)
        
        if not manager_instance:
            return {
                'found_in_history': True,
                'still_installed': False,
                'error': f'Package manager {manager} not found'
            }
        
        # Check if package is in history
        history_data = self.system_history_data if scope == 'system' else self.user_history_data
        installations = history_data['installations']
        
        found_in_history = False
        marked_removed = False
        
        for installation in installations:
            if (installation['manager'] == manager and 
                package_name in installation['packages']):
                found_in_history = True
                marked_removed = installation.get('removed', False)
                break
        
        if not found_in_history:
            return {
                'found_in_history': False,
                'still_installed': False,
                'error': 'Package not found in history'
            }
        
        # Check if package is still installed by querying the manager
        try:
            # Try to search for the package to see if it's still installed
            search_result = manager_instance.search(package_name, {})
            still_installed = (search_result.success and 
                              search_result.packages and 
                              any(package_name.lower() in p.get('name', '').lower() 
                                  for p in search_result.packages))
            
            return {
                'found_in_history': True,
                'marked_removed': marked_removed,
                'still_installed': still_installed,
                'manager_enabled': manager_instance.is_enabled()
            }
            
        except Exception as e:
            return {
                'found_in_history': True,
                'marked_removed': marked_removed,
                'still_installed': False,
                'error': f'Error checking package status: {e}',
                'manager_enabled': manager_instance.is_enabled()
            }
    
    def reconcile_package_status(self, scope: str = 'user') -> Dict[str, Any]:
        """Reconcile history with actual package manager status and update history accordingly"""
        history_data = self.system_history_data if scope == 'system' else self.user_history_data
        installations = history_data['installations']
        
        reconciliation_results = {
            'checked': 0,
            'marked_removed': 0,
            'errors': 0,
            'details': []
        }
        
        for installation in installations:
            # Skip already marked as removed
            if installation.get('removed', False):
                continue
            
            manager = installation['manager']
            packages = installation['packages']
            
            for package in packages:
                reconciliation_results['checked'] += 1
                
                try:
                    status = self.check_package_status(package, manager, scope)
                    
                    if status['found_in_history'] and not status['still_installed']:
                        # Package was in history but is no longer installed
                        # Mark it as removed
                        self.mark_packages_removed(manager, [package], scope)
                        reconciliation_results['marked_removed'] += 1
                        reconciliation_results['details'].append({
                            'package': package,
                            'manager': manager,
                            'action': 'marked_removed',
                            'reason': 'Package no longer found in package manager'
                        })
                    
                except Exception as e:
                    reconciliation_results['errors'] += 1
                    reconciliation_results['details'].append({
                        'package': package,
                        'manager': manager,
                        'action': 'error',
                        'error': str(e)
                    })
        
        return reconciliation_results
    
    def record_rollback(self, installation_id: int, reason: str, scope: str = 'user'):
        """Record a rollback operation"""
        history_data = self.system_history_data if scope == 'system' else self.user_history_data
        
        rollback_record = {
            'timestamp': datetime.now().isoformat(),
            'installation_id': installation_id,
            'reason': reason,
            'original_installation': history_data['installations'][installation_id],
            'scope': scope
        }
        
        history_data['rollbacks'].append(rollback_record)
        history_data['metadata']['total_rollbacks'] += 1
        history_data['metadata']['last_updated'] = datetime.now().isoformat()
        
        self._save_history(scope)
        
        self.logger.info(f"Recorded {scope} rollback: installation {installation_id} - {reason}")
    
    def perform_rollback(self, installation_id: int, scope: str = 'user', purge: bool = False) -> Dict[str, Any]:
        """Perform a rollback by uninstalling packages from a specific installation"""
        from .package_managers import PackageManagerRegistry
        
        # Get the installation record
        installation = self.get_installation(installation_id, scope)
        if not installation:
            return {
                'success': False,
                'error': f'Installation {installation_id} not found'
            }
        
        # Get the package manager instance
        config_manager = self.config_manager
        registry = PackageManagerRegistry(config_manager)
        manager_instance = registry.get_manager(installation['manager'])
        
        if not manager_instance:
            return {
                'success': False,
                'error': f'Package manager {installation["manager"]} not available'
            }
        
        # Prepare packages to remove (main packages + dependencies)
        packages_to_remove = installation['packages'] + installation['dependencies']
        
        # Remove duplicates while preserving order
        seen = set()
        unique_packages = []
        for pkg in packages_to_remove:
            if pkg not in seen:
                seen.add(pkg)
                unique_packages.append(pkg)
        
        try:
            # Perform the removal
            if purge:
                result = manager_instance.purge(unique_packages, {})
            else:
                result = manager_instance.remove(unique_packages, {})
            
            if result.success:
                # Record the rollback
                self.record_rollback(installation_id, f"Manual rollback - {'purged' if purge else 'removed'} packages", scope)
                
                # Mark packages as removed in history
                self.mark_packages_removed(installation['manager'], unique_packages, scope)
                
                return {
                    'success': True,
                    'packages_removed': unique_packages,
                    'manager': installation['manager'],
                    'purge': purge,
                    'message': f"Successfully {'purged' if purge else 'removed'} {len(unique_packages)} packages"
                }
            else:
                return {
                    'success': False,
                    'error': result.error or 'Unknown error during removal',
                    'packages_attempted': unique_packages
                }
                
        except Exception as e:
            self.logger.error(f"Error performing rollback: {e}")
            return {
                'success': False,
                'error': str(e),
                'packages_attempted': unique_packages
            }
    
    def get_installations(self, limit: Optional[int] = None, 
                         manager: Optional[str] = None, 
                         scope: str = 'user') -> List[Dict[str, Any]]:
        """Get installation history for specified scope"""
        if scope == 'system' and not self.privilege_manager.can_access_system_history():
            self.logger.warning("Cannot access system history - insufficient privileges")
            return []
        
        history_data = self.system_history_data if scope == 'system' else self.user_history_data
        installations = history_data['installations']
        
        # Filter by manager if specified
        if manager:
            installations = [i for i in installations if i['manager'] == manager]
        
        # Apply limit if specified
        if limit:
            installations = installations[-limit:]
        
        return installations
    
    def get_all_installations(self, limit: Optional[int] = None, 
                             manager: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all installations (user + system if accessible)"""
        user_installations = self.get_installations(limit, manager, 'user')
        system_installations = self.get_installations(limit, manager, 'system')
        
        # Combine and sort by timestamp
        all_installations = user_installations + system_installations
        all_installations.sort(key=lambda x: x['timestamp'])
        
        # Apply limit if specified
        if limit:
            all_installations = all_installations[-limit:]
        
        return all_installations
    
    def get_installation(self, installation_id: int, scope: str = 'user') -> Optional[Dict[str, Any]]:
        """Get a specific installation record"""
        if scope == 'system' and not self.privilege_manager.can_access_system_history():
            return None
        
        history_data = self.system_history_data if scope == 'system' else self.user_history_data
        installations = history_data['installations']
        
        if 0 <= installation_id < len(installations):
            return installations[installation_id]
        return None
    
    def get_rollbacks(self, limit: Optional[int] = None, scope: str = 'user') -> List[Dict[str, Any]]:
        """Get rollback history for specified scope"""
        if scope == 'system' and not self.privilege_manager.can_access_system_history():
            return []
        
        history_data = self.system_history_data if scope == 'system' else self.user_history_data
        rollbacks = history_data['rollbacks']
        
        if limit:
            rollbacks = rollbacks[-limit:]
        return rollbacks
    
    def get_statistics(self, scope: str = 'user') -> Dict[str, Any]:
        """Get history statistics for specified scope"""
        if scope == 'system' and not self.privilege_manager.can_access_system_history():
            return {'error': 'Cannot access system history - insufficient privileges'}
        
        history_data = self.system_history_data if scope == 'system' else self.user_history_data
        installations = history_data['installations']
        rollbacks = history_data['rollbacks']
        
        # Calculate statistics
        stats = {
            'scope': scope,
            'total_installations': len(installations),
            'total_rollbacks': len(rollbacks),
            'managers_used': {},
            'packages_installed': set(),
            'recent_activity': []
        }
        
        # Count managers used
        for installation in installations:
            manager = installation['manager']
            stats['managers_used'][manager] = stats['managers_used'].get(manager, 0) + 1
            
            # Collect unique packages
            stats['packages_installed'].update(installation['packages'])
        
        # Convert set to list for JSON serialization
        stats['packages_installed'] = list(stats['packages_installed'])
        
        # Get recent activity (last 10 installations)
        stats['recent_activity'] = installations[-10:] if installations else []
        
        return stats
    
    def search_installations(self, query: str, scope: str = 'user') -> List[Dict[str, Any]]:
        """Search installations by package name or manager for specified scope"""
        if scope == 'system' and not self.privilege_manager.can_access_system_history():
            return []
        
        history_data = self.system_history_data if scope == 'system' else self.user_history_data
        query = query.lower()
        results = []
        
        for installation in history_data['installations']:
            # Search in package names
            packages = [p.lower() for p in installation['packages']]
            if any(query in p for p in packages):
                results.append(installation)
                continue
            
            # Search in manager name
            if query in installation['manager'].lower():
                results.append(installation)
                continue
            
            # Search in dependencies
            dependencies = [d.lower() for d in installation['dependencies']]
            if any(query in d for d in dependencies):
                results.append(installation)
        
        return results
    
    def handle_history_command(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle history command operations"""
        if not args:
            # Show recent history (user only by default)
            installations = self.get_installations(limit=10, scope='user')
            self._display_installations(installations, 'user')
            return 0
        
        command = args[0]
        
        if command == 'list':
            limit = options.get('limit', 20)
            manager = options.get('manager')
            scope = options.get('scope', 'user')
            
            if scope == 'all':
                installations = self.get_all_installations(limit=limit, manager=manager)
                self._display_installations(installations, 'all')
            else:
                installations = self.get_installations(limit=limit, manager=manager, scope=scope)
                self._display_installations(installations, scope)
            return 0
        
        elif command == 'show':
            if len(args) < 2:
                print("Error: Installation ID required")
                return 1
            
            try:
                installation_id = int(args[1])
                scope = options.get('scope', 'user')
                installation = self.get_installation(installation_id, scope)
                if installation:
                    self._display_installation_details(installation)
                else:
                    print(f"Error: Installation {installation_id} not found")
                    return 1
            except ValueError:
                print("Error: Invalid installation ID")
                return 1
            return 0
        
        elif command == 'search':
            if len(args) < 2:
                print("Error: Search query required")
                return 1
            
            query = args[1]
            scope = options.get('scope', 'user')
            results = self.search_installations(query, scope)
            self._display_installations(results, scope)
            return 0
        
        elif command == 'rollback':
            if len(args) < 2:
                print("Error: Installation ID required")
                print("Usage: paka history rollback <installation_id> [--purge] [--scope=user|system]")
                return 1
            
            try:
                installation_id = int(args[1])
                scope = options.get('scope', 'user')
                purge = options.get('purge', False)
                
                # Show installation details before rollback
                installation = self.get_installation(installation_id, scope)
                if not installation:
                    print(f"Error: Installation {installation_id} not found")
                    return 1
                
                print(f"Rollback Installation {installation_id}:")
                print(f"  Manager: {installation['manager']}")
                print(f"  Packages: {', '.join(installation['packages'])}")
                if installation['dependencies']:
                    print(f"  Dependencies: {', '.join(installation['dependencies'])}")
                print(f"  Action: {'Purge' if purge else 'Remove'} all packages and dependencies")
                print()
                
                # Confirm rollback
                if not options.get('yes'):
                    confirm = input(f"Proceed with rollback? (y/N): ").lower()
                    if confirm != 'y':
                        print("Rollback cancelled")
                        return 0
                
                # Perform rollback
                result = self.perform_rollback(installation_id, scope, purge)
                
                if result['success']:
                    print(f"✅ {result['message']}")
                    print(f"   Manager: {result['manager']}")
                    print(f"   Packages: {', '.join(result['packages_removed'])}")
                else:
                    print(f"❌ Rollback failed: {result['error']}")
                    if 'packages_attempted' in result:
                        print(f"   Attempted: {', '.join(result['packages_attempted'])}")
                    return 1
                
            except ValueError:
                print("Error: Invalid installation ID")
                return 1
            return 0
        
        elif command == 'stats':
            scope = options.get('scope', 'user')
            stats = self.get_statistics(scope)
            self._display_statistics(stats)
            return 0
        
        elif command == 'clear':
            scope = options.get('scope', 'user')
            if scope == 'system' and not self.privilege_manager.can_access_system_history():
                print("Error: Cannot clear system history - insufficient privileges")
                return 1
            
            if options.get('yes') or input(f"Clear {scope} history? (y/N): ").lower() == 'y':
                if scope == 'system':
                    self.system_history_data['installations'] = []
                    self.system_history_data['rollbacks'] = []
                    self.system_history_data['metadata']['total_installations'] = 0
                    self.system_history_data['metadata']['total_rollbacks'] = 0
                    self._save_history('system')
                else:
                    self.user_history_data['installations'] = []
                    self.user_history_data['rollbacks'] = []
                    self.user_history_data['metadata']['total_installations'] = 0
                    self.user_history_data['metadata']['total_rollbacks'] = 0
                    self._save_history('user')
                print(f"{scope.capitalize()} history cleared")
            return 0
        
        else:
            print(f"Error: Unknown history command: {command}")
            return 1
    
    def _display_installations(self, installations: List[Dict[str, Any]], scope: str):
        """Display a list of installations"""
        if not installations:
            print(f"No {scope} installations found")
            return
        
        print(f"{scope.capitalize()} Installations:")
        print(f"{'ID':<4} {'Date':<20} {'Manager':<12} {'Packages'}")
        print("-" * 60)
        
        for i, installation in enumerate(installations):
            date = datetime.fromisoformat(installation['timestamp']).strftime('%Y-%m-%d %H:%M')
            manager = installation['manager']
            packages = ', '.join(installation['packages'][:3])  # Show first 3 packages
            if len(installation['packages']) > 3:
                packages += f" (+{len(installation['packages']) - 3} more)"
            
            print(f"{i:<4} {date:<20} {manager:<12} {packages}")
    
    def _display_installation_details(self, installation: Dict[str, Any]):
        """Display detailed information about an installation"""
        print(f"Installation Details:")
        print(f"  Date: {installation['timestamp']}")
        print(f"  Manager: {installation['manager']}")
        print(f"  User: {installation['user']}")
        print(f"  Scope: {installation.get('scope', 'user')}")
        print(f"  Version: {installation['version']}")
        if installation['size']:
            print(f"  Size: {installation['size']} bytes")
        
        print(f"  Packages ({len(installation['packages'])}):")
        for package in installation['packages']:
            print(f"    - {package}")
        
        if installation['dependencies']:
            print(f"  Dependencies ({len(installation['dependencies'])}):")
            for dep in installation['dependencies'][:10]:  # Show first 10
                print(f"    - {dep}")
            if len(installation['dependencies']) > 10:
                print(f"    ... and {len(installation['dependencies']) - 10} more")
    
    def _display_statistics(self, stats: Dict[str, Any]):
        """Display history statistics"""
        if 'error' in stats:
            print(f"Error: {stats['error']}")
            return
        
        print(f"History Statistics ({stats['scope']}):")
        print(f"  Total Installations: {stats['total_installations']}")
        print(f"  Total Rollbacks: {stats['total_rollbacks']}")
        print(f"  Unique Packages: {len(stats['packages_installed'])}")
        
        print(f"  Managers Used:")
        for manager, count in stats['managers_used'].items():
            print(f"    {manager}: {count}")
        
        if stats['recent_activity']:
            print(f"  Recent Activity:")
            for installation in stats['recent_activity'][-5:]:  # Last 5
                date = datetime.fromisoformat(installation['timestamp']).strftime('%Y-%m-%d %H:%M')
                packages = ', '.join(installation['packages'][:2])
                print(f"    {date} - {installation['manager']}: {packages}")
    
    def cleanup_old_entries(self, scope: str = 'user') -> int:
        """Clean up old history entries based on retention settings"""
        if scope == 'system' and not self.privilege_manager.can_access_system_history():
            return 0
        
        config = self.config_manager.load_config()
        settings = config.get('settings', {})
        
        # Get retention settings
        max_entries = settings.get('history_max_entries', 1000)
        retention_days = settings.get('history_retention_days', 365)
        
        history_data = self.system_history_data if scope == 'system' else self.user_history_data
        installations = history_data['installations']
        rollbacks = history_data['rollbacks']
        
        # Count entries before cleanup
        initial_count = len(installations)
        
        # Remove old installations based on retention days
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - retention_days)
        
        installations_to_keep = []
        for installation in installations:
            try:
                install_date = datetime.fromisoformat(installation['timestamp'])
                if install_date >= cutoff_date:
                    installations_to_keep.append(installation)
            except ValueError:
                # Keep entries with invalid dates
                installations_to_keep.append(installation)
        
        # Apply max entries limit
        if len(installations_to_keep) > max_entries:
            installations_to_keep = installations_to_keep[-max_entries:]
        
        # Update history data
        history_data['installations'] = installations_to_keep
        history_data['metadata']['total_installations'] = len(installations_to_keep)
        history_data['metadata']['last_updated'] = datetime.now().isoformat()
        
        # Save history
        self._save_history(scope)
        
        cleaned_count = initial_count - len(installations_to_keep)
        self.logger.info(f"Cleaned {cleaned_count} old {scope} history entries")
        
        return cleaned_count 