#!/usr/bin/env python3
"""
UI Management Module

Handles colorful output, user interactions, and display formatting.
"""

import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime


class UIManager:
    """Manages user interface and output formatting"""
    
    def __init__(self):
        """Initialize UI manager"""
        self.colors_enabled = self._check_colors_enabled()
        self.icons_enabled = True  # Could be made configurable
        self.terminal_width = self._get_terminal_width()
    
    def _check_colors_enabled(self) -> bool:
        """Check if colors should be enabled"""
        # Check if NO_COLOR environment variable is set
        if os.environ.get('NO_COLOR'):
            return False
        
        # Check if FORCE_COLOR is set
        if os.environ.get('FORCE_COLOR'):
            return True
        
        # Check if we're in a terminal
        return sys.stdout.isatty()
    
    def _get_terminal_width(self) -> int:
        """Get terminal width"""
        try:
            import shutil
            return shutil.get_terminal_size().columns
        except:
            return 80
    
    def _colorize(self, text: str, color_code: str, bold: bool = False) -> str:
        """Add color to text if colors are enabled"""
        if not self.colors_enabled:
            return text
        
        colors = {
            'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m',
            'blue': '\033[94m', 'magenta': '\033[95m', 'cyan': '\033[96m',
            'white': '\033[97m', 'grey': '\033[90m',
            'bright_red': '\033[1;91m', 'bright_green': '\033[1;92m',
            'bright_yellow': '\033[1;93m', 'bright_blue': '\033[1;94m',
            'bright_magenta': '\033[1;95m', 'bright_cyan': '\033[1;96m',
            'bold': '\033[1m', 'underline': '\033[4m', 'reset': '\033[0m'
        }
        
        style = ''
        if bold:
            style += colors['bold']
        style += colors.get(color_code, '')
        return f"{style}{text}{colors['reset']}"

    def _icon(self, name: str) -> str:
        if not self.icons_enabled:
            return ''
        icons = {
            'info': 'ℹ️', 'success': '✔️', 'warning': '⚠️', 'error': '✗',
            'prompt': '➤', 'star': '★', 'official': '★', 'stable': '✔️',
            'beta': '⚠️', 'alpha': '🔺', 'recommended': '★', 'test': '🧪',
            'menu': '➜', 'section': '🛠️', 'settings': '⚙️', 'back': '⬅️',
            'exit': '⏻', 'enabled': '🟢', 'disabled': '🔴', 'search': '🔍',
            'pkg': '📦', 'history': '🕑', 'plugin': '🔌', 'shell': '🐚',
            'star_hollow': '☆', 'arrow': '➔', 'dot': '•', 'check': '✔️',
            'cross': '✗', 'triangle': '▲', 'circle': '●', 'question': '❓',
        }
        return icons.get(name, '')

    def info(self, message: str, icon: bool = True):
        """Display info message"""
        prefix = self._icon('info') + ' ' if icon else ''
        print(f"{self._colorize(prefix + message, 'cyan', bold=True)}")
    
    def success(self, message: str):
        """Display success message"""
        print(f"{self._icon('success')} {self._colorize(message, 'green', bold=True)}")
    
    def warning(self, message: str):
        """Display warning message"""
        print(f"{self._icon('warning')} {self._colorize(message, 'yellow', bold=True)}")
    
    def error(self, message: str):
        """Display error message"""
        print(f"{self._icon('error')} {self._colorize(message, 'red', bold=True)}")
    
    def debug(self, message: str):
        """Display debug message"""
        print(f"🐛 {self._colorize(message, 'cyan')}")
    
    def progress(self, message: str):
        """Display progress message"""
        print(f"⏳ {message}")
    
    def confirm(self, message: str) -> bool:
        """Ask for user confirmation"""
        response = input(f"{message} (y/N): ").strip().lower()
        return response in ['y', 'yes']
    
    def prompt(self, message: str) -> str:
        """Prompt user for input"""
        prompt_str = f"{self._colorize(self._icon('prompt') + ' ' + message, 'yellow', bold=True)}: "
        return input(prompt_str).strip()
    
    def prompt_yes_no(self, message: str, default: bool = False) -> bool:
        """Prompt user for yes/no input with default value"""
        default_text = "Y/n" if default else "y/N"
        prompt_str = f"{self._colorize(self._icon('prompt') + ' ' + message, 'yellow', bold=True)} ({default_text}): "
        response = input(prompt_str).strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes']
    
    def select_from_list(self, items: List[str], prompt: str = "Select an option:") -> Optional[int]:
        """Display a numbered list and get user selection"""
        if not items:
            return None
        
        print(prompt)
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")
        
        try:
            choice = int(input("Enter number: ").strip())
            if 1 <= choice <= len(items):
                return choice - 1
            else:
                self.error("Invalid selection")
                return None
        except ValueError:
            self.error("Invalid input")
            return None
    
    def display_table(self, headers: List[str], rows: List[List[str]], 
                     title: Optional[str] = None):
        """Display data in a formatted table"""
        if not rows:
            self.info("No data to display")
            return
        
        if title:
            print(f"\n{self._colorize(title, 'bold')}")
        
        # Calculate column widths
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width)
        
        # Print header
        header_row = " | ".join(header.ljust(width) for header, width in zip(headers, col_widths))
        print(self._colorize(header_row, 'bold'))
        print("-" * len(header_row))
        
        # Print rows
        for row in rows:
            formatted_row = []
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    formatted_row.append(str(cell).ljust(col_widths[i]))
                else:
                    formatted_row.append(str(cell))
            print(" | ".join(formatted_row))
    
    def display_search_results(self, packages: List[Dict[str, Any]]):
        """Display package search results"""
        if not packages:
            self.info("No packages found")
            return
        
        # Prepare table data
        headers = [self._colorize('Manager', 'cyan', True), self._colorize('Package', 'magenta', True), self._colorize('Version', 'yellow', True), self._colorize('Description', 'blue', True)]
        rows = []
        
        for package in packages:
            # Status icons
            status = package.get('status', '').lower()
            if status == 'official':
                icon = self._icon('star')
                color = 'yellow'
            elif status == 'stable':
                icon = self._icon('stable')
                color = 'green'
            elif status == 'beta':
                icon = self._icon('beta')
                color = 'yellow'
            elif status == 'alpha':
                icon = self._icon('alpha')
                color = 'red'
            else:
                icon = self._icon('dot')
                color = 'white'
            name = f"{self._colorize(icon, color, True)} {package.get('name', 'Unknown')}"
            rows.append([
                package.get('manager', 'Unknown'),
                name,
                package.get('version', 'Unknown'),
                package.get('description', 'No description')[:50] + '...' if len(package.get('description', '')) > 50 else package.get('description', 'No description')
            ])
        
        self.display_table(headers, rows, self._colorize(self._icon('search') + ' Search Results', 'cyan', True))
    
    def display_progress_bar(self, current: int, total: int, description: str = ""):
        """Display a progress bar"""
        if total == 0:
            return
        
        percentage = (current / total) * 100
        bar_width = 30
        filled_width = int((current / total) * bar_width)
        
        bar = "█" * filled_width + "░" * (bar_width - filled_width)
        
        if description:
            print(f"\r{description}: [{bar}] {percentage:.1f}% ({current}/{total})", end="")
        else:
            print(f"\r[{bar}] {percentage:.1f}% ({current}/{total})", end="")
        
        if current == total:
            print()  # New line when complete
    
    def display_package_info(self, package: Dict[str, Any]):
        """Display detailed package information"""
        print(f"\n{self._colorize('Package Information', 'bold')}")
        print(f"  Name: {package.get('name', 'Unknown')}")
        print(f"  Manager: {package.get('manager', 'Unknown')}")
        print(f"  Version: {package.get('version', 'Unknown')}")
        print(f"  Size: {package.get('size', 'Unknown')}")
        
        if package.get('description'):
            print(f"  Description: {package['description']}")
        
        if package.get('dependencies'):
            print(f"  Dependencies ({len(package['dependencies'])}):")
            for dep in package['dependencies'][:5]:  # Show first 5
                print(f"    - {dep}")
            if len(package['dependencies']) > 5:
                print(f"    ... and {len(package['dependencies']) - 5} more")
    
    def display_help(self, command: Optional[str] = None):
        """Display help information"""
        if command:
            self._display_command_help(command)
        else:
            self._display_general_help()
    
    def _display_general_help(self):
        """Display general help"""
        help_text = """
PAKA - Universal Package Manager Wrapper

Usage: paka <command> [options] [packages...]

Commands:
  install    Install packages
  remove     Remove packages
  purge      Remove packages and configuration files
  update     Refresh package lists
  upgrade    Upgrade installed packages
  search     Search for packages
  health     Check system health
  history    Manage installation history
  config     Manage configuration

Options:
  -y, --yes          Skip confirmation prompts
  --dry-run          Show what would be done without making changes
  --manager <name>   Use specific package manager
  --help             Show this help message

Examples:
  paka install firefox
paka search python
paka health --fix-all
paka history list
paka config show

For more information about a command, use: paka <command> --help
"""
        print(help_text)
    
    def _display_command_help(self, command: str):
        """Display help for a specific command"""
        help_texts = {
            'install': """
Install packages using available package managers.

Usage: paka install [options] <packages...>

Options:
  -y, --yes          Skip confirmation prompts
  --dry-run          Show what would be installed
  --manager <name>   Use specific package manager
  --profile <name>   Use installation profile

Examples:
  paka install firefox
paka install --manager dnf python3
paka install --dry-run vim
""",
            'search': """
Search for packages across all package managers.

Usage: paka search [options] <query>

Options:
  --manager <name>   Search in specific package manager
  --exact            Exact match only
  --installed        Show only installed packages

Examples:
          paka search firefox
        paka search --manager apt python
        paka search --exact vim
""",
            'health': """
Check system and package manager health.

Usage: paka health [options]

Options:
  --fix-all          Automatically fix all issues
  --interactive      Interactive fix mode
  --manager <name>   Check specific package manager

Examples:
  paka health
paka health --fix-all
paka health --interactive
""",
            'history': """
Manage installation history.

Usage: paka history [command] [options]

Commands:
  list               Show installation history
  show <id>          Show details of specific installation
  search <query>     Search installation history
  stats              Show history statistics
  clear              Clear all history

Examples:
  paka history
paka history show 5
paka history search firefox
paka history stats
"""
        }
        
        if command in help_texts:
            print(help_texts[command])
        else:
            self.error(f"No help available for command: {command}")
    
    def display_banner(self):
        """Display PAKA banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    PAKA Package Manager                      ║
║              Universal Package Manager Wrapper               ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(self._colorize(banner, 'cyan'))
    
    def display_version(self):
        """Display version information"""
        version = "0.1.0"  # This should come from a version file
        print(f"PAKA version {version}")
        print("Universal Package Manager Wrapper")
        print("https://github.com/yourusername/paka")
    
    def display_error_summary(self, errors: List[str]):
        """Display a summary of errors"""
        if not errors:
            return
        
        print(f"\n{self._colorize('Error Summary:', 'red')}")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
    
    def display_success_summary(self, successes: List[str]):
        """Display a summary of successful operations"""
        if not successes:
            return
        
        print(f"\n{self._colorize('Success Summary:', 'green')}")
        for i, success in enumerate(successes, 1):
            print(f"  {i}. {success}")
    
    def display_timing(self, start_time: datetime, end_time: datetime):
        """Display timing information"""
        duration = end_time - start_time
        print(f"\n⏱️  Operation completed in {duration.total_seconds():.2f} seconds") 

    def display_menu_header(self, title: str, icon: str = 'section'):
        bar = '+' + '-' * (len(title) + 4) + '+'
        print(self._colorize(bar, 'cyan', bold=True))
        print(self._colorize(f"|  {self._icon(icon)} {title}  |", 'cyan', bold=True))
        print(self._colorize(bar, 'cyan', bold=True))

    def display_menu_options(self, options: List[str]):
        for i, opt in enumerate(options, 1):
            print(f"  {self._colorize(str(i), 'magenta', bold=True)}. {opt}")

    def display_status(self, label: str, value: str, status: str = 'info'):
        color = {'enabled': 'green', 'disabled': 'red', 'info': 'cyan', 'warning': 'yellow', 'error': 'red'}.get(status, 'white')
        icon = self._icon(status)
        print(f"{icon} {self._colorize(label + ':', color, bold=True)} {value}") 

    def display_note(self, message: str):
        """Display a plain note or section/list item (no icon, no bold)"""
        print(self._colorize(message, 'cyan')) 