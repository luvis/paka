#!/usr/bin/env python3
"""
Menu System Module

Handles all interactive menus and user interface flows for PAKA configuration
and management.
"""

import logging
from typing import Dict, List, Any


class MenuSystem:
    """Handles interactive menus and user interface flows"""
    
    def __init__(self, engine):
        """Initialize menu system with engine reference"""
        self.engine = engine
        self.ui_manager = engine.ui_manager
        self.config_manager = engine.config_manager
        self.package_managers = engine.package_managers
        self.plugin_manager = engine.plugin_manager
        self.shell_integration = engine.shell_integration
        self.logger = logging.getLogger(__name__)
    
    def show_config_menu(self) -> int:
        """Show interactive configuration menu with scope support"""
        while True:
            self.ui_manager.display_menu_header("Configuration Menu")
            
            # Show current scope
            scope_info = self.config_manager.get_scope_info()
            self.ui_manager.display_note(f"Current scope: {scope_info['scope']}")
            self.ui_manager.display_note(f"Running as root: {scope_info['is_root']}")
            self.ui_manager.display_note("")
            
            options = [
                "Show configuration",
                "Edit configuration", 
                "Reset configuration",
                "Package managers",
                "Plugins",
                "Preferences",
                "Scope settings",
                "Directory info",
                "Uninstall PAKA",
                "Back to main menu"
            ]
            self.ui_manager.display_menu_options(options)
            
            choice = self.ui_manager.prompt("Enter your choice: ")
            
            if choice == '1':
                self._show_config()
            elif choice == '2':
                self.config_manager.edit_config()
            elif choice == '3':
                self.config_manager.reset_config()
            elif choice == '4':
                self._show_package_manager_menu()
            elif choice == '5':
                self._show_plugin_menu()
            elif choice == '6':
                self._show_preferences_menu()
            elif choice == '7':
                self._show_scope_menu()
            elif choice == '8':
                self._show_directory_info()
            elif choice == '9':
                self._run_uninstaller()
            elif choice == '10':
                return 0
            else:
                self.ui_manager.error("Invalid choice")
    
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
    
    def _show_scope_menu(self) -> int:
        """Show scope configuration menu"""
        while True:
            self.ui_manager.display_menu_header("Scope Configuration")
            
            scope_info = self.config_manager.get_scope_info()
            self.ui_manager.display_note(f"Current scope: {scope_info['scope']}")
            self.ui_manager.display_note(f"Running as root: {scope_info['is_root']}")
            self.ui_manager.display_note("")
            
            options = [
                "Switch to user scope",
                "Switch to system scope",
                "Show scope differences",
                "Back to config menu"
            ]
            self.ui_manager.display_menu_options(options)
            
            choice = self.ui_manager.prompt("Enter your choice: ")
            
            if choice == '1':
                self.config_manager.set_scope('user')
                self.ui_manager.success("Switched to user scope")
            elif choice == '2':
                if scope_info['is_root']:
                    self.config_manager.set_scope('system')
                    self.ui_manager.success("Switched to system scope")
                else:
                    self.ui_manager.error("System scope requires root privileges")
            elif choice == '3':
                self._show_scope_differences()
            elif choice == '4':
                return 0
            else:
                self.ui_manager.error("Invalid choice")
    
    def _show_scope_differences(self):
        """Show differences between user and system scopes"""
        self.ui_manager.info("\nScope Differences")
        self.ui_manager.info("=" * 20)
        
        self.ui_manager.info("User Scope:")
        self.ui_manager.info("  - Configuration: ~/.config/paka/")
        self.ui_manager.info("  - Plugins: ~/.local/share/paka/plugins/")
        self.ui_manager.info("  - History: ~/.local/share/paka/")
        self.ui_manager.info("  - Only affects current user")
        self.ui_manager.info("")
        
        self.ui_manager.info("System Scope:")
        self.ui_manager.info("  - Configuration: /etc/paka/")
        self.ui_manager.info("  - Plugins: /usr/share/paka/plugins/")
        self.ui_manager.info("  - History: /var/lib/paka/")
        self.ui_manager.info("  - Affects all users (requires root)")
    
    def _show_directory_info(self):
        """Show directory information"""
        self.ui_manager.info("\nPAKA Directory Information")
        self.ui_manager.info("=" * 35)
        
        directory_info = self.config_manager.directory_manager.get_directory_info()
        
        for name, info in directory_info.items():
            status = "✓" if info['writable'] else "✗"
            self.ui_manager.info(f"{status} {name}: {info['path']}")
            self.ui_manager.info(f"    Exists: {info['exists']}")
            self.ui_manager.info(f"    Writable: {info['writable']}")
            self.ui_manager.info(f"    Scope: {info['scope']}")
            self.ui_manager.info("")
    
    def _run_uninstaller(self):
        """Run the PAKA uninstaller wizard with granular options"""
        self.ui_manager.info("\nPAKA Uninstaller")
        self.ui_manager.info("=" * 20)
        self.ui_manager.warning("This will completely remove PAKA from your system.")
        self.ui_manager.warning("This action cannot be undone.")
        self.ui_manager.info("")
        
        if not self.ui_manager.confirm("Are you sure you want to uninstall PAKA?"):
            self.ui_manager.info("Uninstallation cancelled")
            return
        
        self.ui_manager.info("\nUninstallation Options:")
        self.ui_manager.info("1. Remove PAKA only (keep user data)")
        self.ui_manager.info("2. Remove PAKA and user data (recommended)")
        self.ui_manager.info("3. Remove PAKA and ALL data (complete cleanup)")
        self.ui_manager.info("4. Granular removal (choose components)")
        
        choice = self.ui_manager.prompt("Choose option (1-4): ")
        
        remove_paka_only = False
        remove_user_data = False
        remove_all_data = False
        granular_mode = False
        
        if choice == '1':
            self.ui_manager.info("Removing PAKA only...")
            remove_paka_only = True
        elif choice == '2':
            self.ui_manager.info("Removing PAKA and user data...")
            remove_user_data = True
        elif choice == '3':
            self.ui_manager.info("Removing PAKA and ALL data...")
            remove_user_data = True
            remove_all_data = True
        elif choice == '4':
            self.ui_manager.info("Granular removal mode...")
            granular_mode = True
        else:
            self.ui_manager.error("Invalid choice")
            return
        
        self.ui_manager.info("Starting uninstallation...")
        
        # Get granular removal choices if needed
        removal_choices = {}
        if granular_mode:
            removal_choices = self._prompt_granular_uninstall()
        
        # Perform removal based on mode
        if granular_mode:
            self._perform_granular_uninstall(removal_choices)
        else:
            self._perform_standard_uninstall(remove_paka_only, remove_user_data, remove_all_data)
        
        self.ui_manager.success("\n╔══════════════════════════════════════════════════════════════╗")
        self.ui_manager.success("║                    Uninstallation Complete!                   ║")
        self.ui_manager.success("╚══════════════════════════════════════════════════════════════╝")
        
        self.ui_manager.success("PAKA has been completely removed from your system.")
        if remove_user_data or granular_mode:
            self.ui_manager.success("All user data and configuration has been removed.")
        if remove_all_data:
            self.ui_manager.success("All system data and configuration has been removed.")
        
        self.ui_manager.info("Note: You may need to restart your shell or run 'source ~/.bashrc'")
        self.ui_manager.info("to remove command completion.")
        
        # Exit the program since PAKA is now uninstalled
        self.ui_manager.info("Exiting PAKA...")
        import sys
        sys.exit(0)
    
    def _prompt_granular_uninstall(self) -> dict:
        """Prompt for granular uninstall options"""
        self.ui_manager.info("\nSelect components to remove (y/n):")
        
        choices = {}
        
        # System components
        choices['rm_bin'] = self.ui_manager.prompt_yes_no("Remove PAKA system executable (/usr/local/bin/paka)?", "n")
        choices['rm_user_bin'] = self.ui_manager.prompt_yes_no("Remove PAKA user executable (~/.local/bin/paka)?", "n")
        choices['rm_sys_py'] = self.ui_manager.prompt_yes_no("Remove PAKA system Python source (/usr/local/share/paka)?", "n")
        choices['rm_user_py'] = self.ui_manager.prompt_yes_no("Remove PAKA user Python source (~/.local/share/paka)?", "n")
        
        # Configuration
        choices['rm_sys_cfg'] = self.ui_manager.prompt_yes_no("Remove system config (/etc/paka)?", "n")
        choices['rm_user_cfg'] = self.ui_manager.prompt_yes_no("Remove user config (~/.config/paka)?", "n")
        
        # Plugins
        choices['rm_sys_plugins'] = self.ui_manager.prompt_yes_no("Remove system plugins (/usr/local/share/paka/plugins)?", "n")
        choices['rm_user_plugins'] = self.ui_manager.prompt_yes_no("Remove user plugins (~/.local/share/paka/plugins)?", "n")
        
        # Data and logs
        choices['rm_user_data'] = self.ui_manager.prompt_yes_no("Remove user data dir (~/.local/share/paka)?", "n")
        choices['rm_user_logs'] = self.ui_manager.prompt_yes_no("Remove PAKA logs (~/.local/share/paka/logs)?", "n")
        
        # Shell integration
        choices['rm_bash_comp'] = self.ui_manager.prompt_yes_no("Remove bash completion (/etc/bash_completion.d/paka.bash)?", "n")
        choices['rm_zsh_comp'] = self.ui_manager.prompt_yes_no("Remove zsh completion (/usr/local/share/zsh/site-functions/_paka)?", "n")
        
        return choices
    
    def _perform_granular_uninstall(self, choices: dict):
        """Perform granular uninstall based on user choices"""
        import os
        import shutil
        
        # Remove system executable
        if choices.get('rm_bin'):
            if os.path.exists("/usr/local/bin/paka"):
                try:
                    os.system("sudo rm -f /usr/local/bin/paka")
                    self.ui_manager.success("✓ Removed system executable")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove system executable: {e}")
        
        # Remove user executable
        if choices.get('rm_user_bin'):
            if os.path.exists(os.path.expanduser("~/.local/bin/paka")):
                try:
                    os.remove(os.path.expanduser("~/.local/bin/paka"))
                    self.ui_manager.success("✓ Removed user executable")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove user executable: {e}")
        
        # Remove system Python source
        if choices.get('rm_sys_py'):
            if os.path.exists("/usr/local/share/paka"):
                try:
                    os.system("sudo rm -rf /usr/local/share/paka")
                    self.ui_manager.success("✓ Removed system Python source")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove system Python source: {e}")
        
        # Remove user Python source
        if choices.get('rm_user_py'):
            if os.path.exists(os.path.expanduser("~/.local/share/paka")):
                try:
                    shutil.rmtree(os.path.expanduser("~/.local/share/paka"))
                    self.ui_manager.success("✓ Removed user Python source")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove user Python source: {e}")
        
        # Remove system configuration
        if choices.get('rm_sys_cfg'):
            if os.path.exists("/etc/paka"):
                try:
                    os.system("sudo rm -rf /etc/paka")
                    self.ui_manager.success("✓ Removed system configuration")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove system configuration: {e}")
        
        # Remove user configuration
        if choices.get('rm_user_cfg'):
            if os.path.exists(os.path.expanduser("~/.config/paka")):
                try:
                    shutil.rmtree(os.path.expanduser("~/.config/paka"))
                    self.ui_manager.success("✓ Removed user configuration")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove user configuration: {e}")
        
        # Remove system plugins
        if choices.get('rm_sys_plugins'):
            if os.path.exists("/usr/local/share/paka/plugins"):
                try:
                    os.system("sudo rm -rf /usr/local/share/paka/plugins")
                    self.ui_manager.success("✓ Removed system plugins")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove system plugins: {e}")
        
        # Remove user plugins
        if choices.get('rm_user_plugins'):
            if os.path.exists(os.path.expanduser("~/.local/share/paka/plugins")):
                try:
                    shutil.rmtree(os.path.expanduser("~/.local/share/paka/plugins"))
                    self.ui_manager.success("✓ Removed user plugins")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove user plugins: {e}")
        
        # Remove user data
        if choices.get('rm_user_data'):
            if os.path.exists(os.path.expanduser("~/.local/share/paka")):
                try:
                    shutil.rmtree(os.path.expanduser("~/.local/share/paka"))
                    self.ui_manager.success("✓ Removed user data directory")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove user data directory: {e}")
        
        # Remove bash completion
        if choices.get('rm_bash_comp'):
            if os.path.exists("/etc/bash_completion.d/paka.bash"):
                try:
                    os.system("sudo rm -f /etc/bash_completion.d/paka.bash")
                    self.ui_manager.success("✓ Removed bash completion")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove bash completion: {e}")
        
        # Remove zsh completion
        if choices.get('rm_zsh_comp'):
            if os.path.exists("/usr/local/share/zsh/site-functions/_paka"):
                try:
                    os.system("sudo rm -f /usr/local/share/zsh/site-functions/_paka")
                    self.ui_manager.success("✓ Removed zsh completion")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove zsh completion: {e}")
        
        # Remove user logs
        if choices.get('rm_user_logs'):
            if os.path.exists(os.path.expanduser("~/.local/share/paka/logs")):
                try:
                    shutil.rmtree(os.path.expanduser("~/.local/share/paka/logs"))
                    self.ui_manager.success("✓ Removed user logs")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove user logs: {e}")
    
    def _perform_standard_uninstall(self, remove_paka_only: bool, remove_user_data: bool, remove_all_data: bool):
        """Perform standard uninstall based on preset options"""
        import os
        import shutil
        
        # Remove executable
        self.ui_manager.info("Removing PAKA executable...")
        if os.path.exists("/usr/local/bin/paka"):
            try:
                os.system("sudo rm -f /usr/local/bin/paka")
                self.ui_manager.success("✓ Removed system executable")
            except Exception as e:
                self.ui_manager.error(f"Failed to remove system executable: {e}")
        
        if os.path.exists(os.path.expanduser("~/.local/bin/paka")):
            try:
                os.remove(os.path.expanduser("~/.local/bin/paka"))
                self.ui_manager.success("✓ Removed user executable")
            except Exception as e:
                self.ui_manager.error(f"Failed to remove user executable: {e}")
        
        # Remove Python source
        self.ui_manager.info("Removing Python source...")
        if os.path.exists("/usr/local/share/paka"):
            try:
                os.system("sudo rm -rf /usr/local/share/paka")
                self.ui_manager.success("✓ Removed system Python source")
            except Exception as e:
                self.ui_manager.error(f"Failed to remove system Python source: {e}")
        
        if os.path.exists(os.path.expanduser("~/.local/share/paka")):
            try:
                shutil.rmtree(os.path.expanduser("~/.local/share/paka"))
                self.ui_manager.success("✓ Removed user Python source")
            except Exception as e:
                self.ui_manager.error(f"Failed to remove user Python source: {e}")
        
        # Remove system configuration
        if remove_all_data:
            self.ui_manager.info("Removing system configuration...")
            if os.path.exists("/etc/paka"):
                try:
                    os.system("sudo rm -rf /etc/paka")
                    self.ui_manager.success("✓ Removed system configuration")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove system configuration: {e}")
        
        # Remove system plugins
        if remove_all_data:
            self.ui_manager.info("Removing system plugins...")
            if os.path.exists("/usr/local/share/paka/plugins"):
                try:
                    os.system("sudo rm -rf /usr/local/share/paka/plugins")
                    self.ui_manager.success("✓ Removed system plugins")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove system plugins: {e}")
        
        # Remove user data
        if remove_user_data:
            self.ui_manager.info("Removing user data...")
            
            if os.path.exists(os.path.expanduser("~/.config/paka")):
                try:
                    shutil.rmtree(os.path.expanduser("~/.config/paka"))
                    self.ui_manager.success("✓ Removed user configuration")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove user configuration: {e}")
            
            if os.path.exists(os.path.expanduser("~/.local/share/paka/plugins")):
                try:
                    shutil.rmtree(os.path.expanduser("~/.local/share/paka/plugins"))
                    self.ui_manager.success("✓ Removed user plugins")
                except Exception as e:
                    self.ui_manager.error(f"Failed to remove user plugins: {e}")
        
        # Remove shell completion
        self.ui_manager.info("Removing shell completion...")
        if os.path.exists("/etc/bash_completion.d/paka.bash"):
            try:
                os.system("sudo rm -f /etc/bash_completion.d/paka.bash")
                self.ui_manager.success("✓ Removed bash completion")
            except Exception as e:
                self.ui_manager.error(f"Failed to remove bash completion: {e}")
        
        if os.path.exists("/usr/local/share/zsh/site-functions/_paka"):
            try:
                os.system("sudo rm -f /usr/local/share/zsh/site-functions/_paka")
                self.ui_manager.success("✓ Removed zsh completion")
            except Exception as e:
                self.ui_manager.error(f"Failed to remove zsh completion: {e}")
    
    def _show_package_manager_menu(self) -> int:
        """Show package manager configuration menu"""
        while True:
            self.ui_manager.display_menu_header("Package Manager Configuration", icon="section")
            enabled_managers = [name for name, manager in self.package_managers.items() if manager.is_enabled()]
            disabled_managers = [name for name, manager in self.package_managers.items() if not manager.is_enabled()]
            self.ui_manager.display_status("Enabled", ', '.join(enabled_managers) if enabled_managers else 'None', status='enabled')
            self.ui_manager.display_status("Disabled", ', '.join(disabled_managers) if disabled_managers else 'None', status='disabled')
            options = [
                "Enable package manager",
                "Disable package manager",
                "Test package manager",
                "Set manager priority",
                "Back to main menu"
            ]
            self.ui_manager.display_menu_options(options)
            choice = self.ui_manager.prompt("Enter choice (1-5)")
            if choice == '1':
                self._enable_package_manager()
            elif choice == '2':
                self._disable_package_manager()
            elif choice == '3':
                self._test_package_manager()
            elif choice == '4':
                self._set_manager_priority()
            elif choice == '5':
                return 0
            else:
                self.ui_manager.error("Invalid choice")
                continue
        return 0
    
    def _enable_package_manager(self):
        """Enable a package manager"""
        disabled_managers = [name for name, manager in self.package_managers.items() 
                           if not manager.is_enabled()]
        
        if not disabled_managers:
            self.ui_manager.info("No disabled package managers found")
            return
        
        self.ui_manager.info("\nDisabled package managers:")
        for i, name in enumerate(disabled_managers, 1):
            self.ui_manager.info(f"{i}. {name.upper()}")
        
        choice = self.ui_manager.prompt("Enter manager number to enable: ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(disabled_managers):
                manager_name = disabled_managers[idx]
                self.config_manager.enable_package_manager(manager_name)
                self.ui_manager.success(f"Package manager '{manager_name.upper()}' enabled")
            else:
                self.ui_manager.error("Invalid manager number")
        except ValueError:
            self.ui_manager.error("Invalid input")
    
    def _disable_package_manager(self):
        """Disable a package manager"""
        enabled_managers = [name for name, manager in self.package_managers.items() 
                          if manager.is_enabled()]
        
        if not enabled_managers:
            self.ui_manager.info("No enabled package managers found")
            return
        
        self.ui_manager.info("\nEnabled package managers:")
        for i, name in enumerate(enabled_managers, 1):
            self.ui_manager.info(f"{i}. {name.upper()}")
        
        choice = self.ui_manager.prompt("Enter manager number to disable: ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(enabled_managers):
                manager_name = enabled_managers[idx]
                self.config_manager.disable_package_manager(manager_name)
                self.ui_manager.success(f"Package manager '{manager_name.upper()}' disabled")
            else:
                self.ui_manager.error("Invalid manager number")
        except ValueError:
            self.ui_manager.error("Invalid input")
    
    def _test_package_manager(self):
        """Test a package manager"""
        all_managers = list(self.package_managers.keys())
        
        self.ui_manager.info("\nAvailable package managers:")
        for i, name in enumerate(all_managers, 1):
            status = "✓ Available" if self.package_managers[name].is_available() else "✗ Not available"
            self.ui_manager.info(f"{i}. {name.upper()} - {status}")
        
        choice = self.ui_manager.prompt("Enter manager number to test: ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(all_managers):
                manager_name = all_managers[idx]
                manager = self.package_managers[manager_name]
                
                if not manager.is_available():
                    self.ui_manager.error(f"{manager_name.upper()} is not available on this system")
                    return
                
                self.ui_manager.info(f"Testing {manager_name.upper()}...")
                result = manager.update({})
                
                if result.success:
                    self.ui_manager.success(f"{manager_name.upper()} is working correctly")
                else:
                    self.ui_manager.error(f"{manager_name.upper()} test failed: {result.error}")
            else:
                self.ui_manager.error("Invalid manager number")
        except ValueError:
            self.ui_manager.error("Invalid input")
    
    def _set_manager_priority(self):
        """Set package manager priority"""
        config = self.config_manager.load_config()
        managers = config.get('package_managers', {})
        
        self.ui_manager.info("\nCurrent priorities (lower = higher priority):")
        for name, manager_config in managers.items():
            priority = manager_config.get('priority', 0)
            self.ui_manager.info(f"{name.upper()}: {priority}")
        
        manager_name = self.ui_manager.prompt("Enter manager name: ").strip().lower()
        if manager_name not in managers:
            self.ui_manager.error("Invalid manager name")
            return
        
        try:
            priority = int(self.ui_manager.prompt("Enter new priority (0-100): "))
            if 0 <= priority <= 100:
                managers[manager_name]['priority'] = priority
                config['package_managers'] = managers
                self.config_manager._save_config(config)
                self.ui_manager.success(f"Priority for {manager_name.upper()} set to {priority}")
            else:
                self.ui_manager.error("Priority must be between 0 and 100")
        except ValueError:
            self.ui_manager.error("Invalid priority value")
    
    def _show_plugin_menu(self) -> int:
        """Show plugin management menu"""
        while True:
            self.ui_manager.display_menu_header("Plugin Management")
            
            # Show plugin status
            enabled_plugins = self.plugin_manager.get_enabled_plugins()
            disabled_plugins = self.plugin_manager.get_disabled_plugins()
            
            self.ui_manager.display_status("Enabled", ', '.join(enabled_plugins.keys()) if enabled_plugins else 'None', status='enabled')
            self.ui_manager.display_status("Disabled", ', '.join(disabled_plugins.keys()) if disabled_plugins else 'None', status='disabled')
            
            options = [
                "List all plugins",
                "Enable plugin",
                "Disable plugin",
                "Create new plugin",
                "Check plugin syntax",
                "Plugin help",
                "Back to config menu"
            ]
            self.ui_manager.display_menu_options(options)
            
            choice = self.ui_manager.prompt("Enter your choice: ")
            
            if choice == '1':
                self._list_plugins()
            elif choice == '2':
                self._enable_plugin()
            elif choice == '3':
                self._disable_plugin()
            elif choice == '4':
                self._create_plugin_template()
            elif choice == '5':
                self._check_plugin_syntax()
            elif choice == '6':
                self.plugin_manager.show_plugin_help()
            elif choice == '7':
                return 0
            else:
                self.ui_manager.error("Invalid choice")
    
    def _list_plugins(self):
        """List all plugins with their status"""
        self.ui_manager.info("\nPlugin Status")
        self.ui_manager.info("=" * 15)
        
        enabled_plugins = self.plugin_manager.get_enabled_plugins()
        disabled_plugins = self.plugin_manager.get_disabled_plugins()
        
        if enabled_plugins:
            self.ui_manager.info("\nEnabled Plugins:")
            for name, plugin in enabled_plugins.items():
                self.ui_manager.info(f"  ✓ {name} - {plugin.config.get('description', 'No description')}")
        
        if disabled_plugins:
            self.ui_manager.info("\nDisabled Plugins:")
            for name, plugin in disabled_plugins.items():
                self.ui_manager.info(f"  ✗ {name} - {plugin.config.get('description', 'No description')}")
        
        if not enabled_plugins and not disabled_plugins:
            self.ui_manager.info("No plugins found")
    
    def _enable_plugin(self):
        """Enable a plugin"""
        disabled_plugins = self.plugin_manager.get_disabled_plugins()
        
        if not disabled_plugins:
            self.ui_manager.info("No disabled plugins found")
            return
        
        self.ui_manager.info("\nDisabled plugins:")
        disabled_list = list(disabled_plugins.items())
        for i, (name, plugin) in enumerate(disabled_list):
            self.ui_manager.info(f"{i}. {name} - {plugin.config.get('description', 'No description')}")
        
        try:
            choice = int(self.ui_manager.prompt("Enter plugin number to enable: "))
            if 0 <= choice < len(disabled_list):
                plugin_name = disabled_list[choice][0]
                
                if self.plugin_manager.enable_plugin(plugin_name):
                    self.ui_manager.success(f"Plugin '{plugin_name}' enabled")
                else:
                    self.ui_manager.error(f"Failed to enable plugin '{plugin_name}'")
            else:
                self.ui_manager.error("Invalid plugin number")
        except ValueError:
            self.ui_manager.error("Invalid input")
    
    def _disable_plugin(self):
        """Disable a plugin"""
        enabled_plugins = self.plugin_manager.get_enabled_plugins()
        
        if not enabled_plugins:
            self.ui_manager.info("No enabled plugins found")
            return
        
        self.ui_manager.info("\nEnabled plugins:")
        enabled_list = list(enabled_plugins.items())
        for i, (name, plugin) in enumerate(enabled_list):
            self.ui_manager.info(f"{i}. {name} - {plugin.config.get('description', 'No description')}")
        
        try:
            choice = int(self.ui_manager.prompt("Enter plugin number to disable: "))
            
            if 0 <= choice < len(enabled_list):
                plugin_name = enabled_list[choice][0]
                
                if self.plugin_manager.disable_plugin(plugin_name):
                    self.ui_manager.success(f"Plugin '{plugin_name}' disabled")
                    
                    # Get plugin info for directory deletion
                    plugin = self.plugin_manager.get_plugin(plugin_name)
                    if plugin:
                        plugin_path = plugin.plugin_dir
                        response = self.ui_manager.prompt_yes_no(
                            f"Do you wish to delete the disabled plugin directory at {plugin_path}?", 
                            False
                        )
                        if response:
                            try:
                                import shutil
                                shutil.rmtree(plugin_path)
                                self.ui_manager.success(f"Plugin directory deleted: {plugin_path}")
                            except Exception as e:
                                self.ui_manager.error(f"Failed to delete plugin directory: {e}")
                                self.ui_manager.display_note(f"To delete manually, run: rm -rf {plugin_path}")
                        else:
                            self.ui_manager.display_note(f"Plugin directory preserved at: {plugin_path}")
                            self.ui_manager.display_note(f"To delete manually, run: rm -rf {plugin_path}")
                else:
                    self.ui_manager.error(f"Failed to disable plugin '{plugin_name}'")
            else:
                self.ui_manager.error("Invalid plugin number")
        except ValueError:
            self.ui_manager.error("Invalid input")
    
    def _check_plugin_syntax(self):
        """Check syntax of all plugins"""
        self.ui_manager.info("\nChecking plugin syntax...")
        
        results = self.plugin_manager.syntax_check_plugins()
        
        if not results:
            self.ui_manager.success("All plugins have valid syntax")
        else:
            self.ui_manager.error("Found syntax errors in plugins:")
            for plugin_name, errors in results.items():
                self.ui_manager.error(f"\n{plugin_name}:")
                for error in errors:
                    self.ui_manager.error(f"  - {error}")
    
    def _create_plugin_template(self):
        """Create a new plugin template"""
        self.ui_manager.info("\nCreate New Plugin")
        self.ui_manager.info("=" * 20)
        
        # Get plugin name
        plugin_name = self.ui_manager.prompt("Enter plugin name: ").strip()
        if not plugin_name:
            self.ui_manager.error("Plugin name is required")
            return
        
        # Get plugin type
        self.ui_manager.info("\nPlugin types:")
        self.ui_manager.info("1. Runtime (actions during operations)")
        self.ui_manager.info("2. Health Check (custom health checks)")
        self.ui_manager.info("3. Package Manager (custom package managers)")
        self.ui_manager.info("4. Advanced (Python-based plugins)")
        
        type_choice = self.ui_manager.prompt("Choose plugin type (1-4): ")
        
        if type_choice == '1':
            plugin_type = 'runtime'
        elif type_choice == '2':
            plugin_type = 'health'
        elif type_choice == '3':
            plugin_type = 'package_manager'
        elif type_choice == '4':
            plugin_type = 'advanced'
        else:
            self.ui_manager.error("Invalid plugin type")
            return
        
        # Get scope
        scope = 'user'  # Default to user scope
        if self.engine.privilege_manager.is_root():
            self.ui_manager.info("\nPlugin scope:")
            self.ui_manager.info("1. User-only (recommended)")
            self.ui_manager.info("2. System-wide")
            
            scope_choice = self.ui_manager.prompt("Choose scope (1-2): ")
            if scope_choice == '2':
                scope = 'system'
        
        # Create the plugin
        if self.plugin_manager.create_plugin_template(plugin_name, plugin_type, scope):
            self.ui_manager.success(f"Plugin template '{plugin_name}' created")
            
            # Show plugin location
            plugin_dirs = self.config_manager.get_plugin_directories()
            if scope == 'system':
                plugin_path = plugin_dirs['system'] / plugin_name
            else:
                plugin_path = plugin_dirs['user'] / plugin_name
            
            self.ui_manager.info(f"Template location: {plugin_path}")
            self.ui_manager.info("Edit plugin.conf to customize your plugin")
            self.ui_manager.info(f"Enable with: paka config plugins enable {plugin_name}")
        else:
            self.ui_manager.error("Failed to create plugin template")
    
    def _show_preferences_menu(self) -> int:
        """Show installation preferences menu"""
        while True:
            self.ui_manager.display_menu_header("Installation Preferences")
            
            # Show current preferences
            config = self.config_manager.load_config()
            prefs = config.get('installation_preferences', {})
            
            self.ui_manager.display_note("Current Preferences:")
            self.ui_manager.display_note(f"  Default dependency level: {prefs.get('default_dependency_level', 'recommended')}")
            self.ui_manager.display_note(f"  Prefer official packages: {prefs.get('prefer_official_packages', True)}")
            self.ui_manager.display_note(f"  Preferred package manager: {prefs.get('preferred_package_manager', 'auto')}")
            self.ui_manager.display_note(f"  Show stability indicators: {prefs.get('show_stability_indicators', True)}")
            self.ui_manager.display_note("")
            
            options = [
                "Set default dependency level",
                "Configure package manager preferences",
                "Edit official packages database",
                "Configure stability indicators",
                "Reset to defaults",
                "Back to config menu"
            ]
            self.ui_manager.display_menu_options(options)
            
            choice = self.ui_manager.prompt("Enter your choice: ")
            
            if choice == '1':
                self._set_dependency_level()
            elif choice == '2':
                self._configure_package_manager_preferences()
            elif choice == '3':
                self._edit_official_packages_database()
            elif choice == '4':
                self._configure_stability_indicators()
            elif choice == '5':
                self._reset_preferences_to_defaults()
            elif choice == '6':
                return 0
            else:
                self.ui_manager.error("Invalid choice")
    
    def _set_dependency_level(self):
        """Set default dependency level"""
        config = self.config_manager.load_config()
        prefs = config.get('installation_preferences', {})
        current_level = prefs.get('default_dependency_level', 'recommended')
        
        self.ui_manager.info(f"\nCurrent default dependency level: {current_level}")
        self.ui_manager.info("")
        self.ui_manager.info("Dependency Levels:")
        self.ui_manager.info("1. minimal - Install only essential dependencies")
        self.ui_manager.info("2. recommended - Install recommended dependencies (default)")
        self.ui_manager.info("3. optional - Install all optional dependencies")
        
        choice = self.ui_manager.prompt("Select dependency level (1-3): ")
        
        level_map = {'1': 'minimal', '2': 'recommended', '3': 'optional'}
        if choice in level_map:
            new_level = level_map[choice]
            prefs['default_dependency_level'] = new_level
            config['installation_preferences'] = prefs
            self.config_manager._save_config(config)
            self.ui_manager.success(f"Default dependency level set to: {new_level}")
        else:
            self.ui_manager.error("Invalid choice")
    
    def _configure_package_manager_preferences(self):
        """Configure package manager preferences"""
        config = self.config_manager.load_config()
        prefs = config.get('installation_preferences', {})
        current_preferred = prefs.get('preferred_package_manager', 'auto')
        current_prefer_official = prefs.get('prefer_official_packages', True)
        
        self.ui_manager.info(f"\nCurrent preferences:")
        self.ui_manager.info(f"  Preferred manager: {current_preferred}")
        self.ui_manager.info(f"  Prefer official packages: {current_prefer_official}")
        self.ui_manager.info("")
        
        # Set preferred package manager
        self.ui_manager.info("Available package managers:")
        managers = list(self.package_managers.keys())
        for i, manager in enumerate(managers, 1):
            self.ui_manager.info(f"  {i}. {manager}")
        self.ui_manager.info(f"  {len(managers) + 1}. auto (let PAKA choose)")
        
        choice = self.ui_manager.prompt("Select preferred package manager: ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(managers):
                prefs['preferred_package_manager'] = managers[idx]
            elif idx == len(managers):
                prefs['preferred_package_manager'] = 'auto'
            else:
                self.ui_manager.error("Invalid choice")
                return
        except ValueError:
            self.ui_manager.error("Invalid input")
            return
        
        # Set official package preference
        prefer_official = self.ui_manager.prompt_yes_no("Prefer official packages over user-contributed ones?", current_prefer_official)
        prefs['prefer_official_packages'] = prefer_official
        
        config['installation_preferences'] = prefs
        self.config_manager._save_config(config)
        self.ui_manager.success("Package manager preferences updated")
    
    def _edit_official_packages_database(self):
        """Edit the official packages database"""
        config = self.config_manager.load_config()
        prefs = config.get('installation_preferences', {})
        official_db = prefs.get('official_packages_database', {})
        
        self.ui_manager.info("\nOfficial Packages Database")
        self.ui_manager.info("=" * 30)
        self.ui_manager.info("This database maps packages to their preferred package managers.")
        self.ui_manager.info("")
        
        if official_db:
            self.ui_manager.info("Current mappings:")
            for package, manager in official_db.items():
                self.ui_manager.info(f"  {package} → {manager}")
        else:
            self.ui_manager.info("No official package mappings defined")
        
        self.ui_manager.info("")
        self.ui_manager.info("Options:")
        self.ui_manager.info("1. Add package mapping")
        self.ui_manager.info("2. Remove package mapping")
        self.ui_manager.info("3. Clear all mappings")
        self.ui_manager.info("4. Back to preferences")
        
        choice = self.ui_manager.prompt("Enter your choice: ")
        
        if choice == '1':
            package = self.ui_manager.prompt("Enter package name: ").strip()
            if package:
                self.ui_manager.info("Available package managers:")
                managers = list(self.package_managers.keys()) + ['official-repo', 'flatpak', 'snap']
                for i, manager in enumerate(managers, 1):
                    self.ui_manager.info(f"  {i}. {manager}")
                
                manager_choice = self.ui_manager.prompt("Select preferred manager: ")
                try:
                    idx = int(manager_choice) - 1
                    if 0 <= idx < len(managers):
                        official_db[package] = managers[idx]
                        prefs['official_packages_database'] = official_db
                        config['installation_preferences'] = prefs
                        self.config_manager._save_config(config)
                        self.ui_manager.success(f"Added mapping: {package} → {managers[idx]}")
                    else:
                        self.ui_manager.error("Invalid choice")
                except ValueError:
                    self.ui_manager.error("Invalid input")
        
        elif choice == '2':
            if official_db:
                package = self.ui_manager.prompt("Enter package name to remove: ").strip()
                if package in official_db:
                    del official_db[package]
                    prefs['official_packages_database'] = official_db
                    config['installation_preferences'] = prefs
                    self.config_manager._save_config(config)
                    self.ui_manager.success(f"Removed mapping for: {package}")
                else:
                    self.ui_manager.error("Package not found in database")
            else:
                self.ui_manager.info("No mappings to remove")
        
        elif choice == '3':
            if self.ui_manager.confirm("Clear all official package mappings?"):
                prefs['official_packages_database'] = {}
                config['installation_preferences'] = prefs
                self.config_manager._save_config(config)
                self.ui_manager.success("All official package mappings cleared")
    
    def _configure_stability_indicators(self):
        """Configure stability indicators"""
        config = self.config_manager.load_config()
        prefs = config.get('installation_preferences', {})
        current_show = prefs.get('show_stability_indicators', True)
        
        self.ui_manager.info(f"\nCurrent setting: Show stability indicators = {current_show}")
        self.ui_manager.info("")
        self.ui_manager.info("Stability indicators show package stability levels:")
        self.ui_manager.info("  ★ Official - From official repositories")
        self.ui_manager.info("  ☆ Community - From community repositories")
        self.ui_manager.info("  ⚠️ Beta - Beta/development versions")
        self.ui_manager.info("  🔺 Alpha - Alpha/experimental versions")
        self.ui_manager.info("")
        
        show_indicators = self.ui_manager.prompt_yes_no("Show stability indicators?", current_show)
        prefs['show_stability_indicators'] = show_indicators
        config['installation_preferences'] = prefs
        self.config_manager._save_config(config)
        self.ui_manager.success(f"Stability indicators {'enabled' if show_indicators else 'disabled'}")
    
    def _reset_preferences_to_defaults(self):
        """Reset installation preferences to defaults"""
        if self.ui_manager.confirm("Reset all installation preferences to defaults?"):
            config = self.config_manager.load_config()
            config['installation_preferences'] = {
                "prefer_official_packages": True,
                "preferred_package_manager": None,
                "default_dependency_level": "recommended",
                "show_stability_indicators": True,
                "official_packages_database": {
                    "bottles": "flatpak",
                    "firefox": "flatpak",
                    "steam": "official-repo",
                    "discord": "flatpak",
                    "spotify": "flatpak",
                    "vscode": "official-repo"
                }
            }
            self.config_manager._save_config(config)
            self.ui_manager.success("Installation preferences reset to defaults")

    def _show_shell_integration_menu(self) -> int:
        """Show shell integration menu"""
        while True:
            self.ui_manager.display_menu_header("Shell Integration")
            
            # Show current status
            self._show_shell_integration_status()
            
            options = [
                "Install shell integration",
                "Remove shell integration",
                "Test shell integration",
                "Configure shell integration",
                "Back to main menu"
            ]
            self.ui_manager.display_menu_options(options)
            
            choice = self.ui_manager.prompt("Enter your choice: ")
            
            if choice == '1':
                self.shell_integration.enable()
            elif choice == '2':
                self.shell_integration.disable()
            elif choice == '3':
                self._test_shell_integration()
            elif choice == '4':
                self._configure_shell_integration()
            elif choice == '5':
                return 0
            else:
                self.ui_manager.error("Invalid choice")
    
    def _show_shell_integration_status(self):
        """Show shell integration status"""
        status = self.shell_integration.get_status()
        
        self.ui_manager.info("\nShell Integration Status:")
        self.ui_manager.info(f"  Enabled: {status['enabled']}")
        self.ui_manager.info(f"  Command not found: {status['command_not_found']}")
        self.ui_manager.info(f"  Suggestions: {status['suggestions']}")
        self.ui_manager.info(f"  Auto install: {status['auto_install']}")
        self.ui_manager.info(f"  Supported shells: {', '.join(status['shells'])}")
        self.ui_manager.info(f"  Suggestion limit: {status['suggestion_limit']}")
        
        # Test if integration is actually working
        if self.shell_integration.test_integration():
            self.ui_manager.success("Shell integration is active and working")
        else:
            self.ui_manager.warning("Shell integration is not properly installed")
    
    def _test_shell_integration(self):
        """Test shell integration"""
        self.ui_manager.info("\nTesting shell integration...")
        
        # Test with a non-existent command
        test_command = "nonexistentcommand12345"
        suggestion = self.shell_integration.handle_command_not_found(test_command)
        
        if suggestion:
            self.ui_manager.success("Shell integration is working")
            self.ui_manager.info(f"Test suggestion: {suggestion}")
        else:
            self.ui_manager.warning("No suggestions found for test command")
    
    def _configure_shell_integration(self):
        """Configure shell integration settings"""
        self.ui_manager.info("\nShell Integration Configuration")
        self.ui_manager.info("=" * 35)
        
        status = self.shell_integration.get_status()
        
        # Configure suggestion limit
        current_limit = status['suggestion_limit']
        new_limit = self.ui_manager.prompt(f"Suggestion limit (current: {current_limit}): ")
        if new_limit.isdigit():
            self.shell_integration.update_config('suggestion_limit', int(new_limit))
        
        # Configure supported shells
        current_shells = status['shells']
        self.ui_manager.info(f"Current supported shells: {', '.join(current_shells)}")
        self.ui_manager.info("Available shells: bash, zsh, fish")
        
        shell_choice = self.ui_manager.prompt("Configure shells (comma-separated, or press Enter to skip): ")
        if shell_choice.strip():
            shells = [s.strip() for s in shell_choice.split(',')]
            self.shell_integration.update_config('shells', shells) 