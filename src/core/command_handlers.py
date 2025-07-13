#!/usr/bin/env python3
"""
Command Handlers Module

Handles execution of PAKA commands with proper error handling,
plugin integration, and user feedback.
"""

import logging
from typing import Dict, List, Any
from .plugin_manager import PluginEvent


class CommandHandlers:
    """Handles execution of PAKA commands"""
    
    def __init__(self, engine):
        """Initialize command handlers with engine reference"""
        self.engine = engine
        self.ui_manager = engine.ui_manager
        self.package_managers = engine.package_managers
        self.privilege_manager = engine.privilege_manager
        self.history_manager = engine.history_manager
        self.health_manager = engine.health_manager
        self.shell_integration = engine.shell_integration
        self.logger = logging.getLogger(__name__)
    
    def handle_install(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle package installation with scope support"""
        if not args:
            self.ui_manager.error("No packages specified for installation")
            return 1
        
        packages = args
        manager_name = options.get('manager')
        dry_run = options.get('dry_run', False)
        scope = options.get('scope', 'user')
        
        # Determine which package managers to use
        if manager_name:
            managers = [self.package_managers.get(manager_name)]
            if not managers[0]:
                self.ui_manager.error(f"Package manager '{manager_name}' not found")
                self.ui_manager.info("Available managers:")
                for name, manager in self.package_managers.items():
                    status = "✓" if manager.is_enabled() else "✗"
                    self.ui_manager.info(f"  {status} {name}")
                return 1
        else:
            # Use all available managers
            managers = list(self.package_managers.values())
        
        # Filter out disabled managers
        managers = [m for m in managers if m and m.is_enabled()]
        
        if not managers:
            self.ui_manager.error("No enabled package managers found")
            return 1
        
        # Check for Flatpak and similar tools that need scope prompting
        flatpak_managers = ['flatpak', 'snap', 'appimage']
        for manager in managers:
            if manager.name in flatpak_managers and scope == 'system':
                # Prompt for Flatpak scope
                self.ui_manager.info(f"\nInstalling with {manager.name}:")
                self.ui_manager.info("1. System-wide (all users)")
                self.ui_manager.info("2. User-only (recommended)")
                
                scope_choice = self.ui_manager.prompt("Choose installation scope (1-2): ")
                if scope_choice == '1':
                    scope = 'system'
                    # Ensure we have privileges for system install
                    if not self.privilege_manager.is_root():
                        if not self.privilege_manager.escalate_if_needed('flatpak_system_install', self.ui_manager):
                            self.ui_manager.error("Cannot install system-wide - privilege escalation failed")
                            return 1
                else:
                    scope = 'user'
        
        # Show installation plan
        self.ui_manager.info(f"Installation Plan ({scope} scope):")
        for manager in managers:
            self.ui_manager.info(f"  {manager.name}: {', '.join(packages)}")
        
        if dry_run:
            self.ui_manager.info("Dry run mode - no packages will be installed")
            return 0
        
        # Check if packages exist before triggering pre-install-success
        found_packages = {}
        for manager in managers:
            try:
                # Search for packages to see if they exist
                search_result = manager.search(' '.join(packages), {})
                if search_result.success and search_result.packages:
                    found_packages[manager.name] = packages
            except Exception as e:
                self.logger.warning(f"Could not search {manager.name} for packages: {e}")
                # Assume packages exist if search fails
                found_packages[manager.name] = packages
        
        # Trigger pre-install-success plugins only for managers that found packages
        if found_packages:
            install_context = {
                'packages': packages,
                'managers': list(found_packages.keys()),
                'options': options,
                'scope': scope,
                'found_packages': found_packages
            }
            if not self.engine._trigger_plugin_event(PluginEvent.PRE_INSTALL_SUCCESS, install_context):
                self.ui_manager.error("Pre-install-success plugins failed")
                return 1
        
        # Confirm installation
        if not options.get('yes', False):
            if not self.ui_manager.confirm("Proceed with installation?"):
                return 0
        
        # Execute installations
        success_count = 0
        failed_managers = []
        
        for manager in managers:
            try:
                result = manager.install(packages, options)
                if result.success:
                    success_count += 1
                    # Record in history with scope
                    self.history_manager.record_install(
                        manager.name, packages, result.details or {}, scope
                    )
                    
                    # Trigger post-install plugins
                    post_context = {
                        'manager': manager.name,
                        'packages': packages,
                        'result': result.details or {},
                        'success': True,
                        'scope': scope
                    }
                    self.engine._trigger_plugin_event(PluginEvent.POST_INSTALL, post_context)
                else:
                    failed_managers.append(manager.name)
                    self.ui_manager.error(f"Installation failed for {manager.name}: {result.error}")
                    
                    # Trigger post-install-failure plugins
                    error_context = {
                        'manager': manager.name,
                        'packages': packages,
                        'error': result.error,
                        'success': False,
                        'scope': scope
                    }
                    self.engine._trigger_plugin_event(PluginEvent.POST_INSTALL_FAILURE, error_context)
            except Exception as e:
                failed_managers.append(manager.name)
                self.ui_manager.error(f"Error with {manager.name}: {e}")
                
                # Trigger post-install-failure plugins
                error_context = {
                    'manager': manager.name,
                    'packages': packages,
                    'error': str(e),
                    'success': False,
                    'scope': scope
                }
                self.engine._trigger_plugin_event(PluginEvent.POST_INSTALL_FAILURE, error_context)
        
        # Show results
        if success_count > 0:
            self.ui_manager.success(f"Successfully installed packages with {success_count} manager(s)")
        if failed_managers:
            self.ui_manager.error(f"Failed managers: {', '.join(failed_managers)}")
        
        return 0
    
    def handle_remove(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle package removal"""
        if not args:
            self.ui_manager.error("No packages specified for removal")
            return 1
        
        packages = args
        manager_name = options.get('manager')
        dry_run = options.get('dry_run', False)
        
        # Determine which package managers to use
        if manager_name:
            managers = [self.package_managers.get(manager_name)]
            if not managers[0]:
                self.ui_manager.error(f"Package manager '{manager_name}' not found")
                return 1
        else:
            # Use all available managers
            managers = list(self.package_managers.values())
        
        # Filter out disabled managers
        managers = [m for m in managers if m and m.is_enabled()]
        
        if not managers:
            self.ui_manager.error("No enabled package managers found")
            return 1
        
        # Show removal plan
        self.ui_manager.info("Removal Plan:")
        for manager in managers:
            self.ui_manager.info(f"  {manager.name}: {', '.join(packages)}")
        
        if dry_run:
            self.ui_manager.info("Dry run mode - no packages will be removed")
            return 0
        
        # Confirm removal
        if not options.get('yes', False):
            if not self.ui_manager.confirm("Proceed with removal?"):
                return 0
        
        # Execute removals
        success_count = 0
        for manager in managers:
            try:
                result = manager.remove(packages, options)
                if result.success:
                    success_count += 1
                else:
                    self.ui_manager.error(f"Removal failed for {manager.name}: {result.error}")
            except Exception as e:
                self.ui_manager.error(f"Error with {manager.name}: {e}")
        
        if success_count > 0:
            self.ui_manager.success(f"Successfully removed packages using {success_count} manager(s)")
            return 0
        else:
            return 1
    
    def handle_purge(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle package purging (remove + config cleanup)"""
        if not args:
            self.ui_manager.error("No packages specified for purging")
            return 1
        
        packages = args
        manager_name = options.get('manager')
        dry_run = options.get('dry_run', False)
        
        # Determine which package managers to use
        if manager_name:
            managers = [self.package_managers.get(manager_name)]
            if not managers[0]:
                self.ui_manager.error(f"Package manager '{manager_name}' not found")
                return 1
        else:
            # Use all available managers
            managers = list(self.package_managers.values())
        
        # Filter out disabled managers
        managers = [m for m in managers if m and m.is_enabled()]
        
        if not managers:
            self.ui_manager.error("No enabled package managers found")
            return 1
        
        # Show purge plan
        self.ui_manager.info("Purge Plan (remove + config cleanup):")
        for manager in managers:
            self.ui_manager.info(f"  {manager.name}: {', '.join(packages)}")
        
        if dry_run:
            self.ui_manager.info("Dry run mode - no packages will be purged")
            return 0
        
        # Confirm purge
        if not options.get('yes', False):
            if not self.ui_manager.confirm("Proceed with purging? This will remove packages AND configuration files."):
                return 0
        
        # Execute purges
        success_count = 0
        for manager in managers:
            try:
                result = manager.purge(packages, options)
                if result.success:
                    success_count += 1
                else:
                    self.ui_manager.error(f"Purge failed for {manager.name}: {result.error}")
            except Exception as e:
                self.ui_manager.error(f"Error with {manager.name}: {e}")
        
        if success_count > 0:
            self.ui_manager.success(f"Successfully purged packages using {success_count} manager(s)")
            return 0
        else:
            return 1
    
    def handle_update(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle package list updates (refresh)"""
        manager_name = options.get('manager')
        dry_run = options.get('dry_run', False)
        
        # Determine which package managers to use
        if manager_name:
            managers = [self.package_managers.get(manager_name)]
            if not managers[0]:
                self.ui_manager.error(f"Package manager '{manager_name}' not found")
                return 1
        else:
            # Use all available managers
            managers = list(self.package_managers.values())
        
        # Filter out disabled managers
        managers = [m for m in managers if m and m.is_enabled()]
        
        if not managers:
            self.ui_manager.error("No enabled package managers found")
            return 1
        
        # Show update plan
        self.ui_manager.info("Update Plan (refresh package lists):")
        for manager in managers:
            self.ui_manager.info(f"  {manager.name}")
        
        if dry_run:
            self.ui_manager.info("Dry run mode - no updates will be performed")
            return 0
        
        # Execute updates
        success_count = 0
        for manager in managers:
            try:
                result = manager.update(options)
                if result.success:
                    success_count += 1
                    self.ui_manager.success(f"Updated {manager.name}")
                else:
                    self.ui_manager.error(f"Update failed for {manager.name}: {result.error}")
            except Exception as e:
                self.ui_manager.error(f"Error with {manager.name}: {e}")
        
        if success_count > 0:
            self.ui_manager.success(f"Successfully updated {success_count} manager(s)")
            return 0
        else:
            return 1
    
    def handle_upgrade(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle package upgrades"""
        manager_name = options.get('manager')
        dry_run = options.get('dry_run', False)
        
        # Determine which package managers to use
        if manager_name:
            managers = [self.package_managers.get(manager_name)]
            if not managers[0]:
                self.ui_manager.error(f"Package manager '{manager_name}' not found")
                return 1
        else:
            # Use all available managers
            managers = list(self.package_managers.values())
        
        # Filter out disabled managers
        managers = [m for m in managers if m and m.is_enabled()]
        
        if not managers:
            self.ui_manager.error("No enabled package managers found")
            return 1
        
        # Show upgrade plan
        self.ui_manager.info("Upgrade Plan:")
        for manager in managers:
            self.ui_manager.info(f"  {manager.name}")
        
        if dry_run:
            self.ui_manager.info("Dry run mode - no upgrades will be performed")
            return 0
        
        # Confirm upgrade
        if not options.get('yes', False):
            if not self.ui_manager.confirm("Proceed with upgrade?"):
                return 0
        
        # Execute upgrades
        success_count = 0
        for manager in managers:
            try:
                result = manager.upgrade(options)
                if result.success:
                    success_count += 1
                    self.ui_manager.success(f"Upgraded {manager.name}")
                else:
                    self.ui_manager.error(f"Upgrade failed for {manager.name}: {result.error}")
            except Exception as e:
                self.ui_manager.error(f"Error with {manager.name}: {e}")
        
        if success_count > 0:
            self.ui_manager.success(f"Successfully upgraded {success_count} manager(s)")
            return 0
        else:
            return 1
    
    def handle_search(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle package search"""
        if not args:
            self.ui_manager.error("No search term specified")
            return 1
        
        search_term = args[0]
        manager_name = options.get('manager')
        
        # Determine which package managers to use
        if manager_name:
            managers = [self.package_managers.get(manager_name)]
            if not managers[0]:
                self.ui_manager.error(f"Package manager '{manager_name}' not found")
                self.ui_manager.info("Available managers:")
                for name, manager in self.package_managers.items():
                    status = "✓" if manager.is_enabled() else "✗"
                    self.ui_manager.info(f"  {status} {name}")
                return 1
        else:
            # Use all available managers
            managers = list(self.package_managers.values())
        
        # Filter out disabled managers
        enabled_managers = [m for m in managers if m and m.is_enabled()]
        
        if not enabled_managers:
            self.ui_manager.error("No enabled package managers found")
            return 1
        
        # Show which managers are being searched
        if manager_name:
            self.ui_manager.info(f"Searching '{search_term}' in {manager_name} package manager...")
        else:
            manager_names = [m.name for m in enabled_managers]
            self.ui_manager.info(f"Searching '{search_term}' in {len(enabled_managers)} package manager(s): {', '.join(manager_names)}")
        
        # Execute searches
        all_results = []
        search_stats = {}
        
        for manager in enabled_managers:
            try:
                result = manager.search(search_term, options)
                if result.success:
                    if result.packages:
                        all_results.extend(result.packages)
                        search_stats[manager.name] = len(result.packages)
                    else:
                        search_stats[manager.name] = 0
                else:
                    self.ui_manager.error(f"Search failed for {manager.name}: {result.error}")
                    search_stats[manager.name] = 'error'
            except Exception as e:
                self.ui_manager.error(f"Error with {manager.name}: {e}")
                search_stats[manager.name] = 'error'
        
        # Display search statistics
        if manager_name:
            # Single manager search
            count = search_stats.get(manager_name, 0)
            if isinstance(count, int):
                self.ui_manager.info(f"Found {count} package(s) in {manager_name}")
        else:
            # Multi-manager search
            self.ui_manager.info("Search results by manager:")
            for manager_name, count in search_stats.items():
                if isinstance(count, int):
                    status = f"{count} package(s)" if count > 0 else "No packages"
                    self.ui_manager.info(f"  {manager_name}: {status}")
                else:
                    self.ui_manager.error(f"  {manager_name}: Search failed")
        
        # Display results
        if all_results:
            self.ui_manager.display_search_results(all_results)
        else:
            self.ui_manager.info("No packages found")
            
            # Provide helpful suggestions
            if not manager_name:
                self.ui_manager.info("\nTip: Use --manager <name> to search in a specific package manager")
                self.ui_manager.info("Example: paka search firefox --manager appimage")
        
        return 0
    
    def handle_health(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle health checks"""
        return self.health_manager.run_health_checks(options)
    
    def handle_history(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle history operations with scope support"""
        # Add scope option if not present
        if 'scope' not in options:
            # Default to user scope, but allow system if privileged
            if self.privilege_manager.can_access_system_history():
                options['scope'] = 'user'  # Default to user, can be overridden
            else:
                options['scope'] = 'user'
        
        return self.history_manager.handle_history_command(args, options)
    
    def handle_shell_not_found(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle shell-not-found command for command-not-found integration"""
        if not args:
            return 1
        
        command = args[0]
        suggestion = self.shell_integration.handle_command_not_found(command)
        
        if suggestion:
            print(suggestion)
            return 0
        else:
            return 1 