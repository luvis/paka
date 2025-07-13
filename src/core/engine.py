#!/usr/bin/env python3
"""
Core Engine Module

Handles command orchestration, session management, and coordinates
between package managers, plugins, and user interface.
"""

import sys
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import shutil

from .config import ConfigManager
from .session import SessionManager
from .history import HistoryManager
from .health import HealthManager
from .ui import UIManager
from .package_managers import PackageManagerRegistry
from .plugin_manager import PluginManager, PluginEvent
from .shell_integration import ShellIntegration
from .directories import DirectoryManager
from .privilege import PrivilegeManager
from .command_handlers import CommandHandlers
from .menu_system import MenuSystem
from .wizard_system import WizardSystem


class PAKAEngine:
    """Main engine that orchestrates all PAKA operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the PAKA engine with configuration"""
        self.directory_manager = DirectoryManager()
        self.privilege_manager = PrivilegeManager()
        self.config_manager = ConfigManager(config_path)
        self.session_manager = SessionManager(self.config_manager)
        self.history_manager = HistoryManager(self.config_manager)
        self.health_manager = HealthManager(self.config_manager, self)
        self.ui_manager = UIManager()
        self.package_manager_registry = PackageManagerRegistry(self.config_manager)
        
        # Setup logging
        self._setup_logging()
        
        # Load configuration
        self.config = self.config_manager.load_config()
        
        # Initialize package managers
        self.package_managers = self.package_manager_registry.get_available_managers()
        
        # Load plugins
        self.plugin_manager = PluginManager(self.config_manager)
        
        # Initialize shell integration
        self.shell_integration = ShellIntegration(self.config_manager)
        
        # Initialize modular systems
        self.command_handlers = CommandHandlers(self)
        self.menu_system = MenuSystem(self)
        self.wizard_system = WizardSystem(self)
        
        self.logger = logging.getLogger(__name__)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = self.config_manager.get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'paka.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _trigger_plugin_event(self, event: str, context: Dict[str, Any]) -> bool:
        """Trigger a plugin event"""
        return self.plugin_manager.trigger_event(event, context)
    
    def run_command(self, command: str, args: List[str], options: Dict[str, Any]) -> int:
        """Execute a PAKA command with arguments and options"""
        # Check privilege requirements and escalate if needed
        if self.privilege_manager.needs_privilege_escalation(command):
            if not self.privilege_manager.escalate_if_needed(command, self.ui_manager):
                return 1
        
        try:
            # Update session with command
            self.session_manager.record_command(command, args, options)
            
            # Execute command using command handlers
            if command == 'install':
                result = self.command_handlers.handle_install(args, options)
            elif command == 'remove':
                result = self._handle_remove(args, options)
            elif command == 'purge':
                result = self.command_handlers.handle_purge(args, options)
            elif command == 'update':
                result = self.command_handlers.handle_update(args, options)
            elif command == 'upgrade':
                result = self.command_handlers.handle_upgrade(args, options)
            elif command == 'search':
                result = self.command_handlers.handle_search(args, options)
            elif command == 'health':
                result = self.command_handlers.handle_health(args, options)
            elif command == 'history':
                result = self.command_handlers.handle_history(args, options)
            elif command == 'config':
                result = self._handle_config(args, options)
            elif command == 'shell-not-found':
                result = self.command_handlers.handle_shell_not_found(args, options)
            elif command == 'reconcile':
                result = self._handle_reconcile(args, options)
            else:
                self.ui_manager.error(f"Unknown command: {command}")
                return 1
            
            return result
        except Exception as e:
            self.logger.error(f"Error executing command {command}: {e}")
            self.ui_manager.error(f"Command failed: {e}")
            return 1
    
    def _handle_config(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle configuration operations"""
        if not args:
            # Show interactive config menu
            return self.menu_system.show_config_menu()
        
        operation = args[0]
        
        if operation == 'show':
            self._show_config()
            return 0
        elif operation == 'edit':
            self.config_manager.edit_config()
            return 0
        elif operation == 'reset':
            if self.ui_manager.confirm("Reset configuration to defaults?"):
                self.config_manager.reset_config()
                self.ui_manager.success("Configuration reset to defaults")
            return 0
        elif operation == 'plugins':
            return self._handle_plugin_config(args[1:], options)
        elif operation == 'wizard':
            return self.wizard_system.run_configuration_wizard()
        else:
            self.ui_manager.error(f"Unknown config operation: {operation}")
            return 1
    
    def _show_config(self):
        """Show current configuration"""
        self.ui_manager.info("\nPAKA Configuration")
        self.ui_manager.info("=" * 30)
        
        # Show scope info
        scope_info = self.config_manager.get_scope_info()
        self.ui_manager.display_note(f"Scope: {scope_info['scope']}")
        self.ui_manager.display_note(f"Running as root: {scope_info['is_root']}")
        self.ui_manager.display_note("")
        
        # Show directories
        self.ui_manager.display_note("Directories:")
        self.ui_manager.display_note(f"  Config: {scope_info['config_dir']}")
        self.ui_manager.display_note(f"  Plugins: {scope_info['plugins_dir']}")
        self.ui_manager.display_note(f"  History: {scope_info['history_dir']}")
        self.ui_manager.display_note("")
        
        # Show permissions
        self.ui_manager.display_note("Permissions:")
        self.ui_manager.display_note(f"  Can write config: {scope_info['can_write_config']}")
        self.ui_manager.display_note(f"  Can write plugins: {scope_info['can_write_plugins']}")
        self.ui_manager.display_note(f"  Can write history: {scope_info['can_write_history']}")
        self.ui_manager.display_note("")
        
        # Show configuration data
        self.ui_manager.display_note("Configuration Data:")
        import json
        print(json.dumps(self.config_manager.load_config(), indent=2))
    
    def _handle_plugin_config(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle plugin-specific configuration"""
        if not args:
            return self.menu_system._show_plugin_menu()
        
        subcommand = args[0]
        
        if subcommand == 'list':
            self.menu_system._list_plugins()
            return 0
        elif subcommand == 'enable':
            if len(args) < 2:
                self.ui_manager.error("Plugin name required")
                return 1
            plugin_name = args[1]
            if self.plugin_manager.enable_plugin(plugin_name):
                self.ui_manager.success(f"Plugin '{plugin_name}' enabled")
                return 0
            else:
                self.ui_manager.error(f"Failed to enable plugin '{plugin_name}'")
                return 1
        elif subcommand == 'disable':
            if len(args) < 2:
                self.ui_manager.error("Plugin name required")
                return 1
            plugin_name = args[1]
            if self.plugin_manager.disable_plugin(plugin_name):
                self.ui_manager.success(f"Plugin '{plugin_name}' disabled")
                return 0
            else:
                self.ui_manager.error(f"Failed to disable plugin '{plugin_name}'")
                return 1
        elif subcommand == 'create':
            self.menu_system._create_plugin_template()
            return 0
        elif subcommand == 'check':
            self.menu_system._check_plugin_syntax()
            return 0
        elif subcommand == 'help':
            self.plugin_manager.show_plugin_help()
            return 0
        else:
            self.ui_manager.error(f"Unknown plugin subcommand: {subcommand}")
            return 1
    
    def display_timing(self, start_time: datetime, end_time: datetime):
        """Display timing information"""
        duration = end_time - start_time
        self.ui_manager.info(f"Operation completed in {duration.total_seconds():.2f} seconds") 

    def _handle_remove(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle package removal with smart detection"""
        if not args:
            self.ui_manager.error("No packages specified for removal")
            return 1
        
        packages = args
        manager = options.get('manager')
        
        # Smart package detection
        if not manager:
            # Check for multiple installations across package managers
            multi_installations = self._detect_multiple_installations(packages)
            
            if multi_installations:
                return self._handle_multi_installation_removal(multi_installations, options)
        
        # Proceed with normal removal
        return self.command_handlers.handle_remove(packages, options)
    
    def _detect_multiple_installations(self, package_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Detect if packages are installed in multiple package managers"""
        multi_installations = {}
        
        for package_name in package_names:
            installations = []
            
            # First, check history for any packages that might be installed
            # but not found by currently enabled managers
            history_installations = self._check_history_for_package(package_name)
            installations.extend(history_installations)
            
            # Check each enabled package manager
            for manager_name, manager in self.package_manager_registry.get_enabled_managers().items():
                try:
                    # Try to search for the package to see if it's available/installed
                    search_result = manager.search(package_name, {})
                    if search_result.success and search_result.packages:
                        # Check if any of the found packages match our search
                        for package in search_result.packages:
                            if package_name.lower() in package.get('name', '').lower():
                                installations.append({
                                    'manager': manager_name,
                                    'package_name': package.get('name', package_name),
                                    'display_name': package.get('name', package_name),
                                    'version': package.get('version', 'unknown'),
                                    'description': package.get('description', ''),
                                    'size': package.get('size', 'unknown'),
                                    'installed': package.get('installed', False),
                                    'source': 'live_manager'
                                })
                                break
                except Exception as e:
                    self.logger.debug(f"Error checking {package_name} in {manager_name}: {e}")
            
            # Remove duplicates and filter out already removed packages
            unique_installations = []
            seen_managers = set()
            
            for install in installations:
                manager_key = f"{install['manager']}_{install['package_name']}"
                if manager_key not in seen_managers:
                    seen_managers.add(manager_key)
                    unique_installations.append(install)
            
            if len(unique_installations) > 1:
                multi_installations[package_name] = unique_installations
        
        return multi_installations
    
    def _check_history_for_package(self, package_name: str) -> List[Dict[str, Any]]:
        """Check history for packages that might not be found by enabled managers"""
        installations = []
        
        # Get all installations from history
        all_installations = self.history_manager.get_all_installations()
        
        for installation in all_installations:
            # Skip if already marked as removed
            if installation.get('removed', False):
                continue
            
            # Check if this installation contains our package
            if package_name in installation['packages']:
                manager_name = installation['manager']
                
                # Check if the manager is currently enabled
                manager_instance = self.package_manager_registry.get_manager(manager_name)
                manager_enabled = manager_instance and manager_instance.is_enabled()
                
                # If manager is disabled, include it in results with a note
                if not manager_enabled:
                    installations.append({
                        'manager': manager_name,
                        'package_name': package_name,
                        'display_name': package_name,
                        'version': installation.get('version', 'unknown'),
                        'description': f"Installed via {manager_name} (manager currently disabled)",
                        'size': installation.get('size', 'unknown'),
                        'installed': True,
                        'source': 'history',
                        'manager_disabled': True,
                        'installation_timestamp': installation.get('timestamp', 'unknown')
                    })
                else:
                    # Manager is enabled, check if package is still actually installed
                    try:
                        status = self.history_manager.check_package_status(
                            package_name, manager_name, installation.get('scope', 'user')
                        )
                        
                        if status['found_in_history'] and not status['still_installed']:
                            # Package was in history but is no longer installed
                            # Mark it as removed in history
                            self.history_manager.mark_packages_removed(
                                manager_name, [package_name], installation.get('scope', 'user')
                            )
                            continue  # Skip this installation
                        
                    except Exception as e:
                        self.logger.debug(f"Error checking package status for {package_name} in {manager_name}: {e}")
        
        return installations
    
    def _handle_multi_installation_removal(self, multi_installations: Dict[str, List[Dict[str, Any]]], options: Dict[str, Any]) -> int:
        """Handle removal when multiple installations are detected"""
        self.ui_manager.info("\nMultiple installations detected:")
        self.ui_manager.info("=" * 40)
        
        for package_name, installations in multi_installations.items():
            self.ui_manager.info(f"\n{package_name.upper()}:")
            
            for i, install in enumerate(installations, 1):
                status_icon = "✓" if install['manager'] in ['dnf', 'apt', 'pacman'] else "📦"
                self.ui_manager.info(f"  {i}. {status_icon} {install['display_name']} ({install['manager']}) - {install['version']}")
                if install['description']:
                    self.ui_manager.info(f"      {install['description']}")
        
        self.ui_manager.info("\nRemoval options:")
        self.ui_manager.info("1. Remove specific version(s)")
        self.ui_manager.info("2. Remove all versions")
        self.ui_manager.info("3. Cancel")
        
        choice = self.ui_manager.prompt("Enter your choice (1-3): ")
        
        if choice == '1':
            return self._selective_removal(multi_installations, options)
        elif choice == '2':
            return self._remove_all_versions(multi_installations, options)
        else:
            self.ui_manager.info("Operation cancelled")
            return 0
    
    def _selective_removal(self, multi_installations: Dict[str, List[Dict[str, Any]]], options: Dict[str, Any]) -> int:
        """Handle selective removal of specific versions"""
        for package_name, installations in multi_installations.items():
            self.ui_manager.info(f"\nSelect versions of {package_name} to remove:")
            
            # Show options
            for i, install in enumerate(installations, 1):
                status_icon = "✓" if install['manager'] in ['dnf', 'apt', 'pacman'] else "📦"
                self.ui_manager.info(f"  {i}. {status_icon} {install['display_name']} ({install['manager']})")
            
            self.ui_manager.info(f"  {len(installations) + 1}. Skip this package")
            
            # Get user selection
            selection = self.ui_manager.prompt("Enter version numbers (comma-separated) or 'all': ")
            
            if selection.lower() == 'all':
                # Remove all versions
                for install in installations:
                    self._remove_specific_package(install, options)
            elif selection.strip() == str(len(installations) + 1):
                # Skip this package
                continue
            else:
                # Remove selected versions
                try:
                    selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
                    for idx in selected_indices:
                        if 0 <= idx < len(installations):
                            self._remove_specific_package(installations[idx], options)
                except ValueError:
                    self.ui_manager.error("Invalid selection")
                    return 1
        
        return 0
    
    def _remove_specific_package(self, installation: Dict[str, Any], options: Dict[str, Any]) -> int:
        """Remove a specific package installation"""
        manager_name = installation['manager']
        package_name = installation['package_name']
        
        self.ui_manager.info(f"Removing {package_name} ({manager_name})...")
        
        # Create manager-specific options
        manager_options = options.copy()
        manager_options['manager'] = manager_name
        
        # Remove using the specific manager
        result = self.command_handlers.handle_remove([package_name], manager_options)
        
        # If removal was successful, mark it as removed in history
        if result == 0:
            # Determine scope based on the installation source
            scope = 'system' if installation.get('source') == 'history' and 'system' in installation.get('description', '') else 'user'
            
            # Mark as removed in history
            self.history_manager.mark_packages_removed(manager_name, [package_name], scope)
            
            # If this was from a disabled manager, show a note
            if installation.get('manager_disabled', False):
                self.ui_manager.info(f"Note: {manager_name} manager is currently disabled. Re-enable it to manage future {manager_name} packages.")
        
        return result
    
    def _remove_all_versions(self, multi_installations: Dict[str, List[Dict[str, Any]]], options: Dict[str, Any]) -> int:
        """Remove all versions of packages"""
        self.ui_manager.warning("This will remove ALL versions of the specified packages!")
        
        if not self.ui_manager.confirm("Are you sure you want to continue?"):
            self.ui_manager.info("Operation cancelled")
            return 0
        
        for package_name, installations in multi_installations.items():
            self.ui_manager.info(f"Removing all versions of {package_name}...")
            
            for install in installations:
                self._remove_specific_package(install, options)
        
        return 0 

    def _handle_reconcile(self, args: List[str], options: Dict[str, Any]) -> int:
        """Handle package status reconciliation"""
        scope = 'system' if options.get('system', False) else 'user'
        
        self.ui_manager.info(f"Reconciling package status for {scope} scope...")
        self.ui_manager.info("This will check if packages in history are still actually installed.")
        
        if not options.get('yes', False):
            if not self.ui_manager.confirm("Proceed with reconciliation?"):
                return 0
        
        # Run reconciliation
        results = self.history_manager.reconcile_package_status(scope)
        
        # Display results
        self.ui_manager.info(f"\nReconciliation Results:")
        self.ui_manager.info(f"  Packages checked: {results['checked']}")
        self.ui_manager.info(f"  Packages marked as removed: {results['marked_removed']}")
        self.ui_manager.info(f"  Errors encountered: {results['errors']}")
        
        if results['details']:
            self.ui_manager.info(f"\nDetails:")
            for detail in results['details']:
                if detail['action'] == 'marked_removed':
                    self.ui_manager.info(f"  ✓ {detail['package']} ({detail['manager']}) - {detail['reason']}")
                elif detail['action'] == 'error':
                    self.ui_manager.error(f"  ✗ {detail['package']} ({detail['manager']}) - {detail['error']}")
        
        if results['marked_removed'] > 0:
            self.ui_manager.success(f"Successfully updated history with {results['marked_removed']} removed packages")
        
        return 0 