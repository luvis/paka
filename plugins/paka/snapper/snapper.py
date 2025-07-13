#!/usr/bin/env python3
"""
Snapper Plugin for PAKA

Creates system snapshots before and after package operations and health checks using Snapper.
Features interactive configuration for granular control over snapshot events.
"""

import subprocess
import shutil
import json
from typing import Dict, Any, List
from pathlib import Path


def register_handlers(plugin):
    """Register event handlers for this plugin"""
    
    # Load configuration
    config = _load_snapper_config(plugin)
    
    def handle_pre_install_success(context: Dict[str, Any]) -> bool:
        """Handle pre-install-success event - create snapshot when packages are found and about to be installed"""
        if not config.get('pre_install', True) or not _is_snapper_available():
            return True
        
        packages = context.get('packages', [])
        snapshot_description = f"PAKA pre-install: {', '.join(packages)}"
        
        try:
            result = subprocess.run([
                'snapper', 'create', '--type', 'pre', '--description', snapshot_description
            ], capture_output=True, text=True, check=True)
            
            plugin.logger.info(f"Created pre-install snapshot: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            plugin.logger.error(f"Failed to create pre-install snapshot: {e.stderr}")
            return False
    
    def handle_post_install(context: Dict[str, Any]) -> bool:
        """Handle post-install event - create snapshot"""
        if not config.get('post_install', True) or not _is_snapper_available():
            return True
        
        packages = context.get('packages', [])
        success = context.get('success', True)
        snapshot_description = f"PAKA post-install: {', '.join(packages)} ({'success' if success else 'failure'})"
        
        try:
            result = subprocess.run([
                'snapper', 'create', '--type', 'post', '--description', snapshot_description
            ], capture_output=True, text=True, check=True)
            
            plugin.logger.info(f"Created post-install snapshot: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            plugin.logger.error(f"Failed to create post-install snapshot: {e.stderr}")
            return False
    
    def handle_pre_remove(context: Dict[str, Any]) -> bool:
        """Handle pre-remove event - create snapshot"""
        if not config.get('pre_remove', True) or not _is_snapper_available():
            return True
        
        packages = context.get('packages', [])
        snapshot_description = f"PAKA pre-remove: {', '.join(packages)}"
        
        try:
            result = subprocess.run([
                'snapper', 'create', '--type', 'pre', '--description', snapshot_description
            ], capture_output=True, text=True, check=True)
            
            plugin.logger.info(f"Created pre-remove snapshot: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            plugin.logger.error(f"Failed to create pre-remove snapshot: {e.stderr}")
            return False
    
    def handle_post_remove(context: Dict[str, Any]) -> bool:
        """Handle post-remove event - create snapshot"""
        if not config.get('post_remove', True) or not _is_snapper_available():
            return True
        
        packages = context.get('packages', [])
        success = context.get('success', True)
        snapshot_description = f"PAKA post-remove: {', '.join(packages)} ({'success' if success else 'failure'})"
        
        try:
            result = subprocess.run([
                'snapper', 'create', '--type', 'post', '--description', snapshot_description
            ], capture_output=True, text=True, check=True)
            
            plugin.logger.info(f"Created post-remove snapshot: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            plugin.logger.error(f"Failed to create post-remove snapshot: {e.stderr}")
            return False
    
    def handle_pre_upgrade(context: Dict[str, Any]) -> bool:
        """Handle pre-upgrade event - create snapshot"""
        if not config.get('pre_upgrade', True) or not _is_snapper_available():
            return True
        
        snapshot_description = "PAKA pre-upgrade: system packages"
        
        try:
            result = subprocess.run([
                'snapper', 'create', '--type', 'pre', '--description', snapshot_description
            ], capture_output=True, text=True, check=True)
            
            plugin.logger.info(f"Created pre-upgrade snapshot: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            plugin.logger.error(f"Failed to create pre-upgrade snapshot: {e.stderr}")
            return False
    
    def handle_post_upgrade(context: Dict[str, Any]) -> bool:
        """Handle post-upgrade event - create snapshot"""
        if not config.get('post_upgrade', True) or not _is_snapper_available():
            return True
        
        success = context.get('success', True)
        snapshot_description = f"PAKA post-upgrade: system packages ({'success' if success else 'failure'})"
        
        try:
            result = subprocess.run([
                'snapper', 'create', '--type', 'post', '--description', snapshot_description
            ], capture_output=True, text=True, check=True)
            
            plugin.logger.info(f"Created post-upgrade snapshot: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            plugin.logger.error(f"Failed to create post-upgrade snapshot: {e.stderr}")
            return False
    
    def handle_pre_health(context: Dict[str, Any]) -> bool:
        """Handle pre-health event - create snapshot before health checks"""
        if not config.get('pre_health', True) or not _is_snapper_available():
            return True
        
        snapshot_description = "PAKA pre-health: before system health check"
        
        try:
            result = subprocess.run([
                'snapper', 'create', '--type', 'pre', '--description', snapshot_description
            ], capture_output=True, text=True, check=True)
            
            plugin.logger.info(f"Created pre-health snapshot: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            plugin.logger.error(f"Failed to create pre-health snapshot: {e.stderr}")
            return False
    
    def handle_post_health_success(context: Dict[str, Any]) -> bool:
        """Handle post-health-success event - create snapshot after successful health check"""
        if not config.get('post_health_success', True) or not _is_snapper_available():
            return True
        
        snapshot_description = "PAKA post-health: after successful health check"
        
        try:
            result = subprocess.run([
                'snapper', 'create', '--type', 'post', '--description', snapshot_description
            ], capture_output=True, text=True, check=True)
            
            plugin.logger.info(f"Created post-health-success snapshot: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            plugin.logger.error(f"Failed to create post-health-success snapshot: {e.stderr}")
            return False
    
    def handle_post_health_failure(context: Dict[str, Any]) -> bool:
        """Handle post-health-failure event - create snapshot after failed health check"""
        if not config.get('post_health_failure', True) or not _is_snapper_available():
            return True
        
        snapshot_description = "PAKA post-health: after failed health check (rollback point)"
        
        try:
            result = subprocess.run([
                'snapper', 'create', '--type', 'post', '--description', snapshot_description
            ], capture_output=True, text=True, check=True)
            
            plugin.logger.info(f"Created post-health-failure snapshot: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            plugin.logger.error(f"Failed to create post-health-failure snapshot: {e.stderr}")
            return False
    
    def handle_health_fix(context: Dict[str, Any]) -> bool:
        """Handle health-fix event - create snapshot before applying health fixes"""
        if not config.get('health_fix', True) or not _is_snapper_available():
            return True
        
        fixes = context.get('fixes', [])
        snapshot_description = f"PAKA pre-health-fix: before applying {len(fixes)} fixes"
        
        try:
            result = subprocess.run([
                'snapper', 'create', '--type', 'pre', '--description', snapshot_description
            ], capture_output=True, text=True, check=True)
            
            plugin.logger.info(f"Created pre-health-fix snapshot: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            plugin.logger.error(f"Failed to create pre-health-fix snapshot: {e.stderr}")
            return False
    
    # Register handlers
    plugin.register_handler("pre-install-success", handle_pre_install_success)
    plugin.register_handler("post-install", handle_post_install)
    plugin.register_handler("pre-remove", handle_pre_remove)
    plugin.register_handler("post-remove", handle_post_remove)
    plugin.register_handler("pre-upgrade", handle_pre_upgrade)
    plugin.register_handler("post-upgrade", handle_post_upgrade)
    plugin.register_handler("pre-health", handle_pre_health)
    plugin.register_handler("post-health-success", handle_post_health_success)
    plugin.register_handler("post-health-failure", handle_post_health_failure)
    plugin.register_handler("health-fix", handle_health_fix)


def configure_snapper_plugin(plugin) -> bool:
    """Interactive configuration for Snapper plugin"""
    from src.core.ui import UIManager
    ui = UIManager()
    
    ui.info("\nSnapper Plugin Configuration")
    ui.info("=" * 35)
    ui.info("Configure which events should create snapshots:")
    ui.info("")
    
    # Check if snapper is available
    if not _is_snapper_available():
        ui.warning("Snapper is not installed or not available on this system.")
        ui.info("Install Snapper first:")
        ui.info("  Fedora/RHEL: sudo dnf install snapper")
        ui.info("  Ubuntu/Debian: sudo apt install snapper")
        ui.info("  Arch: sudo pacman -S snapper")
        ui.info("")
        
        if not ui.confirm("Continue with configuration anyway?"):
            return False
    
    # Load current config
    config = _load_snapper_config(plugin)
    
    # Define event descriptions
    events = {
        'pre_install': 'Before installing packages (only when packages are found)',
        'post_install': 'After installing packages (with success/failure status)',
        'pre_remove': 'Before removing packages',
        'post_remove': 'After removing packages (with success/failure status)',
        'pre_upgrade': 'Before upgrading system packages',
        'post_upgrade': 'After upgrading system packages (with success/failure status)',
        'pre_health': 'Before applying health fixes',
        'post_health_success': 'After successful health checks',
        'post_health_failure': 'After failed health checks (rollback point)',
        'health_fix': 'Before applying health fixes'
    }
    
    # Configure each event
    for event_key, description in events.items():
        current_value = config.get(event_key, True)
        enabled = ui.prompt_yes_no(f"Create snapshots {description}?", current_value)
        config[event_key] = enabled
    
    # Save configuration
    _save_snapper_config(plugin, config)
    
    ui.success("Snapper plugin configuration saved!")
    ui.info("")
    
    # Show summary
    enabled_events = [desc for key, desc in events.items() if config.get(key, True)]
    if enabled_events:
        ui.info("Enabled events:")
        for event in enabled_events:
            ui.info(f"  ✓ {event}")
    else:
        ui.warning("No events enabled - plugin will not create any snapshots")
    
    return True


def _load_snapper_config(plugin) -> Dict[str, Any]:
    """Load Snapper plugin configuration"""
    config_file = Path.home() / '.config/paka/snapper_config.json'
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            plugin.logger.error(f"Error loading snapper config: {e}")
    
    # Default configuration
    return {
        'pre_install': True,
        'post_install': True,
        'pre_remove': True,
        'post_remove': True,
        'pre_upgrade': True,
        'post_upgrade': True,
        'pre_health': True,
        'post_health_success': False,
        'post_health_failure': True,
        'health_fix': True
    }


def _save_snapper_config(plugin, config: Dict[str, Any]):
    """Save Snapper plugin configuration"""
    config_file = Path.home() / '.config/paka/snapper_config.json'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        plugin.logger.error(f"Error saving snapper config: {e}")


def _is_snapper_available() -> bool:
    """Check if snapper is available on the system"""
    return shutil.which('snapper') is not None 