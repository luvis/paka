# PAKA API Documentation

This document provides comprehensive API documentation for PAKA's plugin system, internal APIs, and development interfaces.

## Table of Contents

1. [Plugin System API](#plugin-system-api)
2. [Package Manager API](#package-manager-api)
3. [Health System API](#health-system-api)
4. [Configuration API](#configuration-api)
5. [History Management API](#history-management-api)
6. [Session Management API](#session-management-api)
7. [UI Manager API](#ui-manager-api)
8. [Event System](#event-system)
9. [Advanced Plugin Development](#advanced-plugin-development)

## Plugin System API

### Simple Plugins

Simple plugins use INI configuration files and support basic actions.

#### Plugin Configuration Format

```ini
# Plugin metadata
name=my-plugin
description=My plugin description
version=1.0.0
author=Your Name
enabled=true

# Event handlers
[post-install-success]
action=notify:Successfully installed $packages!
action=run:echo "Installed $packages" >> ~/paka.log

[error]
action=log:Error occurred: $error
```

#### Available Actions

- `run:command` - Execute a shell command
- `script:filename` - Run a script file in the plugin directory
- `notify:message` - Send a desktop notification
- `log:message` - Log a message to plugin log

#### Available Variables

- `$packages` - List of packages being processed
- `$package-count` - Number of packages
- `$package-manager` - Name of the package manager
- `$operation` - Current operation (install, remove, upgrade, etc.)
- `$success` - Whether the operation succeeded (true/false)
- `$error` - Error message if operation failed
- `$user` - Current username
- `$home` - User's home directory
- `$hostname` - System hostname
- `$timestamp` - Current timestamp (YYYY-MM-DD HH:MM:SS)
- `$date` - Current date (YYYY-MM-DD)
- `$time` - Current time (HH:MM:SS)

### Advanced Plugins

Advanced plugins are Python classes that inherit from base classes and provide full API access.

#### Base Classes

```python
from src.core.advanced_plugins.base import BasePlugin, BasePackageManager, BaseRepositoryManager
```

#### BasePlugin Class

```python
class BasePlugin(ABC):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"paka.plugin.{name}")
        self.enabled = config.get('enabled', False)
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup plugin resources"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'type': self.__class__.__name__,
            'description': self.config.get('description', ''),
            'version': self.config.get('version', '1.0.0')
        }
```

#### BasePackageManager Class

```python
class BasePackageManager(BasePlugin):
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.package_cache = {}
        self.installed_packages = set()
        self.repositories = config.get('repositories', {})
    
    @abstractmethod
    def search(self, query: str, options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for packages"""
        pass
    
    @abstractmethod
    def install(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> bool:
        """Install packages"""
        pass
    
    @abstractmethod
    def remove(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> bool:
        """Remove packages"""
        pass
    
    @abstractmethod
    def update(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Update package lists"""
        pass
    
    @abstractmethod
    def upgrade(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Upgrade installed packages"""
        pass
    
    @abstractmethod
    def list_installed(self, options: Optional[Dict[str, Any]] = None) -> List[str]:
        """List installed packages"""
        pass
    
    def get_package_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a package"""
        return None
    
    def check_updates(self) -> List[Dict[str, Any]]:
        """Check for available updates"""
        return []
    
    def add_repository(self, name: str, url: str, **kwargs) -> bool:
        """Add a new repository"""
        self.repositories[name] = {
            'url': url,
            'enabled': True,
            **kwargs
        }
        return True
    
    def remove_repository(self, name: str) -> bool:
        """Remove a repository"""
        if name in self.repositories:
            del self.repositories[name]
            return True
        return False
    
    def list_repositories(self) -> Dict[str, Dict[str, Any]]:
        """List all repositories"""
        return self.repositories.copy()
```

## Package Manager API

### BasePackageManager Interface

All package managers must implement the following interface:

```python
class BasePackageManager(ABC):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.command = config.get('command', name)
        self.enabled = config.get('enabled', True)
        self.logger = logging.getLogger(f"paka.{name}")
    
    def is_enabled(self) -> bool:
        """Check if package manager is enabled"""
        return self.enabled and shutil.which(self.command) is not None
    
    def is_available(self) -> bool:
        """Check if package manager is available on system"""
        return shutil.which(self.command) is not None
    
    @abstractmethod
    def install(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Install packages"""
        pass
    
    @abstractmethod
    def remove(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Remove packages"""
        pass
    
    @abstractmethod
    def purge(self, packages: List[str], options: Dict[str, Any]) -> PackageResult:
        """Purge packages and configuration"""
        pass
    
    @abstractmethod
    def update(self, options: Dict[str, Any]) -> PackageResult:
        """Update package lists"""
        pass
    
    @abstractmethod
    def upgrade(self, options: Dict[str, Any]) -> PackageResult:
        """Upgrade packages"""
        pass
    
    @abstractmethod
    def search(self, query: str, options: Dict[str, Any]) -> PackageResult:
        """Search for packages"""
        pass
    
    def _run_command(self, args: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result"""
        try:
            return subprocess.run(
                [self.command] + args,
                capture_output=capture_output,
                text=True,
                timeout=300  # 5 minute timeout
            )
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {self.command} {' '.join(args)}")
            raise
        except Exception as e:
            self.logger.error(f"Command failed: {self.command} {' '.join(args)} - {e}")
            raise
```

### PackageResult Class

```python
class PackageResult(NamedTuple):
    """Result of a package manager operation"""
    success: bool
    error: Optional[str] = None
    packages: Optional[List[Dict[str, Any]]] = None
    details: Optional[Dict[str, Any]] = None
```

## Health System API

### HealthCheck Class

```python
class HealthCheck(NamedTuple):
    """Represents a health check result"""
    name: str
    status: str  # 'ok', 'warning', 'error'
    message: str
    fix_command: Optional[str] = None
    fix_description: Optional[str] = None
```

### HealthManager Class

```python
class HealthManager:
    def __init__(self, config_manager: ConfigManager, engine=None):
        self.config_manager = config_manager
        self.engine = engine
        self.logger = logging.getLogger(__name__)
    
    def run_health_checks(self, options: Dict[str, Any]) -> int:
        """Run package manager health checks"""
        # Implementation details...
```

### HealthCheckers Class

```python
class HealthCheckers:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def check_package_managers(self) -> List[HealthCheck]:
        """Check package manager health"""
        # Implementation details...
    
    def check_package_caches(self) -> List[HealthCheck]:
        """Check package manager caches safely"""
        # Implementation details...
    
    def check_package_databases(self) -> List[HealthCheck]:
        """Check package manager database health safely"""
        # Implementation details...
```

## Configuration API

### ConfigManager Class

```python
class ConfigManager:
    def __init__(self, config_path: Optional[str] = None, scope: str = 'user'):
        self.directory_manager = DirectoryManager()
        self.privilege_manager = PrivilegeManager()
        self.scope = scope
        self.config_dir = self._get_effective_config_dir()
        self.config_file = self.directory_manager.get_config_file(self.scope)
        self.config = self._load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        # Implementation details...
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        # Implementation details...
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting"""
        return self.config.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a configuration setting"""
        self.config[key] = value
        self._save_config(self.config)
    
    def enable_package_manager(self, name: str):
        """Enable a package manager"""
        # Implementation details...
    
    def disable_package_manager(self, name: str):
        """Disable a package manager"""
        # Implementation details...
    
    def get_scope_info(self) -> Dict[str, Any]:
        """Get information about current scope"""
        # Implementation details...
```

## History Management API

### HistoryManager Class

```python
class HistoryManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.directory_manager = DirectoryManager()
        self.privilege_manager = PrivilegeManager()
        self.logger = logging.getLogger(__name__)
        self.user_history_data = self._load_history('user')
        self.system_history_data = self._load_history('system')
    
    def record_install(self, manager: str, packages: List[str], details: Dict[str, Any], scope: str = 'user'):
        """Record a package installation"""
        # Implementation details...
    
    def mark_packages_removed(self, manager: str, packages: List[str], scope: str = 'user'):
        """Mark packages as removed in history"""
        # Implementation details...
    
    def check_package_status(self, package_name: str, manager: str, scope: str = 'user') -> Dict[str, Any]:
        """Check if a package is still installed by querying the package manager"""
        # Implementation details...
    
    def reconcile_package_status(self, scope: str = 'user') -> Dict[str, Any]:
        """Reconcile history with actual package manager status"""
        # Implementation details...
    
    def get_installations(self, limit: Optional[int] = None, 
                         manager: Optional[str] = None, 
                         scope: str = 'user') -> List[Dict[str, Any]]:
        """Get installation history"""
        # Implementation details...
```

## Session Management API

### SessionManager Class

```python
class SessionManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.session_file = self.config_manager.get_session_file()
        self.session_data = self._load_session()
        self.logger = logging.getLogger(__name__)
    
    def record_command(self, command: str, args: List[str], options: Dict[str, Any]):
        """Record a command execution in session history"""
        # Implementation details...
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        return self.session_data['preferences'].get(key, default)
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference"""
        self.session_data['preferences'][key] = value
        self._save_session()
    
    def get_command_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get command history"""
        # Implementation details...
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return self.session_data['usage_stats'].copy()
```

## UI Manager API

### UIManager Class

```python
class UIManager:
    def __init__(self):
        self.colors_enabled = self._check_colors_enabled()
        self.terminal_width = self._get_terminal_width()
    
    def info(self, message: str, icon: bool = True):
        """Display an informational message"""
        # Implementation details...
    
    def success(self, message: str):
        """Display a success message"""
        # Implementation details...
    
    def warning(self, message: str):
        """Display a warning message"""
        # Implementation details...
    
    def error(self, message: str):
        """Display an error message"""
        # Implementation details...
    
    def confirm(self, message: str) -> bool:
        """Ask for user confirmation"""
        # Implementation details...
    
    def prompt(self, message: str) -> str:
        """Prompt for user input"""
        # Implementation details...
    
    def select_from_list(self, items: List[str], prompt: str = "Select an option:") -> Optional[int]:
        """Display a numbered list and get user selection"""
        # Implementation details...
    
    def display_table(self, headers: List[str], rows: List[List[str]], 
                     title: Optional[str] = None):
        """Display a formatted table"""
        # Implementation details...
    
    def display_search_results(self, packages: List[Dict[str, Any]]):
        """Display search results in a formatted way"""
        # Implementation details...
    
    def display_progress_bar(self, current: int, total: int, description: str = ""):
        """Display a progress bar"""
        # Implementation details...
```

## Event System

### PluginEvent Constants

```python
class PluginEvent:
    # Search events
    PRE_SEARCH = 'pre-search'
    SEARCH_SUCCESS = 'search-success'
    SEARCH_FAILURE = 'search-failure'
    POST_SEARCH = 'post-search'
    
    # Installation events
    PRE_INSTALL = 'pre-install'
    PRE_INSTALL_SUCCESS = 'pre-install-success'
    POST_INSTALL_SUCCESS = 'post-install-success'
    POST_INSTALL_FAILURE = 'post-install-failure'
    POST_INSTALL = 'post-install'
    
    # Removal events
    PRE_REMOVE = 'pre-remove'
    PRE_REMOVE_SUCCESS = 'pre-remove-success'
    POST_REMOVE_SUCCESS = 'post-remove-success'
    POST_REMOVE_FAILURE = 'post-remove-failure'
    POST_REMOVE = 'post-remove'
    
    # Health events
    PRE_HEALTH = 'pre-health'
    HEALTH_CHECK = 'health-check'
    HEALTH_FIX = 'health-fix'
    POST_HEALTH_SUCCESS = 'post-health-success'
    POST_HEALTH_FAILURE = 'post-health-failure'
    POST_HEALTH = 'post-health'
    
    # Session events
    SESSION_START = 'session-start'
    SESSION_END = 'session-end'
    
    # Error events
    ERROR = 'error'
    WARNING = 'warning'
```

### Triggering Events

```python
# In your code, trigger events like this:
self.engine._trigger_plugin_event(PluginEvent.POST_INSTALL_SUCCESS, {
    'manager': manager_name,
    'packages': packages,
    'result': result.details or {},
    'success': True,
    'scope': scope
})
```

## Advanced Plugin Development

### Creating an Advanced Plugin

1. **Create the plugin structure:**
```bash
paka config plugins create
# Choose "Advanced (Python-based plugins)"
```

2. **Implement the required methods:**
```python
class MyCustomManager(BasePackageManager):
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        # Your initialization code
    
    def initialize(self) -> bool:
        # Check if your package manager is available
        return True
    
    def cleanup(self):
        # Cleanup resources
        pass
    
    def search(self, query: str, options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Implement search functionality
        return []
    
    def install(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> bool:
        # Implement install functionality
        return True
    
    # Implement other required methods...
```

3. **Register the plugin:**
```python
def register_handlers(plugin):
    """Register plugin handlers with PAKA"""
    # Add any initialization logic here
    pass
```

### Plugin Configuration

Advanced plugins use JSON configuration:

```json
{
    "name": "my-custom-manager",
    "description": "Custom package manager plugin",
    "version": "1.0.0",
    "author": "Your Name",
    "enabled": false,
    "plugin_type": "advanced",
    "python_module": "my_custom_manager",
    "class_name": "MyCustomManager",
    "command": "my-custom-command",
    "search_timeout": 30,
    "install_timeout": 300,
    "update_timeout": 60
}
```

### Best Practices

1. **Error Handling:** Always handle exceptions gracefully
2. **Logging:** Use the provided logger for debugging
3. **Timeouts:** Implement timeouts for external commands
4. **Validation:** Validate inputs and outputs
5. **Documentation:** Document your plugin thoroughly
6. **Testing:** Test your plugin thoroughly before distribution

### Example Plugin

See the Docker plugin (`plugins/paka/docker/docker_manager.py`) for a complete example of an advanced plugin implementation.

## Directory Structure

```
paka/
├── src/core/                    # Core PAKA functionality
│   ├── engine.py               # Main engine
│   ├── config.py               # Configuration management
│   ├── plugin_manager.py       # Plugin system
│   ├── package_managers/       # Package manager implementations
│   ├── health/                 # Health system
│   ├── history.py              # History management
│   ├── session.py              # Session management
│   ├── ui.py                   # User interface
│   └── advanced_plugins/       # Advanced plugin base classes
├── plugins/                    # Plugin directory
│   ├── user/                   # User plugins
│   └── paka/                   # System plugins
└── API.md                      # This documentation
```

## Getting Help

- **Plugin Development:** Check the plugin examples in the `plugins/` directory
- **API Questions:** Review this documentation
- **Bug Reports:** Use GitHub Issues
- **Feature Requests:** Use GitHub Issues

For more information, see the main README.md file. 