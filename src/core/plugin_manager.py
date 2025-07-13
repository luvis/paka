#!/usr/bin/env python3
"""
Simple Plugin System for PAKA

A user-friendly plugin system that allows anyone to create plugins using simple templates.
No programming knowledge required - just uncomment lines and add commands!
"""

import os
import sys
import json
import logging
import subprocess
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from .config import ConfigManager
from .ui import UIManager
from .directories import DirectoryManager
from .privilege import PrivilegeManager


class PluginEvent:
    """Available plugin events"""
    # Search events
    PRE_SEARCH = 'pre-search'                    # Before searching for packages
    SEARCH_SUCCESS = 'search-success'            # Package found during search
    SEARCH_FAILURE = 'search-failure'            # Package not found during search
    POST_SEARCH = 'post-search'                  # After search operation (regardless of result)
    
    # Installation events
    PRE_INSTALL = 'pre-install'                  # Before installing packages
    PRE_INSTALL_SUCCESS = 'pre-install-success'  # Package found and about to be installed
    POST_INSTALL_SUCCESS = 'post-install-success' # After successful installation
    POST_INSTALL_FAILURE = 'post-install-failure' # After failed installation
    POST_INSTALL = 'post-install'                # After installation (regardless of result)
    
    # Removal events
    PRE_REMOVE = 'pre-remove'                    # Before removing packages
    PRE_REMOVE_SUCCESS = 'pre-remove-success'    # Package found and about to be removed
    POST_REMOVE_SUCCESS = 'post-remove-success'  # After successful removal
    POST_REMOVE_FAILURE = 'post-remove-failure'  # After failed removal
    POST_REMOVE = 'post-remove'                  # After removal (regardless of result)
    
    # Purge events
    PRE_PURGE = 'pre-purge'                      # Before purging packages
    PRE_PURGE_SUCCESS = 'pre-purge-success'      # Package found and about to be purged
    POST_PURGE_SUCCESS = 'post-purge-success'    # After successful purge
    POST_PURGE_FAILURE = 'post-purge-failure'    # After failed purge
    POST_PURGE = 'post-purge'                    # After purge (regardless of result)
    
    # Upgrade events
    PRE_UPGRADE = 'pre-upgrade'                  # Before upgrading packages
    PRE_UPGRADE_SUCCESS = 'pre-upgrade-success'  # Upgrades available and about to be applied
    POST_UPGRADE_SUCCESS = 'post-upgrade-success' # After successful upgrade
    POST_UPGRADE_FAILURE = 'post-upgrade-failure' # After failed upgrade
    POST_UPGRADE = 'post-upgrade'                # After upgrade (regardless of result)
    
    # Update events
    PRE_UPDATE = 'pre-update'                    # Before updating package lists
    POST_UPDATE_SUCCESS = 'post-update-success'  # After successful update
    POST_UPDATE_FAILURE = 'post-update-failure'  # After failed update
    POST_UPDATE = 'post-update'                  # After update (regardless of result)
    
    # Health events
    PRE_HEALTH = 'pre-health'                    # Before health check operation
    HEALTH_CHECK = 'health-check'                # During health checks
    HEALTH_FIX = 'health-fix'                    # When fixing health issues
    POST_HEALTH_SUCCESS = 'post-health-success'  # After successful health operation
    POST_HEALTH_FAILURE = 'post-health-failure'  # After failed health operation
    POST_HEALTH = 'post-health'                  # After health operation (regardless of result)
    
    # Session events
    SESSION_START = 'session-start'              # When PAKA starts
    SESSION_END = 'session-end'                  # When PAKA ends
    
    # Error events
    ERROR = 'error'                              # When any error occurs
    WARNING = 'warning'                          # When any warning occurs
    
    # Configuration events
    CONFIG_CHANGED = 'config-changed'            # When configuration is modified
    PLUGIN_ENABLED = 'plugin-enabled'            # When a plugin is enabled
    PLUGIN_DISABLED = 'plugin-disabled'          # When a plugin is disabled
    
    # Package manager events
    MANAGER_DETECTED = 'manager-detected'        # When a package manager is detected
    MANAGER_ENABLED = 'manager-enabled'          # When a package manager is enabled
    MANAGER_DISABLED = 'manager-disabled'        # When a package manager is disabled
    
    # History events
    HISTORY_RECORDED = 'history-recorded'        # When an operation is recorded in history
    HISTORY_CLEARED = 'history-cleared'          # When history is cleared
    
    # Cache events
    CACHE_UPDATED = 'cache-updated'              # When package cache is updated
    CACHE_CLEARED = 'cache-cleared'              # When package cache is cleared


class SimplePlugin:
    """Simple plugin that anyone can create and modify"""
    
    def __init__(self, name: str, plugin_dir: Path):
        """Initialize plugin"""
        self.name = name
        self.plugin_dir = plugin_dir
        self.config_file = plugin_dir / 'plugin.conf'
        self.enabled = True
        self.logger = logging.getLogger(f"paka.plugin.{name}")
        self.ui_manager = UIManager()
        
        # Load plugin configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load plugin configuration"""
        config = {
            'enabled': True,
            'description': '',
            'version': '1.0.0',
            'author': '',
            'events': {}
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    lines = f.readlines()
                
                current_event = None
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse metadata
                    if line.startswith('description='):
                        config['description'] = line.split('=', 1)[1]
                    elif line.startswith('version='):
                        config['version'] = line.split('=', 1)[1]
                    elif line.startswith('author='):
                        config['author'] = line.split('=', 1)[1]
                    elif line.startswith('enabled='):
                        config['enabled'] = line.split('=', 1)[1].lower() == 'true'
                    
                    # Parse events
                    elif line.startswith('[') and line.endswith(']'):
                        current_event = line[1:-1]
                        config['events'][current_event] = []
                    
                    # Parse actions
                    elif current_event and line.startswith('action='):
                        action = line.split('=', 1)[1]
                        config['events'][current_event].append(action)
            
            except Exception as e:
                self.logger.error(f"Error loading plugin config: {e}")
        
        return config
    
    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self.config.get('enabled', True)
    
    def handle_event(self, event: str, context: Dict[str, Any]) -> bool:
        """Handle a plugin event"""
        if not self.is_enabled():
            return True
        
        if event in self.config.get('events', {}):
            actions = self.config['events'][event]
            for action in actions:
                if not self._execute_action(action, context):
                    return False
        
        return True
    
    def _execute_action(self, action: str, context: Dict[str, Any]) -> bool:
        """Execute a plugin action"""
        try:
            # Expand variables in action
            expanded_action = self._expand_variables(action, context)
            
            # Execute the action
            if expanded_action.startswith('run:'):
                return self._run_command(expanded_action[4:])
            elif expanded_action.startswith('script:'):
                return self._run_script(expanded_action[7:])
            elif expanded_action.startswith('notify:'):
                return self._send_notification(expanded_action[7:])
            elif expanded_action.startswith('log:'):
                return self._log_message(expanded_action[4:])
            else:
                # Default to running as command
                return self._run_command(expanded_action)
        
        except Exception as e:
            self.logger.error(f"Error executing action '{action}': {e}")
            return False
    
    def _run_command(self, command: str) -> bool:
        """Run a shell command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                self.logger.error(f"Command failed: {result.stderr}")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error running command: {e}")
            return False
    
    def _run_script(self, script_path: str) -> bool:
        """Run a script file"""
        try:
            script_file = self.plugin_dir / script_path
            if not script_file.exists():
                self.logger.error(f"Script not found: {script_file}")
                return False
            
            # Make script executable
            os.chmod(script_file, 0o755)
            
            result = subprocess.run(
                [str(script_file)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                self.logger.error(f"Script failed: {result.stderr}")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error running script: {e}")
            return False
    
    def _send_notification(self, message: str) -> bool:
        """Send a desktop notification"""
        try:
            # Try different notification commands
            commands = [
                ['notify-send', 'PAKA', message],
['zenity', '--info', '--text', message, '--title', 'PAKA'],
['kdialog', '--title', 'PAKA', '--msgbox', message]
            ]
            
            for cmd in commands:
                if shutil.which(cmd[0]):
                    subprocess.run(cmd, capture_output=True)
                    return True
            
            # Fallback to echo if no notification system available
            print(f"PAKA: {message}")
            return True
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            return False
    
    def _log_message(self, message: str) -> bool:
        """Log a message to plugin log"""
        try:
            log_file = self.plugin_dir / 'plugin.log'
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(log_file, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
            return True
        except Exception as e:
            self.logger.error(f"Error logging message: {e}")
            return False
    
    def _expand_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Expand variables in text"""
        # Package manager variables
        text = text.replace('$package-manager', context.get('package_manager', ''))
        text = text.replace('$packages', ' '.join(context.get('packages', [])))
        text = text.replace('$package-count', str(len(context.get('packages', []))))
        
        # Operation variables
        text = text.replace('$operation', context.get('operation', ''))
        text = text.replace('$success', str(context.get('success', False)))
        text = text.replace('$error', context.get('error', ''))
        
        # System variables
        text = text.replace('$user', os.getenv('USER', ''))
        text = text.replace('$home', os.getenv('HOME', ''))
        text = text.replace('$hostname', os.getenv('HOSTNAME', ''))
        
        # Plugin variables
        text = text.replace('$plugin-name', self.name)
        text = text.replace('$plugin-dir', str(self.plugin_dir))
        
        # Timestamp variables
        text = text.replace('$timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        text = text.replace('$date', datetime.now().strftime('%Y-%m-%d'))
        text = text.replace('$time', datetime.now().strftime('%H:%M:%S'))
        
        return text


class PluginManager:
    """Manages PAKA plugins"""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize plugin manager"""
        self.config_manager = config_manager
        self.directory_manager = DirectoryManager()
        self.privilege_manager = PrivilegeManager()
        self.plugins: Dict[str, SimplePlugin] = {}
        self.logger = logging.getLogger('paka.plugin_manager')
        self.ui_manager = UIManager()
        
        # Load all plugins
        self._load_plugins()
        
        # Clean up any missing plugins
        self._cleanup_missing_plugins()
    
    def _load_plugins(self):
        """Load all plugins from the plugins directories"""
        plugin_dirs = self.config_manager.get_plugin_directories()
        
        # Load system plugins first (lower priority)
        if 'system' in plugin_dirs and plugin_dirs['system'].exists():
            self._load_plugins_from_dir(plugin_dirs['system'], 'system')
        
        # Load user plugins (higher priority, can override system plugins)
        if 'user' in plugin_dirs and plugin_dirs['user'].exists():
            self._load_plugins_from_dir(plugin_dirs['user'], 'user')
    
    def _load_plugins_from_dir(self, plugin_dir: Path, prefix: str = ''):
        """Load plugins from a specific directory"""
        for item in plugin_dir.iterdir():
            if item.is_dir() and (item / 'plugin.conf').exists():
                try:
                    plugin_name = item.name
                    if prefix:
                        plugin_name = f"{prefix}-{item.name}"
                    
                    plugin = SimplePlugin(plugin_name, item)
                    self.plugins[plugin_name] = plugin
                    self.logger.info(f"Loaded plugin: {plugin_name}")
                except Exception as e:
                    self.logger.error(f"Error loading plugin {item.name}: {e}")
    
    def _cleanup_missing_plugins(self):
        """Remove references to plugins that no longer exist"""
        # Get list of enabled plugins from config
        enabled_plugins = self._get_enabled_plugins_from_config()
        
        for plugin_name in enabled_plugins:
            if plugin_name not in self.plugins:
                self.logger.warning(f"Plugin '{plugin_name}' not found - deactivating")
                self._remove_plugin_from_config(plugin_name)
    
    def _get_enabled_plugins_from_config(self) -> List[str]:
        """Get list of enabled plugins from the main config"""
        try:
            config = self.config_manager.load_config()
            return config.get('enabled_plugins', [])
        except Exception:
            return []
    
    def _remove_plugin_from_config(self, plugin_name: str):
        """Remove plugin from main config"""
        try:
            config = self.config_manager.load_config()
            enabled_plugins = config.get('enabled_plugins', [])
            if plugin_name in enabled_plugins:
                enabled_plugins.remove(plugin_name)
                config['enabled_plugins'] = enabled_plugins
                self.config_manager._save_config(config)
        except Exception as e:
            self.logger.error(f"Error removing plugin from config: {e}")
    
    def _add_plugin_to_config(self, plugin_name: str):
        """Add plugin to main config"""
        try:
            config = self.config_manager.load_config()
            enabled_plugins = config.get('enabled_plugins', [])
            if plugin_name not in enabled_plugins:
                enabled_plugins.append(plugin_name)
                config['enabled_plugins'] = enabled_plugins
                self.config_manager._save_config(config)
        except Exception as e:
            self.logger.error(f"Error adding plugin to config: {e}")
    
    def get_plugin(self, name: str) -> Optional[SimplePlugin]:
        """Get a specific plugin"""
        return self.plugins.get(name)
    
    def get_enabled_plugins(self) -> Dict[str, SimplePlugin]:
        """Get all enabled plugins"""
        return {name: plugin for name, plugin in self.plugins.items() if plugin.is_enabled()}
    
    def get_disabled_plugins(self) -> Dict[str, SimplePlugin]:
        """Get all disabled plugins"""
        return {name: plugin for name, plugin in self.plugins.items() if not plugin.is_enabled()}
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all plugins with their status"""
        plugins_list = []
        for name, plugin in self.plugins.items():
            plugins_list.append({
                'name': name,
                'enabled': plugin.is_enabled(),
                'description': plugin.config.get('description', ''),
                'version': plugin.config.get('version', '1.0.0'),
                'author': plugin.config.get('author', ''),
                'events': list(plugin.config.get('events', {}).keys()),
                'scope': 'system' if name.startswith('system-') else 'user'
            })
        return plugins_list
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin"""
        if name == 'all':
            return self._enable_all_plugins()
        
        plugin = self.get_plugin(name)
        if plugin:
            plugin.config['enabled'] = True
            self._save_plugin_config(plugin)
            self._add_plugin_to_config(name)
            return True
        return False
    
    def _enable_all_plugins(self) -> bool:
        """Enable all plugins that have enabled=true in their config"""
        enabled_count = 0
        for plugin in self.plugins.values():
            if plugin.config.get('enabled', False):
                plugin.config['enabled'] = True
                self._save_plugin_config(plugin)
                enabled_count += 1
        
        return enabled_count > 0
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin"""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.config['enabled'] = False
            self._save_plugin_config(plugin)
            self._remove_plugin_from_config(name)
            return True
        return False
    
    def _save_plugin_config(self, plugin: SimplePlugin):
        """Save plugin configuration"""
        try:
            config_lines = []
            
            # Add metadata
            config_lines.append(f"description={plugin.config.get('description', '')}")
            config_lines.append(f"version={plugin.config.get('version', '1.0.0')}")
            config_lines.append(f"author={plugin.config.get('author', '')}")
            config_lines.append(f"enabled={plugin.config.get('enabled', True)}")
            config_lines.append("")
            
            # Add events and actions
            for event, actions in plugin.config.get('events', {}).items():
                config_lines.append(f"[{event}]")
                for action in actions:
                    config_lines.append(f"action={action}")
                config_lines.append("")
            
            with open(plugin.config_file, 'w') as f:
                f.write('\n'.join(config_lines))
        
        except Exception as e:
            self.logger.error(f"Error saving plugin config: {e}")
    
    def trigger_event(self, event: str, context: Dict[str, Any]) -> bool:
        """Trigger an event for all enabled plugins"""
        success = True
        for plugin in self.get_enabled_plugins().values():
            if not plugin.handle_event(event, context):
                success = False
        return success
    
    def _execute_action(self, action: str, context: Dict[str, Any]) -> bool:
        """Execute a plugin action (wrapper for testing)"""
        # Create a temporary plugin to execute the action
        temp_plugin = SimplePlugin('temp', Path('/tmp'))
        return temp_plugin._execute_action(action, context)
    
    def _substitute_variables(self, action: str, context: Dict[str, Any]) -> str:
        """Substitute variables in action (wrapper for testing)"""
        # Create a temporary plugin to substitute variables
        temp_plugin = SimplePlugin('temp', Path('/tmp'))
        return temp_plugin._expand_variables(action, context)
    
    def show_plugin_help(self):
        """Show comprehensive plugin help"""
        help_text = """
PAKA Plugin System

PAKA plugins allow you to run custom actions during package operations. Plugins use a simple INI configuration format.

TEMPLATE GENERATOR:
The 'paka config plugins create' command generates a template file for you to edit. This is not an interactive wizard - you'll need to edit the generated file manually.

TYPES OF PLUGINS:
1. Runtime Plugins - Actions that happen during PAKA operations
2. Health Check Plugins - Custom health checks and fixes
3. Package Manager Plugins - Support for custom package managers

AVAILABLE EVENTS:

SEARCH EVENTS:
- pre-search: Before searching for packages
- search-success: Package found during search
- search-failure: Package not found during search
- post-search: After search operation (regardless of result)

INSTALLATION EVENTS:
- pre-install: Before installing packages
- pre-install-success: Package found and about to be installed
- post-install-success: After successful installation
- post-install-failure: After failed installation
- post-install: After installation (regardless of result)

REMOVAL EVENTS:
- pre-remove: Before removing packages
- pre-remove-success: Package found and about to be removed
- post-remove-success: After successful removal
- post-remove-failure: After failed removal
- post-remove: After removal (regardless of result)

PURGE EVENTS:
- pre-purge: Before purging packages
- pre-purge-success: Package found and about to be purged
- post-purge-success: After successful purge
- post-purge-failure: After failed purge
- post-purge: After purge (regardless of result)

UPGRADE EVENTS:
- pre-upgrade: Before upgrading packages
- pre-upgrade-success: Upgrades available and about to be applied
- post-upgrade-success: After successful upgrade
- post-upgrade-failure: After failed upgrade
- post-upgrade: After upgrade (regardless of result)

UPDATE EVENTS:
- pre-update: Before updating package lists
- post-update-success: After successful update
- post-update-failure: After failed update
- post-update: After update (regardless of result)

HEALTH EVENTS:
- pre-health: Before health check operation
- health-check: During health checks
- health-fix: When fixing health issues
- post-health-success: After successful health operation
- post-health-failure: After failed health operation
- post-health: After health operation (regardless of result)

SESSION EVENTS:
- session-start: When PAKA starts
- session-end: When PAKA ends

ERROR EVENTS:
- error: When any error occurs
- warning: When any warning occurs

CONFIGURATION EVENTS:
- config-changed: When configuration is modified
- plugin-enabled: When a plugin is enabled
- plugin-disabled: When a plugin is disabled

PACKAGE MANAGER EVENTS:
- manager-detected: When a package manager is detected
- manager-enabled: When a package manager is enabled
- manager-disabled: When a package manager is disabled

HISTORY EVENTS:
- history-recorded: When an operation is recorded in history
- history-cleared: When history is cleared

CACHE EVENTS:
- cache-updated: When package cache is updated
- cache-cleared: When package cache is cleared

AVAILABLE VARIABLES:
- $packages: List of packages being processed
- $package-count: Number of packages
- $package-manager: Name of the package manager
- $operation: Current operation (install, remove, upgrade, etc.)
- $success: Whether the operation succeeded (true/false)
- $error: Error message if operation failed
- $warning: Warning message if operation had warnings
- $user: Current username
- $home: User's home directory
- $hostname: System hostname
- $timestamp: Current timestamp
- $date: Current date
- $time: Current time

ACTION TYPES:
- run:command - Execute a shell command
- script:filename - Run a script file
- notify:message - Send a desktop notification
- log:message - Log a message

EXAMPLES:

1. Smart Snapper Plugin (only snapshots when packages are found):
   [pre-install-success]
   action=run:snapper create --description "Before install $packages"
   
   [post-install-success]
   action=run:snapper create --description "After successful install $packages"
   
   [post-install-failure]
   action=run:snapper create --description "After failed install $packages (rollback point)"

2. Health Check Snapshot Plugin:
   [pre-health]
   action=run:snapper create --description "Before health check"
   
   [post-health-success]
   action=run:snapper create --description "After successful health check"

3. Search Notification Plugin:
   [search-success]
   action=notify:Found packages: $packages
   
   [search-failure]
   action=notify:No packages found for: $packages

4. Error Logging Plugin:
   [error]
   action=log:Error occurred: $error
   action=run:echo "[$timestamp] ERROR: $error" >> ~/paka-errors.log

5. Session Logger Plugin:
   [session-start]
   action=run:echo "[$timestamp] PAKA session started" >> ~/paka-sessions.log
   
   [session-end]
   action=run:echo "[$timestamp] PAKA session ended" >> ~/paka-sessions.log

CREATING A PLUGIN:
1. Run: paka config plugins create
2. Choose plugin type and name
3. Edit the generated plugin.conf file
4. Uncomment and modify the actions you want
5. Enable the plugin: paka config plugins enable plugin-name
"""
        self.ui_manager.info(help_text)
    
    def syntax_check_plugins(self) -> Dict[str, List[str]]:
        """Check syntax of all plugins"""
        results = {}
        for name, plugin in self.plugins.items():
            errors = []
            
            # Check if config file exists
            if not plugin.config_file.exists():
                errors.append("Plugin configuration file missing")
                continue
            
            # Check if plugin is properly configured
            if not plugin.config.get('name'):
                errors.append("Plugin name not specified")
            
            # Check events and actions
            for event, actions in plugin.config.get('events', {}).items():
                if not actions:
                    errors.append(f"Event '{event}' has no actions")
                
                for action in actions:
                    if not action.startswith(('run:', 'script:', 'notify:', 'log:')):
                        errors.append(f"Invalid action format: {action}")
            
            if errors:
                results[name] = errors
        
        return results
    
    def create_plugin_template(self, plugin_name: str, plugin_type: str = 'runtime', scope: str = 'user') -> bool:
        """Create a new plugin template"""
        try:
            # Determine plugin directory based on scope
            if scope == 'system':
                plugin_dir = self.config_manager.directory_manager.get_system_plugins_dir() / plugin_name
            else:
                plugin_dir = self.config_manager.directory_manager.get_user_plugins_dir() / plugin_name
            
            # Create plugin directory
            plugin_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate template based on plugin type
            if plugin_type == 'runtime':
                template = self._generate_runtime_template(plugin_name)
                config_file = plugin_dir / 'plugin.conf'
                with open(config_file, 'w') as f:
                    f.write(template)
            elif plugin_type == 'health':
                template = self._generate_health_template(plugin_name)
                config_file = plugin_dir / 'plugin.conf'
                with open(config_file, 'w') as f:
                    f.write(template)
            elif plugin_type == 'package_manager':
                template = self._generate_package_manager_template(plugin_name)
                config_file = plugin_dir / 'plugin.conf'
                with open(config_file, 'w') as f:
                    f.write(template)
            elif plugin_type == 'advanced':
                # Create advanced Python plugin
                self._create_advanced_plugin_files(plugin_dir, plugin_name)
            else:
                template = self._generate_runtime_template(plugin_name)
                config_file = plugin_dir / 'plugin.conf'
                with open(config_file, 'w') as f:
                    f.write(template)
            
            # Create README file
            readme_file = plugin_dir / 'README.md'
            readme_content = f"""# {plugin_name.title()} Plugin

This plugin was created using PAKA's plugin template system.

## Configuration

Edit the `plugin.conf` file to customize the plugin behavior.

## Events

This plugin responds to the following events:
- See the `plugin.conf` file for configured events

## Actions

Available action types:
- `run:command` - Execute a shell command
- `script:filename` - Run a script file
- `notify:message` - Send a desktop notification
- `log:message` - Log a message

## Variables

Available variables:
- `$packages` - List of packages being processed
- `$package-manager` - Name of the package manager
- `$timestamp` - Current timestamp
- `$user` - Current username
- And many more...

## Enabling

To enable this plugin:
```bash
paka config plugins enable {plugin_name}
```

## Testing

Test your plugin by running PAKA operations and checking the plugin log file.
"""
            
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            
            self.logger.info(f"Created plugin template: {plugin_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating plugin template: {e}")
            return False
    
    def _generate_runtime_template(self, plugin_name: str) -> str:
        """Generate runtime plugin template"""
        return f"""# {plugin_name.title()} Plugin Configuration

# Plugin metadata
name={plugin_name}
description=Runtime plugin for {plugin_name}
version=1.0.0
author=Your Name
enabled=false

# Post-install actions (after installing packages)
[post-install-success]
# Uncomment and modify the actions you want:
# action=notify:Successfully installed $packages!
# action=run:echo "Installed $packages at $timestamp" >> ~/paka-history.log

# Post-remove actions (after removing packages)
[post-remove-success]
# Uncomment and modify the actions you want:
# action=notify:Successfully removed $packages!
# action=run:echo "Removed $packages at $timestamp" >> ~/paka-history.log

# Error handling
[error]
# Uncomment and modify the actions you want:
# action=notify:An error occurred: $error
# action=run:echo "[$timestamp] ERROR: $error" >> ~/paka-errors.log

# Session events
[session-start]
# Uncomment and modify the actions you want:
# action=run:echo "[$timestamp] PAKA session started" >> ~/paka-sessions.log

[session-end]
# Uncomment and modify the actions you want:
# action=run:echo "[$timestamp] PAKA session ended" >> ~/paka-sessions.log
"""
    
    def _generate_health_template(self, plugin_name: str) -> str:
        """Generate health check plugin template"""
        return f"""# {plugin_name.title()} Health Check Plugin Configuration

# Plugin metadata
name={plugin_name}
description=Health check plugin for {plugin_name}
version=1.0.0
author=Your Name
enabled=false

# Pre-health actions (before applying health fixes)
[pre-health]
# Uncomment and modify the actions you want:
# action=run:snapper create --description "Before applying health fixes"
# action=notify:Starting health check...

# Health check actions (during health checks)
[health-check]
# Uncomment and modify the actions you want:
# action=run:df -h | grep -E "(/$|/home)" >> /tmp/paka-health.log

# Health fix actions (when fixing health issues)
[health-fix]
# Uncomment and modify the actions you want:
# action=run:find /tmp -type f -atime +7 -delete 2>/dev/null || true
# action=notify:Applied custom health fixes

# Post-health actions (after health operations)
[post-health-success]
# Uncomment and modify the actions you want:
# action=notify:Health check completed successfully!
# action=run:echo "[$timestamp] Health check successful" >> ~/paka-health.log

[post-health-failure]
# Uncomment and modify the actions you want:
# action=notify:Health check failed: $error
# action=run:echo "[$timestamp] Health check failed: $error" >> ~/paka-health.log
"""
    
    def _generate_package_manager_template(self, plugin_name: str) -> str:
        """Generate package manager plugin template"""
        return f"""# {plugin_name.title()} Package Manager Plugin Configuration

# Plugin metadata
name={plugin_name}
description=Package manager plugin for {plugin_name}
version=1.0.0
author=Your Name
enabled=false

# Package manager detection
[manager-detected]
# Uncomment and modify the actions you want:
# action=log:Detected package manager: $package-manager
# action=notify:Found package manager: $package-manager

# Package manager enabled
[manager-enabled]
# Uncomment and modify the actions you want:
# action=log:Enabled package manager: $package-manager
# action=notify:Enabled package manager: $package-manager

# Package manager disabled
[manager-disabled]
# Uncomment and modify the actions you want:
# action=log:Disabled package manager: $package-manager
# action=notify:Disabled package manager: $package-manager

# Installation events
[post-install-success]
# Uncomment and modify the actions you want:
# action=log:Successfully installed $packages using $package-manager
# action=notify:Installed $packages via $package-manager

# Removal events
[post-remove-success]
# Uncomment and modify the actions you want:
# action=log:Successfully removed $packages using $package-manager
# action=notify:Removed $packages via $package-manager
""" 

    def _create_advanced_plugin_files(self, plugin_dir: Path, plugin_name: str):
        """Create advanced Python plugin files"""
        # Create __init__.py
        init_content = f'''"""
{plugin_name.title()} Advanced Plugin for PAKA

This is an advanced Python-based plugin that provides custom functionality.
"""

from .{plugin_name}_manager import {plugin_name.title()}Manager

__all__ = ['{plugin_name.title()}Manager']
'''
        
        with open(plugin_dir / '__init__.py', 'w') as f:
            f.write(init_content)
        
        # Create main plugin file
        manager_content = f'''#!/usr/bin/env python3
"""
{plugin_name.title()} Advanced Plugin for PAKA

This plugin demonstrates how to create advanced Python-based plugins
that can implement custom package managers, repository managers, or other
complex functionality.
"""

import subprocess
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.core.advanced_plugins.base import BasePackageManager


class {plugin_name.title()}Manager(BasePackageManager):
    """Advanced {plugin_name.title()} package manager plugin"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.{plugin_name}_command = '{plugin_name}'
        self.installed_packages = set()
        self._load_installed_packages()
    
    def initialize(self) -> bool:
        """Initialize the {plugin_name.title()} plugin"""
        if not self._is_{plugin_name}_available():
            self.logger.warning("{plugin_name.title()} not available")
            return False
        
        try:
            # Test {plugin_name} connection
            result = subprocess.run([self.{plugin_name}_command, '--version'], 
                                  capture_output=True, text=True, check=True)
            self.logger.info("{plugin_name.title()} plugin initialized successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to initialize {plugin_name.title()}: {{e}}")
            return False
    
    def cleanup(self):
        """Cleanup plugin resources"""
        pass
    
    def search(self, query: str, options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for packages using {plugin_name.title()}"""
        if not self._is_{plugin_name}_available():
            return []
        
        options = options or {{}}
        results = []
        
        try:
            # Example search implementation
            result = subprocess.run([
                self.{plugin_name}_command, 'search', query
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse search results
                packages = self._parse_search_output(result.stdout)
                for package in packages:
                    results.append({{
                        'name': package.get('name', ''),
                        'description': package.get('description', ''),
                        'version': package.get('version', 'unknown'),
                        'manager': '{plugin_name}',
                        'size': package.get('size', 'unknown'),
                        'installed': package.get('name', '') in self.installed_packages
                    }})
        except subprocess.TimeoutExpired:
            self.logger.warning("{plugin_name.title()} search timed out")
        except Exception as e:
            self.logger.error(f"Error searching {plugin_name.title()}: {{e}}")
        
        return results
    
    def install(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> bool:
        """Install packages using {plugin_name.title()}"""
        if not self._is_{plugin_name}_available():
            return False
        
        options = options or {{}}
        success = True
        
        for package in packages:
            try:
                self.logger.info(f"Installing {plugin_name.title()} package: {{package}}")
                result = subprocess.run([
                    self.{plugin_name}_command, 'install', package
                ], capture_output=True, text=True, check=True)
                
                # Update installed packages list
                self.installed_packages.add(package)
                self._save_installed_packages()
                
                self.logger.info(f"Successfully installed {plugin_name.title()} package: {{package}}")
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to install {plugin_name.title()} package {{package}}: {{e.stderr}}")
                success = False
        
        return success
    
    def remove(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> bool:
        """Remove packages using {plugin_name.title()}"""
        if not self._is_{plugin_name}_available():
            return False
        
        options = options or {{}}
        success = True
        
        for package in packages:
            try:
                self.logger.info(f"Removing {plugin_name.title()} package: {{package}}")
                result = subprocess.run([
                    self.{plugin_name}_command, 'remove', package
                ], capture_output=True, text=True, check=True)
                
                # Update installed packages list
                if package in self.installed_packages:
                    self.installed_packages.remove(package)
                    self._save_installed_packages()
                
                self.logger.info(f"Successfully removed {plugin_name.title()} package: {{package}}")
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to remove {plugin_name.title()} package {{package}}: {{e.stderr}}")
                success = False
        
        return success
    
    def update(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Update package lists using {plugin_name.title()}"""
        if not self._is_{plugin_name}_available():
            return False
        
        try:
            result = subprocess.run([
                self.{plugin_name}_command, 'update'
            ], capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to update {plugin_name.title()}: {{e.stderr}}")
            return False
    
    def upgrade(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Upgrade installed packages using {plugin_name.title()}"""
        if not self._is_{plugin_name}_available():
            return False
        
        options = options or {{}}
        success = True
        
        try:
            self.logger.info(f"Upgrading {plugin_name.title()} packages")
            result = subprocess.run([
                self.{plugin_name}_command, 'upgrade'
            ], capture_output=True, text=True, check=True)
            
            self.logger.info(f"Successfully upgraded {plugin_name.title()} packages")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to upgrade {plugin_name.title()} packages: {{e.stderr}}")
            success = False
        
        return success
    
    def list_installed(self, options: Optional[Dict[str, Any]] = None) -> List[str]:
        """List installed {plugin_name.title()} packages"""
        return list(self.installed_packages)
    
    def get_package_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a {plugin_name.title()} package"""
        if not self._is_{plugin_name}_available():
            return None
        
        try:
            result = subprocess.run([
                self.{plugin_name}_command, 'info', package_name
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                return {{
                    'name': package_name,
                    'info': result.stdout,
                    'manager': '{plugin_name}'
                }}
        except subprocess.CalledProcessError:
            pass
        
        return None
    
    def check_updates(self) -> List[Dict[str, Any]]:
        """Check for available {plugin_name.title()} updates"""
        if not self._is_{plugin_name}_available():
            return []
        
        updates = []
        try:
            result = subprocess.run([
                self.{plugin_name}_command, 'list-updates'
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                # Parse update list
                for line in result.stdout.strip().split('\\n'):
                    if line.strip():
                        updates.append({{
                            'name': line.strip(),
                            'manager': '{plugin_name}',
                            'current_version': 'unknown',
                            'available_version': 'unknown'
                        }})
        except subprocess.CalledProcessError:
            pass
        
        return updates
    
    def _is_{plugin_name}_available(self) -> bool:
        """Check if {plugin_name.title()} is available on the system"""
        import shutil
        return shutil.which(self.{plugin_name}_command) is not None
    
    def _load_installed_packages(self):
        """Load list of installed packages"""
        # This is a placeholder - implement based on your package manager
        # You might read from a file, database, or query the package manager
        pass
    
    def _save_installed_packages(self):
        """Save list of installed packages"""
        # This is a placeholder - implement based on your package manager
        # You might write to a file, database, or update the package manager
        pass
    
    def _parse_search_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse search output from {plugin_name.title()}"""
        packages = []
        # This is a placeholder - implement based on your package manager's output format
        # Example parsing logic:
        for line in output.strip().split('\\n'):
            if line.strip():
                # Parse line and extract package info
                packages.append({{
                    'name': line.strip(),
                    'version': 'unknown',
                    'description': '',
                    'size': 'unknown'
                }})
        return packages


def register_handlers(plugin):
    """Register plugin handlers with PAKA"""
    # This function is called by PAKA to register the plugin
    # You can add any initialization logic here
    pass
'''
        
        with open(plugin_dir / f'{plugin_name}_manager.py', 'w') as f:
            f.write(manager_content)
        
        # Create configuration file
        config_content = f'''# {plugin_name.title()} Advanced Plugin Configuration

# Plugin metadata
name={plugin_name}
description=Advanced {plugin_name.title()} package manager plugin
version=1.0.0
author=Your Name
enabled=false

# Advanced plugin settings
plugin_type=advanced
python_module={plugin_name}_manager
class_name={plugin_name.title()}Manager

# Package manager specific settings
command={plugin_name}
search_timeout=30
install_timeout=300
update_timeout=60

# Repository settings
default_repositories=
    https://example.com/{plugin_name}/stable
    https://example.com/{plugin_name}/testing

# Advanced options
auto_update=true
cache_packages=true
verify_signatures=true
'''
        
        with open(plugin_dir / 'config.json', 'w') as f:
            f.write(config_content) 