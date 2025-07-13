#!/usr/bin/env python3
"""
Base Health Manager Module

Defines the base health manager and common functionality for health checks.
"""

import logging
from typing import Dict, List, Any, Optional, NamedTuple
from pathlib import Path

from ..config import ConfigManager
from ..plugin_manager import PluginEvent


class HealthCheck(NamedTuple):
    """Represents a health check result"""
    name: str
    status: str  # 'ok', 'warning', 'error'
    message: str
    fix_command: Optional[str] = None
    fix_description: Optional[str] = None


class HealthManager:
    """Manages health checks and fixes for package managers"""
    
    def __init__(self, config_manager: ConfigManager, engine=None):
        """Initialize health manager"""
        self.config_manager = config_manager
        self.engine = engine
        self.logger = logging.getLogger(__name__)
    
    def run_health_checks(self, options: Dict[str, Any]) -> int:
        """Run package manager health checks"""
        from .checkers import HealthCheckers
        from .ui import HealthUI
        
        checkers = HealthCheckers(self.config_manager)
        ui = HealthUI()
        
        ui.display_header("Running PAKA Package Manager Health Checks...")
        
        all_checks = []
        
        # 1. Package manager health checks
        ui.display_section("Checking package managers...")
        all_checks.extend(checkers.check_package_managers())
        
        # 2. Package manager cache health
        ui.display_section("Checking package caches...")
        all_checks.extend(checkers.check_package_caches())
        
        # 3. Disk bloat and package cleanup
        ui.display_section("Checking disk bloat and package cleanup...")
        all_checks.extend(checkers.check_disk_bloat())
        
        # 4. Partial installations and locks
        ui.display_section("Checking partial installations and locks...")
        all_checks.extend(checkers.check_partial_installations())
        
        # 5. Purge history and orphaned packages
        ui.display_section("Checking purge history and orphaned packages...")
        all_checks.extend(checkers.check_purge_history())
        
        # 6. Package manager database health
        ui.display_section("Checking package databases...")
        all_checks.extend(checkers.check_package_databases())
        
        # 7. Third-party repository health
        ui.display_section("Checking third-party repositories...")
        all_checks.extend(checkers.check_third_party_repos())
        
        ui.display_section("")  # Empty line
        
        # Handle fixes
        if options.get('fix_all'):
            # Trigger pre-health event before applying fixes
            if self.engine:
                health_context = {
                    'checks': all_checks,
                    'fix_count': len([c for c in all_checks if c.fix_command]),
                    'options': options
                }
                self.engine._trigger_plugin_event(PluginEvent.PRE_HEALTH, health_context)
            return ui.fix_all_issues(all_checks, self.engine)
        else:
            # For interactive mode, we need to trigger pre-health before any fixes
            # We'll do this in the UI methods that handle fixes
            return ui.interactive_health_overview(all_checks, self.engine)
    
    def create_check(self, name: str, status: str, message: str, fix_command: Optional[str] = None, fix_description: Optional[str] = None) -> HealthCheck:
        """Create a health check result"""
        return HealthCheck(
            name=name,
            status=status,
            message=message,
            fix_command=fix_command,
            fix_description=fix_description
        ) 