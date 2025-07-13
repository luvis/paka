"""
Configuration management for PAKA
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .directories import DirectoryManager
from .privilege import PrivilegeManager

@dataclass
class PackageManagerConfig:
    """Configuration for a single package manager"""
    name: str
    enabled: bool = True
    priority: int = 0
    command: str = ""
    search_flags: Optional[List[str]] = None
    install_flags: Optional[List[str]] = None
    remove_flags: Optional[List[str]] = None
    purge_flags: Optional[List[str]] = None
    update_flags: Optional[List[str]] = None
    upgrade_flags: Optional[List[str]] = None
    check_updates_flags: Optional[List[str]] = None
    auto_confirm_flag: Optional[str] = None
    
    def __post_init__(self):
        if self.search_flags is None:
            self.search_flags = []
        if self.install_flags is None:
            self.install_flags = []
        if self.remove_flags is None:
            self.remove_flags = []
        if self.purge_flags is None:
            self.purge_flags = []
        if self.update_flags is None:
            self.update_flags = []
        if self.upgrade_flags is None:
            self.upgrade_flags = []
        if self.check_updates_flags is None:
            self.check_updates_flags = []

@dataclass
class PluginConfig:
    """Configuration for a plugin"""
    name: str
    enabled: bool = False
    description: str = ""
    dependencies: Optional[List[str]] = None
    hooks: Optional[List[str]] = None  # pre-install, post-install, pre-remove, etc.
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.hooks is None:
            self.hooks = []

class Config:
    """Main configuration class for PAKA"""
    
    def __init__(self, config_path: Optional[str] = None, scope: str = 'user'):
        """Initialize configuration with directory and privilege managers"""
        self.directory_manager = DirectoryManager()
        self.privilege_manager = PrivilegeManager()
        self.scope = scope
        
        # Determine effective directories based on scope and privileges
        if scope == 'system' and not self.privilege_manager.is_root():
            # Fall back to user scope if not root
            self.scope = 'user'
        
        self.config_dir = self._get_effective_config_dir()
        self.config_file = self.directory_manager.get_config_file(self.scope)
        self.history_dir = self.directory_manager.get_history_file(self.scope).parent
        self.plugins_dir = self.directory_manager.get_effective_plugins_dir()
        
        if config_path:
            self.config_file = Path(config_path)
        
        # Create directories if they don't exist and we can write to them
        if self.directory_manager.can_write_to_directory(self.config_dir):
            self.config_dir.mkdir(parents=True, exist_ok=True)
        if self.directory_manager.can_write_to_directory(self.history_dir):
            self.history_dir.mkdir(parents=True, exist_ok=True)
        if self.directory_manager.can_write_to_directory(self.plugins_dir):
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = self._load_config()
    
    def _get_effective_config_dir(self) -> Path:
        """Get effective configuration directory based on scope and privileges"""
        if self.scope == 'system':
            return self.directory_manager.get_system_config_dir()
        else:
            return self.directory_manager.get_user_config_dir()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
                return self._get_default_config()
        else:
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration with all package managers"""
        return {
            "package_managers": {
                # Fedora/RHEL/CentOS
                "dnf": {
                    "name": "dnf",
                    "enabled": True,
                    "priority": 1,
                    "command": "dnf",
                    "search_flags": ["search"],
                    "install_flags": ["install"],
                    "remove_flags": ["remove"],
                    "purge_flags": ["remove", "--purge"],
                    "update_flags": ["makecache"],
                    "upgrade_flags": ["upgrade"],
                    "check_updates_flags": ["check-update"],
                    "auto_confirm_flag": "-y"
                },
                # Debian/Ubuntu
                "apt": {
                    "name": "apt",
                    "enabled": True,
                    "priority": 2,
                    "command": "apt",
                    "search_flags": ["search"],
                    "install_flags": ["install"],
                    "remove_flags": ["remove"],
                    "purge_flags": ["purge"],
                    "update_flags": ["update"],
                    "upgrade_flags": ["upgrade"],
                    "check_updates_flags": ["list", "--upgradable"],
                    "auto_confirm_flag": "-y"
                },
                # Arch Linux
                "pacman": {
                    "name": "pacman",
                    "enabled": True,
                    "priority": 3,
                    "command": "pacman",
                    "search_flags": ["-Ss"],
                    "install_flags": ["-S"],
                    "remove_flags": ["-R"],
                    "purge_flags": ["-Rns"],
                    "update_flags": ["-Sy"],
                    "upgrade_flags": ["-Syu"],
                    "check_updates_flags": ["-Qu"],
                    "auto_confirm_flag": "--noconfirm"
                },
                # openSUSE
                "zypper": {
                    "name": "zypper",
                    "enabled": True,
                    "priority": 4,
                    "command": "zypper",
                    "search_flags": ["search"],
                    "install_flags": ["install"],
                    "remove_flags": ["remove"],
                    "purge_flags": ["remove", "--clean-deps"],
                    "update_flags": ["refresh"],
                    "upgrade_flags": ["update"],
                    "check_updates_flags": ["list-updates"],
                    "auto_confirm_flag": "-y"
                },
                # Gentoo
                "emerge": {
                    "name": "emerge",
                    "enabled": True,
                    "priority": 5,
                    "command": "emerge",
                    "search_flags": ["-s"],
                    "install_flags": ["-a"],
                    "remove_flags": ["-C"],
                    "purge_flags": ["-C"],
                    "update_flags": ["--sync"],
                    "upgrade_flags": ["-u", "world"],
                    "check_updates_flags": ["-u", "--pretend", "world"],
                    "auto_confirm_flag": "--ask=n"
                },
                # AUR helper
                "yay": {
                    "name": "yay",
                    "enabled": True,
                    "priority": 6,
                    "command": "yay",
                    "search_flags": ["-Ss"],
                    "install_flags": ["-S"],
                    "remove_flags": ["-R"],
                    "purge_flags": ["-Rns"],
                    "update_flags": ["-Sy"],
                    "upgrade_flags": ["-Syu"],
                    "check_updates_flags": ["-Qu"],
                    "auto_confirm_flag": "--noconfirm"
                },
                # Slackware
                "slackpkg": {
                    "name": "slackpkg",
                    "enabled": True,
                    "priority": 7,
                    "command": "slackpkg",
                    "search_flags": ["search"],
                    "install_flags": ["install"],
                    "remove_flags": ["remove"],
                    "purge_flags": ["remove"],
                    "update_flags": ["update"],
                    "upgrade_flags": ["upgrade-all"],
                    "check_updates_flags": ["check-updates"],
                    "auto_confirm_flag": "-batch=on"
                },
                # Alpine
                "apk": {
                    "name": "apk",
                    "enabled": True,
                    "priority": 8,
                    "command": "apk",
                    "search_flags": ["search"],
                    "install_flags": ["add"],
                    "remove_flags": ["del"],
                    "purge_flags": ["del"],
                    "update_flags": ["update"],
                    "upgrade_flags": ["upgrade"],
                    "check_updates_flags": ["version"],
                    "auto_confirm_flag": "--no-cache"
                },
                # Void Linux
                "xbps": {
                    "name": "xbps",
                    "enabled": True,
                    "priority": 9,
                    "command": "xbps-install",
                    "search_flags": ["-s"],
                    "install_flags": ["-S"],
                    "remove_flags": ["-R"],
                    "purge_flags": ["-R"],
                    "update_flags": ["-S"],
                    "upgrade_flags": ["-Su"],
                    "check_updates_flags": ["-un"],
                    "auto_confirm_flag": "-y"
                },
                # Vanilla OS
                "apx": {
                    "name": "apx",
                    "enabled": True,
                    "priority": 10,
                    "command": "apx",
                    "search_flags": ["search"],
                    "install_flags": ["install"],
                    "remove_flags": ["remove"],
                    "purge_flags": ["remove"],
                    "update_flags": ["update"],
                    "upgrade_flags": ["upgrade"],
                    "check_updates_flags": ["update", "--check"],
                    "auto_confirm_flag": "-y"
                },
                # Universal
                "flatpak": {
                    "name": "flatpak",
                    "enabled": True,
                    "priority": 11,
                    "command": "flatpak",
                    "search_flags": ["search"],
                    "install_flags": ["install"],
                    "remove_flags": ["uninstall"],
                    "purge_flags": ["uninstall"],
                    "update_flags": ["update"],
                    "upgrade_flags": ["update"],
                    "check_updates_flags": ["update", "--dry-run"],
                    "auto_confirm_flag": "-y"
                },
                # Universal
                "snap": {
                    "name": "snap",
                    "enabled": True,
                    "priority": 12,
                    "command": "snap",
                    "search_flags": ["search"],
                    "install_flags": ["install"],
                    "remove_flags": ["remove"],
                    "purge_flags": ["remove", "--purge"],
                    "update_flags": ["refresh"],
                    "upgrade_flags": ["refresh"],
                    "check_updates_flags": ["refresh", "--list"],
                    "auto_confirm_flag": "--classic"
                },
                "appimage": {
                    "name": "appimage",
                    "enabled": False,  # Disabled by default
                    "priority": 5,  # High priority for AppImages
                    "command": "appimage",
                    "description": "Revolutionary AppImage package manager",
                    "repositories": {
                        "appimagehub": {
                            "url": "https://appimage.github.io/apps",
                            "type": "appimagehub",
                            "enabled": True
                        },
                        "github": {
                            "url": "https://api.github.com/search/repositories",
                            "type": "github",
                            "enabled": True
                        },
                        "flathub": {
                            "url": "https://flathub.org/api/v1/apps",
                            "type": "flathub",
                            "enabled": True
                        }
                    }
                }
            },
            "plugins": {
                "snapper": {
                    "name": "snapper",
                    "enabled": False,
                    "description": "Create system snapshots before/after package operations",
                    "dependencies": ["snapper"],
                    "hooks": ["pre-install", "post-install", "pre-remove", "post-remove"]
                },
                "docker": {
                    "name": "docker",
                    "enabled": False,
                    "description": "Use Docker as a package manager for containerized applications",
                    "dependencies": ["docker"],
                    "hooks": []
                }
            },
            "settings": {
                "auto_confirm": False,
                "verbose": False,
                "default_install_type": "recommended",
                "interactive": True,
                "parallel_operations": True,
                "history_max_entries": 1000,
                "session_learning": True,
                "color_output": True
            },
            "installation_preferences": {
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
        }
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get_package_manager_config(self, name: str) -> Optional[PackageManagerConfig]:
        """Get configuration for a specific package manager"""
        if name in self.config["package_managers"]:
            pm_config = self.config["package_managers"][name]
            return PackageManagerConfig(**pm_config)
        return None
    
    def get_enabled_package_managers(self) -> List[PackageManagerConfig]:
        """Get list of enabled package managers sorted by priority"""
        enabled = []
        for name, config in self.config["package_managers"].items():
            if config.get("enabled", True):
                pm_config = PackageManagerConfig(**config)
                enabled.append(pm_config)
        
        return sorted(enabled, key=lambda x: x.priority)
    
    def get_enabled_plugins(self) -> List[PluginConfig]:
        """Get list of enabled plugins"""
        enabled = []
        for name, config in self.config["plugins"].items():
            if config.get("enabled", False):
                plugin_config = PluginConfig(**config)
                enabled.append(plugin_config)
        
        return enabled
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.config["settings"].get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value"""
        self.config["settings"][key] = value
        self._save_config(self.config)
    
    def enable_package_manager(self, name: str):
        """Enable a package manager"""
        if name in self.config["package_managers"]:
            self.config["package_managers"][name]["enabled"] = True
            self._save_config(self.config)
    
    def disable_package_manager(self, name: str):
        """Disable a package manager"""
        if name in self.config["package_managers"]:
            self.config["package_managers"][name]["enabled"] = False
            self._save_config(self.config)
    
    def enable_plugin(self, name: str):
        """Enable a plugin"""
        if name in self.config["plugins"]:
            self.config["plugins"][name]["enabled"] = True
            self._save_config(self.config)
    
    def disable_plugin(self, name: str):
        """Disable a plugin"""
        if name in self.config["plugins"]:
            self.config["plugins"][name]["enabled"] = False
            self._save_config(self.config)


class ConfigManager(Config):
    """Configuration manager that provides the expected interface for the engine"""
    
    def __init__(self, config_path: Optional[str] = None, scope: str = 'user'):
        """Initialize the config manager"""
        super().__init__(config_path, scope)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration"""
        return self.config
    
    def get_log_dir(self) -> Path:
        """Get log directory"""
        if self.scope == 'system':
            return self.directory_manager.get_system_log_dir()
        else:
            return self.directory_manager.get_user_log_dir()
    
    def get_history_file(self) -> Path:
        """Get history file path"""
        return self.directory_manager.get_history_file(self.scope)
    
    def get_session_file(self) -> Path:
        """Get session file path"""
        return self.directory_manager.get_session_file(self.scope)
    
    def get_plugin_directories(self) -> Dict[str, Path]:
        """Get plugin directories for current scope"""
        return self.directory_manager.get_plugin_directories('all')
    
    def can_access_system_config(self) -> bool:
        """Check if current user can access system configuration"""
        return self.privilege_manager.can_access_system_history()
    
    def get_scope_info(self) -> Dict[str, Any]:
        """Get information about current configuration scope"""
        return {
            'scope': self.scope,
            'is_root': self.privilege_manager.is_root(),
            'config_dir': str(self.config_dir),
            'plugins_dir': str(self.plugins_dir),
            'history_dir': str(self.history_dir),
            'can_write_config': self.directory_manager.can_write_to_directory(self.config_dir),
            'can_write_plugins': self.directory_manager.can_write_to_directory(self.plugins_dir),
            'can_write_history': self.directory_manager.can_write_to_directory(self.history_dir)
        }
    
    def show_config(self):
        """Show current configuration"""
        print(json.dumps(self.config, indent=2))
    
    def edit_config(self):
        """Edit configuration interactively"""
        from .ui import UIManager
        ui = UIManager()
        
        ui.info("PAKA Configuration Editor")
        ui.info("=" * 30)
        
        while True:
            ui.info("\nConfiguration Sections:")
            ui.info("1. Package Managers")
            ui.info("2. Settings")
            ui.info("3. Health Checks")
            ui.info("4. History")
            ui.info("5. Plugins")
            ui.info("6. Save and Exit")
            ui.info("7. Exit without saving")
            
            choice = ui.prompt("Select section to edit (1-7): ")
            
            if choice == '1':
                self._edit_package_managers(ui)
            elif choice == '2':
                self._edit_settings(ui)
            elif choice == '3':
                self._edit_health_checks(ui)
            elif choice == '4':
                self._edit_history(ui)
            elif choice == '5':
                self._edit_plugins(ui)
            elif choice == '6':
                self._save_config(self.config)
                ui.success("Configuration saved successfully")
                break
            elif choice == '7':
                if ui.confirm("Exit without saving changes?"):
                    break
            else:
                ui.error("Invalid choice")
    
    def _edit_package_managers(self, ui):
        """Edit package manager configuration"""
        ui.info("\nPackage Manager Configuration")
        ui.info("-" * 30)
        
        managers = self.config.get('package_managers', {})
        for name, config in managers.items():
            enabled = config.get('enabled', False)
            priority = config.get('priority', 0)
            ui.info(f"{name}: enabled={enabled}, priority={priority}")
            
            if ui.prompt_yes_no(f"Edit {name} configuration?"):
                enabled = ui.prompt_yes_no(f"Enable {name}?", enabled)
                priority_str = ui.prompt(f"Priority (0-100, current: {priority}): ")
                try:
                    priority = int(priority_str) if priority_str.strip() else priority
                except ValueError:
                    ui.error("Invalid priority value, keeping current")
                
                managers[name] = {
                    'enabled': enabled,
                    'priority': priority
                }
    
    def _edit_settings(self, ui):
        """Edit general settings"""
        ui.info("\nGeneral Settings")
        ui.info("-" * 20)
        
        settings = self.config.get('settings', {})
        
        auto_confirm = settings.get('auto_confirm', False)
        auto_confirm = ui.prompt_yes_no(f"Auto-confirm operations (current: {auto_confirm})?", auto_confirm)
        
        verbose = settings.get('verbose', False)
        verbose = ui.prompt_yes_no(f"Verbose output (current: {verbose})?", verbose)
        
        color_output = settings.get('color_output', True)
        color_output = ui.prompt_yes_no(f"Color output (current: {color_output})?", color_output)
        
        settings.update({
            'auto_confirm': auto_confirm,
            'verbose': verbose,
            'color_output': color_output
        })
        
        self.config['settings'] = settings
    
    def _edit_health_checks(self, ui):
        """Edit health check configuration"""
        ui.info("\nHealth Check Configuration")
        ui.info("-" * 30)
        
        health_config = self.config.get('health_checks', {})
        
        auto_fix = health_config.get('auto_fix', False)
        auto_fix = ui.prompt_yes_no(f"Auto-fix issues (current: {auto_fix})?", auto_fix)
        
        check_interval = health_config.get('check_interval', 7)
        interval_str = ui.prompt(f"Check interval in days (current: {check_interval}): ")
        try:
            check_interval = int(interval_str) if interval_str.strip() else check_interval
        except ValueError:
            ui.error("Invalid interval value, keeping current")
        
        health_config.update({
            'auto_fix': auto_fix,
            'check_interval': check_interval
        })
        
        self.config['health_checks'] = health_config
    
    def _edit_history(self, ui):
        """Edit history configuration"""
        ui.info("\nHistory Configuration")
        ui.info("-" * 25)
        
        history_config = self.config.get('history', {})
        
        max_entries = history_config.get('max_entries', 1000)
        max_str = ui.prompt(f"Maximum history entries (current: {max_entries}): ")
        try:
            max_entries = int(max_str) if max_str.strip() else max_entries
        except ValueError:
            ui.error("Invalid value, keeping current")
        
        auto_cleanup = history_config.get('auto_cleanup', True)
        auto_cleanup = ui.prompt_yes_no(f"Auto-cleanup old entries (current: {auto_cleanup})?", auto_cleanup)
        
        history_config.update({
            'max_entries': max_entries,
            'auto_cleanup': auto_cleanup
        })
        
        self.config['history'] = history_config
    
    def _edit_plugins(self, ui):
        """Edit plugin configuration"""
        ui.info("\nPlugin Configuration")
        ui.info("-" * 25)
        
        enabled_plugins = self.config.get('enabled_plugins', [])
        ui.info(f"Currently enabled plugins: {', '.join(enabled_plugins) if enabled_plugins else 'None'}")
        
        if ui.prompt_yes_no("Edit enabled plugins?"):
            ui.info("Enter plugin names to enable (comma-separated, or 'none' for none):")
            plugins_input = ui.prompt("Plugins: ")
            
            if plugins_input.strip().lower() == 'none':
                enabled_plugins = []
            else:
                enabled_plugins = [p.strip() for p in plugins_input.split(',') if p.strip()]
            
            self.config['enabled_plugins'] = enabled_plugins
    
    def reset_config(self):
        """Reset configuration to defaults"""
        default_config = self._get_default_config()
        self._save_config(default_config)
        self.config = default_config
        print("Configuration reset to defaults") 