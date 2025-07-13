#!/usr/bin/env python3
"""
Shell Integration Module

Handles command-not-found suggestions and shell integration features.
This is a feature/function rather than a plugin since it operates outside of PAKA actions.
"""

import os
import sys
import json
import logging
import subprocess
import shutil
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

from .config import ConfigManager
from .package_managers import PackageManagerRegistry
from .ui import UIManager


class ShellIntegration:
    """Manages shell integration features like command-not-found suggestions"""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize shell integration"""
        self.config_manager = config_manager
        self.package_manager_registry = PackageManagerRegistry(config_manager)
        self.ui_manager = UIManager()
        self.logger = logging.getLogger('paka.shell_integration')
        
        # Load configuration
        self.config = self._load_config()
        
        # Get available package managers
        self.package_managers = self.package_manager_registry.get_available_managers()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load shell integration configuration"""
        config = self.config_manager.load_config()
        return config.get('shell_integration', {
            'enabled': False,
            'command_not_found': True,
            'suggestions': True,
            'auto_install': False,
            'shells': ['bash', 'zsh'],
            'suggestion_limit': 5
        })
    
    def is_enabled(self) -> bool:
        """Check if shell integration is enabled"""
        return self.config.get('enabled', False)
    
    def enable(self):
        """Enable shell integration"""
        self.config['enabled'] = True
        self._save_config()
        self._install_shell_hooks()
        self.ui_manager.success("Shell integration enabled")
    
    def disable(self):
        """Disable shell integration"""
        self.config['enabled'] = False
        self._save_config()
        self._remove_shell_hooks()
        self.ui_manager.success("Shell integration disabled")
    
    def _save_config(self):
        """Save shell integration configuration"""
        try:
            config = self.config_manager.load_config()
            config['shell_integration'] = self.config
            self.config_manager._save_config(config)
        except Exception as e:
            self.logger.error(f"Error saving shell integration config: {e}")
    
    def handle_command_not_found(self, command: str) -> Optional[str]:
        """Handle command-not-found event and return suggestion"""
        if not self.is_enabled() or not self.config.get('command_not_found', True):
            return None
        
        # Search for the command across all package managers
        suggestions = self._search_command_packages(command)
        
        if not suggestions:
            return None
        
        # Format the suggestion
        return self._format_suggestion(command, suggestions)
    
    def _search_command_packages(self, command: str) -> List[Dict[str, Any]]:
        """Search for packages that provide the given command"""
        suggestions = []
        
        for manager_name, manager in self.package_managers.items():
            if not manager.is_enabled():
                continue
            
            try:
                # Search for packages that might provide this command
                result = manager.search(command, {})
                if result.success and result.packages:
                    # Filter packages that likely provide the command
                    for package in result.packages[:3]:  # Limit to 3 per manager
                        if self._package_likely_provides_command(package, command):
                            suggestions.append({
                                'manager': manager_name,
                                'package': package,
                                'confidence': self._calculate_confidence(package, command)
                            })
            except Exception as e:
                self.logger.debug(f"Error searching {manager_name} for {command}: {e}")
        
        # Sort by confidence and limit results
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return suggestions[:self.config.get('suggestion_limit', 5)]
    
    def _package_likely_provides_command(self, package: Dict[str, Any], command: str) -> bool:
        """Check if a package is likely to provide the given command"""
        package_name = package.get('name', '').lower()
        description = package.get('description', '').lower()
        
        # High confidence: package name matches command
        if package_name == command.lower():
            return True
        
        # Medium confidence: package name contains command
        if command.lower() in package_name:
            return True
        
        # Low confidence: description mentions command
        if command.lower() in description:
            return True
        
        return False
    
    def _calculate_confidence(self, package: Dict[str, Any], command: str) -> float:
        """Calculate confidence score for a package suggestion"""
        package_name = package.get('name', '').lower()
        description = package.get('description', '').lower()
        command_lower = command.lower()
        
        # Exact name match
        if package_name == command_lower:
            return 1.0
        
        # Name contains command
        if command_lower in package_name:
            return 0.8
        
        # Description contains command
        if command_lower in description:
            return 0.6
        
        return 0.3
    
    def _format_suggestion(self, command: str, suggestions: List[Dict[str, Any]]) -> Optional[str]:
        """Format command-not-found suggestion"""
        if not suggestions:
            return None
        
        lines = [
            f"Command '{command}' not found. You can install it with:",
            ""
        ]
        
        for i, suggestion in enumerate(suggestions, 1):
            manager = suggestion['manager']
            package = suggestion['package']
            package_name = package.get('name', '')
            description = package.get('description', '')
            
            lines.append(f"{i}. paka install {package_name}  # {manager}")
            if description:
                lines.append(f"   {description}")
            lines.append("")
        
        lines.append("Or search for alternatives:")
        lines.append(f"paka search {command}")
        
        return "\n".join(lines)
    
    def _install_shell_hooks(self):
        """Install shell hooks for command-not-found"""
        try:
            # Create the hook script
            hook_script = self._create_hook_script()
            
            # Install for each configured shell
            for shell in self.config.get('shells', ['bash', 'zsh']):
                self._install_shell_hook(shell, hook_script)
        
        except Exception as e:
            self.logger.error(f"Error installing shell hooks: {e}")
    
    def _create_hook_script(self) -> str:
        """Create the command-not-found hook script"""
        return '''#!/bin/bash
# PAKA Command Not Found Hook

# Only run if PAKA is available
if ! command -v paka &> /dev/null; then
    return 1
fi

# Get the command that wasn't found
COMMAND="$1"

# Skip if command is empty or is a builtin
if [[ -z "$COMMAND" ]] || type "$COMMAND" &> /dev/null; then
    return 1
fi

# Get suggestion from PAKA
SUGGESTION=$(paka shell-not-found "$COMMAND" 2>/dev/null)

if [[ -n "$SUGGESTION" ]]; then
    echo "$SUGGESTION"
    return 0
fi

return 1
'''
    
    def _install_shell_hook(self, shell: str, hook_script: str):
        """Install hook for a specific shell"""
        try:
            if shell == 'bash':
                self._install_bash_hook(hook_script)
            elif shell == 'zsh':
                self._install_zsh_hook(hook_script)
            elif shell == 'fish':
                self._install_fish_hook(hook_script)
        except Exception as e:
            self.logger.error(f"Error installing {shell} hook: {e}")
    
    def _install_bash_hook(self, hook_script: str):
        """Install bash command-not-found hook"""
        # Create hook directory
        hook_dir = Path.home() / '.local/share/paka/hooks'
        hook_dir.mkdir(parents=True, exist_ok=True)
        
        # Write hook script
        hook_file = hook_dir / 'command-not-found'
        with open(hook_file, 'w') as f:
            f.write(hook_script)
        os.chmod(hook_file, 0o755)
        
        # Add to bashrc if not already present
        bashrc = Path.home() / '.bashrc'
        if bashrc.exists():
            with open(bashrc, 'r') as f:
                content = f.read()
            
            hook_line = f'source "{hook_file}"'
            if hook_line not in content:
                with open(bashrc, 'a') as f:
                    f.write(f'\n# PAKA command-not-found hook\n{hook_line}\n')
    
    def _install_zsh_hook(self, hook_script: str):
        """Install zsh command-not-found hook"""
        # Create hook directory
        hook_dir = Path.home() / '.local/share/paka/hooks'
        hook_dir.mkdir(parents=True, exist_ok=True)
        
        # Write hook script
        hook_file = hook_dir / 'command-not-found'
        with open(hook_file, 'w') as f:
            f.write(hook_script)
        os.chmod(hook_file, 0o755)
        
        # Add to zshrc if not already present
        zshrc = Path.home() / '.zshrc'
        if zshrc.exists():
            with open(zshrc, 'r') as f:
                content = f.read()
            
            hook_line = f'source "{hook_file}"'
            if hook_line not in content:
                with open(zshrc, 'a') as f:
                    f.write(f'\n# PAKA command-not-found hook\n{hook_line}\n')
    
    def _install_fish_hook(self, hook_script: str):
        """Install fish command-not-found hook"""
        # Fish uses a different approach - we need to create a fish function
        fish_config_dir = Path.home() / '.config/fish/functions'
        fish_config_dir.mkdir(parents=True, exist_ok=True)
        
        fish_function = f'''function fish_command_not_found
    # Only run if PAKA is available
    if not command -q paka
        return 1
    end
    
    # Get suggestion from PAKA
    set suggestion (paka shell-not-found $argv[1] 2>/dev/null)
    
    if test -n "$suggestion"
        echo $suggestion
        return 0
    end
    
    return 1
end
'''
        
        function_file = fish_config_dir / 'fish_command_not_found.fish'
        with open(function_file, 'w') as f:
            f.write(fish_function)
    
    def _remove_shell_hooks(self):
        """Remove shell hooks"""
        try:
            # Remove hook files
            hook_dir = Path.home() / '.local/share/paka/hooks'
            if hook_dir.exists():
                import shutil
                shutil.rmtree(hook_dir)
            
            # Remove from shell configs
            self._remove_from_shell_config('.bashrc')
            self._remove_from_shell_config('.zshrc')
            
            # Remove fish function
            fish_function = Path.home() / '.config/fish/functions/fish_command_not_found.fish'
            if fish_function.exists():
                fish_function.unlink()
        
        except Exception as e:
            self.logger.error(f"Error removing shell hooks: {e}")
    
    def _remove_from_shell_config(self, config_file: str):
        """Remove PAKA hooks from shell config file"""
        config_path = Path.home() / config_file
        if not config_path.exists():
            return
        
        try:
            with open(config_path, 'r') as f:
                lines = f.readlines()
            
            # Remove PAKA-related lines
            filtered_lines = []
            skip_next = False
            
            for line in lines:
                if '# PAKA command-not-found hook' in line:
                    skip_next = True
                    continue
                elif skip_next and line.strip().startswith('source'):
                    skip_next = False
                    continue
                elif skip_next:
                    skip_next = False
                
                filtered_lines.append(line)
            
            # Write back the filtered content
            with open(config_path, 'w') as f:
                f.writelines(filtered_lines)
        
        except Exception as e:
            self.logger.error(f"Error removing from {config_file}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get shell integration status"""
        return {
            'enabled': self.is_enabled(),
            'command_not_found': self.config.get('command_not_found', True),
            'suggestions': self.config.get('suggestions', True),
            'auto_install': self.config.get('auto_install', False),
            'shells': self.config.get('shells', ['bash', 'zsh']),
            'suggestion_limit': self.config.get('suggestion_limit', 5)
        }
    
    def update_config(self, key: str, value: Any):
        """Update shell integration configuration"""
        self.config[key] = value
        self._save_config()
    
    def test_integration(self) -> bool:
        """Test if shell integration is working"""
        try:
            # Test if hooks are installed
            hook_dir = Path.home() / '.local/share/paka/hooks'
            hook_file = hook_dir / 'command-not-found'
            
            if not hook_file.exists():
                return False
            
            # Test if hook is executable
            if not os.access(hook_file, os.X_OK):
                return False
            
            # Test if hook is sourced in shell configs
            bashrc = Path.home() / '.bashrc'
            zshrc = Path.home() / '.zshrc'
            
            bash_hooked = False
            zsh_hooked = False
            
            if bashrc.exists():
                with open(bashrc, 'r') as f:
                    bash_hooked = 'PAKA command-not-found hook' in f.read()
            
            if zshrc.exists():
                with open(zshrc, 'r') as f:
                    zsh_hooked = 'PAKA command-not-found hook' in f.read()
            
            return bash_hooked or zsh_hooked
        
        except Exception as e:
            self.logger.error(f"Error testing shell integration: {e}")
            return False 