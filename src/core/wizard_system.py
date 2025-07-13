#!/usr/bin/env python3
"""
Wizard System Module

Handles guided configuration wizards and setup flows for PAKA.
"""

import logging
from typing import Dict, List, Any


class WizardSystem:
    """Handles configuration wizards and setup flows"""
    
    def __init__(self, engine):
        """Initialize wizard system with engine reference"""
        self.engine = engine
        self.ui_manager = engine.ui_manager
        self.config_manager = engine.config_manager
        self.package_managers = engine.package_managers
        self.plugin_manager = engine.plugin_manager
        self.shell_integration = engine.shell_integration
        self.logger = logging.getLogger(__name__)
    
    def run_configuration_wizard(self) -> int:
        """Run guided configuration wizard"""
        self.ui_manager.info("\nPAKA Configuration Wizard")
        self.ui_manager.info("=" * 30)
        self.ui_manager.info("This wizard will help you configure PAKA step by step.")
        
        # Step 1: Package Manager Detection
        self.ui_manager.info("\nStep 1: Package Manager Detection")
        self.ui_manager.info("-" * 30)
        self._detect_and_configure_package_managers()
        
        # Step 2: Basic Settings
        self.ui_manager.info("\nStep 2: Basic Settings")
        self.ui_manager.info("-" * 30)
        self._configure_basic_settings()
        
        # Step 3: Health Check Preferences
        self.ui_manager.info("\nStep 3: Health Check Preferences")
        self.ui_manager.info("-" * 30)
        self._configure_health_preferences()
        
        # Step 4: Shell Integration
        self.ui_manager.info("\nStep 4: Shell Integration")
        self.ui_manager.info("-" * 30)
        self._configure_shell_integration_wizard()
        
        # Step 5: Plugin Setup
        self.ui_manager.info("\nStep 5: Plugin Setup")
        self.ui_manager.info("-" * 30)
        self._configure_plugins_wizard()
        
        self.ui_manager.success("\nConfiguration wizard completed!")
        self.ui_manager.info("You can run 'paka config' anytime to modify settings.")
        return 0
    
    def _detect_and_configure_package_managers(self):
        """Detect and configure available package managers"""
        self.ui_manager.info("Detecting available package managers...")
        
        available_managers = {}
        for name, manager in self.package_managers.items():
            if manager.is_available():
                available_managers[name] = manager
                self.ui_manager.info(f"✓ Found {name.upper()}")
            else:
                self.ui_manager.info(f"✗ {name.upper()} not available")
        
        if not available_managers:
            self.ui_manager.warning("No package managers detected!")
            return 0
        
        self.ui_manager.info(f"\nFound {len(available_managers)} package manager(s)")
        
        # Ask user which managers to enable
        self.ui_manager.info("\nWhich package managers would you like to enable?")
        for i, (name, manager) in enumerate(available_managers.items(), 1):
            current_status = "enabled" if manager.is_enabled() else "disabled"
            self.ui_manager.info(f"{i}. {name.upper()} (currently {current_status})")
        
        choice = self.ui_manager.prompt("Enter numbers separated by commas (or 'all'): ")
        
        if choice.lower() == 'all':
            for name in available_managers:
                self.config_manager.enable_package_manager(name)
        else:
            try:
                selected = [int(x.strip()) - 1 for x in choice.split(',')]
                manager_names = list(available_managers.keys())
                for idx in selected:
                    if 0 <= idx < len(manager_names):
                        self.config_manager.enable_package_manager(manager_names[idx])
            except ValueError:
                self.ui_manager.error("Invalid input, keeping current settings")
        
        return 0
    
    def _configure_basic_settings(self):
        """Configure basic PAKA settings"""
        config = self.config_manager.load_config()
        settings = config.get('settings', {})
        
        # Auto confirm
        current_auto_confirm = settings.get('auto_confirm', False)
        auto_confirm = self.ui_manager.prompt_yes_no(
            f"Auto-confirm operations? (current: {current_auto_confirm}): ",
            current_auto_confirm
        )
        settings['auto_confirm'] = auto_confirm
        
        # Verbose output
        current_verbose = settings.get('verbose', False)
        verbose = self.ui_manager.prompt_yes_no(
            f"Verbose output? (current: {current_verbose}): ",
            current_verbose
        )
        settings['verbose'] = verbose
        
        # Color output
        current_color = settings.get('color_output', True)
        color = self.ui_manager.prompt_yes_no(
            f"Color output? (current: {current_color}): ",
            current_color
        )
        settings['color_output'] = color
        
        # Interactive mode
        current_interactive = settings.get('interactive', True)
        interactive = self.ui_manager.prompt_yes_no(
            f"Interactive mode? (current: {current_interactive}): ",
            current_interactive
        )
        settings['interactive'] = interactive
        
        # Save settings
        config['settings'] = settings
        self.config_manager._save_config(config)
        self.ui_manager.success("Basic settings configured")
        return 0
    
    def _configure_health_preferences(self):
        """Configure health check preferences"""
        config = self.config_manager.load_config()
        health_config = config.get('health_checks', {})
        
        # Auto fix
        current_auto_fix = health_config.get('auto_fix', False)
        auto_fix = self.ui_manager.prompt_yes_no(
            f"Auto-fix health issues? (current: {current_auto_fix}): ",
            current_auto_fix
        )
        health_config['auto_fix'] = auto_fix
        
        # Check interval
        current_interval = health_config.get('check_interval', 7)
        interval_str = self.ui_manager.prompt(f"Health check interval in days (current: {current_interval}): ")
        try:
            interval = int(interval_str) if interval_str.strip() else current_interval
            health_config['check_interval'] = interval
        except ValueError:
            self.ui_manager.error("Invalid interval, keeping current value")
        
        # Save health config
        config['health_checks'] = health_config
        self.config_manager._save_config(config)
        self.ui_manager.success("Health check preferences configured")
        return 0
    
    def _configure_shell_integration_wizard(self):
        """Configure shell integration in wizard mode"""
        self.ui_manager.info("Shell integration provides command suggestions when commands are not found.")
        
        install_integration = self.ui_manager.prompt_yes_no(
            "Would you like to install shell integration?", True
        )
        
        if install_integration:
            self.shell_integration.install_integration()
            self.ui_manager.success("Shell integration installed")
        else:
            self.ui_manager.info("Shell integration skipped")
        
        return 0
    
    def _configure_plugins_wizard(self):
        """Configure plugins in wizard mode"""
        self.ui_manager.info("Plugins allow you to customize PAKA's behavior.")
        self.ui_manager.info("You can create plugins for notifications, logging, backups, and more.")
        
        create_sample_plugin = self.ui_manager.prompt_yes_no(
            "Would you like to create a sample notification plugin?", False
        )
        
        if create_sample_plugin:
            plugin_name = "sample-notifications"
            if self.plugin_manager.create_plugin_template(plugin_name, 'runtime', 'user'):
                self.ui_manager.success(f"Sample plugin '{plugin_name}' created")
                self.ui_manager.info("Edit the plugin configuration to customize it")
            else:
                self.ui_manager.error("Failed to create sample plugin")
        else:
            self.ui_manager.info("Sample plugin creation skipped")
        
        return 0 