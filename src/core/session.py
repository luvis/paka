#!/usr/bin/env python3
"""
Session Management Module

Handles user session data, preferences, and command history tracking.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from .config import ConfigManager


class SessionManager:
    """Manages user session data and preferences"""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize session manager"""
        self.config_manager = config_manager
        self.session_file = self.config_manager.get_session_file()
        self.session_data = self._load_session()
        self.logger = logging.getLogger(__name__)
    
    def _load_session(self) -> Dict[str, Any]:
        """Load session data from file"""
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    # Convert usage_stats fields back to defaultdict(int)
                    if 'usage_stats' in data:
                        us = data['usage_stats']
                        us['commands_by_type'] = defaultdict(int, us.get('commands_by_type', {}))
                        us['managers_used'] = defaultdict(int, us.get('managers_used', {}))
                        data['usage_stats'] = us
                    return data
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load session data: {e}")
        
        # Return default session structure
        return {
            'created': datetime.now().isoformat(),
            'last_used': datetime.now().isoformat(),
            'command_history': [],
            'preferences': {
                'default_manager': None,
                'auto_confirm': False,
                'show_progress': True,
                'color_output': True,
                'max_history': 1000
            },
            'usage_stats': {
                'total_commands': 0,
                'commands_by_type': defaultdict(int),
                'managers_used': defaultdict(int),
                'last_install': None,
                'last_upgrade': None
            }
        }
    
    def _save_session(self):
        """Save session data to file"""
        def convert_defaultdict(obj):
            if isinstance(obj, defaultdict):
                return dict(obj)
            if isinstance(obj, dict):
                return {k: convert_defaultdict(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_defaultdict(i) for i in obj]
            return obj
        try:
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            serializable_data = convert_defaultdict(self.session_data)
            with open(self.session_file, 'w') as f:
                json.dump(serializable_data, f, indent=2)
        except IOError as e:
            self.logger.error(f"Failed to save session data: {e}")
    
    def record_command(self, command: str, args: List[str], options: Dict[str, Any]):
        """Record a command execution in session history"""
        try:
            # Update last used timestamp
            self.session_data['last_used'] = datetime.now().isoformat()
            
            # Record command in history
            command_record = {
                'timestamp': datetime.now().isoformat(),
                'command': command,
                'args': args,
                'options': options
            }
            
            self.session_data['command_history'].append(command_record)
            
            # Limit history size
            max_history = self.session_data['preferences']['max_history']
            if len(self.session_data['command_history']) > max_history:
                self.session_data['command_history'] = self.session_data['command_history'][-max_history:]
            
            # Update usage statistics
            self.session_data['usage_stats']['total_commands'] += 1
            self.session_data['usage_stats']['commands_by_type'][command] += 1
            
            # Track manager usage
            if 'manager' in options and options['manager']:
                self.session_data['usage_stats']['managers_used'][options['manager']] += 1
            
            # Track last operations
            if command == 'install':
                self.session_data['usage_stats']['last_install'] = datetime.now().isoformat()
            elif command == 'upgrade':
                self.session_data['usage_stats']['last_upgrade'] = datetime.now().isoformat()
            
            # Save session
            self._save_session()
        except Exception as e:
            self.logger.error(f"Error recording command: {e}")
            raise
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        return self.session_data['preferences'].get(key, default)
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference"""
        self.session_data['preferences'][key] = value
        self._save_session()
    
    def get_command_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get command history"""
        history = self.session_data['command_history']
        if limit:
            return history[-limit:]
        return history
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return self.session_data['usage_stats'].copy()
    
    def get_most_used_manager(self) -> Optional[str]:
        """Get the most frequently used package manager"""
        managers = self.session_data['usage_stats']['managers_used']
        if not managers:
            return None
        
        return max(managers.items(), key=lambda x: x[1])[0]
    
    def get_most_used_commands(self, limit: int = 5) -> List[tuple]:
        """Get the most frequently used commands"""
        commands = self.session_data['usage_stats']['commands_by_type']
        if not commands:
            return []
        
        sorted_commands = sorted(commands.items(), key=lambda x: x[1], reverse=True)
        return sorted_commands[:limit]
    
    def clear_history(self):
        """Clear command history"""
        self.session_data['command_history'] = []
        self._save_session()
    
    def get_session_age(self) -> timedelta:
        """Get the age of the current session"""
        created = datetime.fromisoformat(self.session_data['created'])
        return datetime.now() - created
    
    def get_last_activity(self) -> Optional[datetime]:
        """Get the timestamp of last activity"""
        if self.session_data['last_used']:
            return datetime.fromisoformat(self.session_data['last_used'])
        return None 