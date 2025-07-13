#!/usr/bin/env python3
"""
Privilege Management Module

Handles internal privilege escalation, context-aware messaging, and privilege status tracking.
"""

import os
import subprocess
import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path


class PrivilegeManager:
    """Manages privilege escalation and status for PAKA operations"""
    
    def __init__(self):
        """Initialize privilege manager"""
        self.logger = logging.getLogger(__name__)
        self._privilege_status = {
            'has_root': os.geteuid() == 0,
            'escalated_this_session': False,
            'last_escalation_time': None
        }
    
    def is_root(self) -> bool:
        """Check if currently running as root"""
        return self._privilege_status['has_root']
    
    def needs_privilege_escalation(self, operation: str) -> bool:
        """Check if an operation needs privilege escalation"""
        privileged_operations = {
            'install': True,
            'remove': True,
            'purge': True,
            'update': True,
            'upgrade': True,
            'system_plugin_create': True,
            'system_config_modify': True,
            'system_history_access': True,
            'flatpak_system_install': True,
            'search': False,
            'history_user': False,
            'user_plugin_create': False,
            'user_config_modify': False
        }
        return privileged_operations.get(operation, False)
    
    def escalate_if_needed(self, operation: str, ui_manager) -> bool:
        """Escalate privileges if needed for the operation"""
        if self.is_root():
            ui_manager.display_note("Root privileges already acquired. Running operation...")
            return True
        
        if not self.needs_privilege_escalation(operation):
            return True
        
        return self._escalate_privileges(ui_manager)
    
    def _escalate_privileges(self, ui_manager) -> bool:
        """Attempt to escalate privileges using sudo"""
        try:
            # Test if sudo is available and user has sudo access
            result = subprocess.run(
                ['sudo', '-n', 'true'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # User has sudo access without password prompt
                ui_manager.display_note("Privilege escalation successful (password cached)")
                self._privilege_status['escalated_this_session'] = True
                return True
            else:
                # Need to prompt for password - let sudo handle it naturally
                result = subprocess.run(
                    ['sudo', 'true'],
                    input='\n',
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    ui_manager.success("Privilege escalation successful")
                    self._privilege_status['escalated_this_session'] = True
                    return True
                else:
                    ui_manager.error("Privilege escalation failed")
                    return False
                    
        except subprocess.TimeoutExpired:
            ui_manager.error("Privilege escalation timed out")
            return False
        except Exception as e:
            ui_manager.error(f"Privilege escalation error: {e}")
            return False
    
    def run_privileged_command(self, command: list, ui_manager, 
                             operation_description: str = "privileged operation") -> Tuple[bool, str]:
        """Run a command with privilege escalation if needed"""
        if self.is_root():
            # Already root, run directly
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=60)
                return result.returncode == 0, result.stdout + result.stderr
            except Exception as e:
                return False, str(e)
        else:
            # Need to escalate
            if not self.escalate_if_needed("install", ui_manager):  # Use generic privileged operation
                return False, "Privilege escalation failed"
            
            try:
                result = subprocess.run(['sudo'] + command, capture_output=True, text=True, timeout=60)
                return result.returncode == 0, result.stdout + result.stderr
            except Exception as e:
                return False, str(e)
    
    def get_privilege_context_message(self, operation: str) -> str:
        """Get context-aware privilege message for an operation"""
        if self.is_root():
            return "Running as root - all operations available"
        
        if self.needs_privilege_escalation(operation):
            return f"Operation '{operation}' requires elevated privileges"
        else:
            return f"Operation '{operation}' can run with user privileges"
    
    def can_access_system_history(self) -> bool:
        """Check if current user can access system history"""
        return self.is_root() or self._privilege_status['escalated_this_session']
    
    def get_user_context(self) -> Dict[str, Any]:
        """Get current user context for operations"""
        return {
            'is_root': self.is_root(),
            'username': os.getenv('USER', 'unknown'),
            'home_dir': os.path.expanduser('~'),
            'can_escalate': self._privilege_status['escalated_this_session']
        }
    
    def can_escalate_privileges(self) -> bool:
        """Check if the current user can escalate privileges"""
        try:
            # Test if sudo is available and user has sudo access
            result = subprocess.run(
                ['sudo', '-n', 'true'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False 