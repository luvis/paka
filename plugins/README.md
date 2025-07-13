# PAKA Plugins

PAKA plugins allow you to run custom actions during package operations. Plugins use a simple INI configuration format.

## What Makes PAKA Plugins Work

- **Simple Configuration**: Plugins use INI-style text files
- **Template System**: Get started with pre-made templates
- **Variables**: Use `$packages`, `$timestamp`, `$user`, etc.
- **Multiple Actions**: Run commands, scripts, notifications, and logs
- **Three Types**: Runtime, Health Check, and Package Manager plugins

## Quick Start

### 1. Generate a Plugin Template

```bash
# Create a new plugin template
paka config plugins create

# Choose plugin type:
# - Runtime (actions during operations)
# - Health Check (custom health checks)
# - Package Manager (custom package managers)
```

### 2. Edit the Template

The plugin creator generates a `plugin.conf` template. Edit it to add your actions:

```ini
# Post-install actions (after installing packages)
[post-install]
# Uncomment and modify the actions you want:
action=notify:Successfully installed $packages!
action=run:echo "Installed $packages at $timestamp" >> ~/paka-history.log
```

### 3. Enable Your Plugin

```bash
paka config plugins enable my-plugin
```

## Template Generator

When you use `paka config plugins create`, PAKA generates a template file for you to edit. This is not an interactive wizard - you'll need to edit the generated file manually.

## Plugin Configuration Format

Plugins use a simple INI-style format:

```ini
# Plugin metadata
name=my-plugin
description=My plugin
version=1.0.0
author=Your Name
enabled=true

# Event sections
[post-install]
action=notify:Successfully installed $packages!

[pre-upgrade]
action=run:backup-system.sh
```

## Available Events

| Event | When It Triggers |
|-------|------------------|
| **Search Events** | |
| `pre-search` | Before searching for packages |
| `search-success` | Package found during search |
| `search-failure` | Package not found during search |
| `post-search` | After search operation (regardless of result) |
| **Installation Events** | |
| `pre-install` | Before installing packages |
| `pre-install-success` | Package found and about to be installed |
| `post-install-success` | After successful installation |
| `post-install-failure` | After failed installation |
| `post-install` | After installation (regardless of result) |
| **Removal Events** | |
| `pre-remove` | Before removing packages |
| `pre-remove-success` | Package found and about to be removed |
| `post-remove-success` | After successful removal |
| `post-remove-failure` | After failed removal |
| `post-remove` | After removal (regardless of result) |
| **Purge Events** | |
| `pre-purge` | Before purging packages |
| `pre-purge-success` | Package found and about to be purged |
| `post-purge-success` | After successful purge |
| `post-purge-failure` | After failed purge |
| `post-purge` | After purge (regardless of result) |
| **Upgrade Events** | |
| `pre-upgrade` | Before upgrading packages |
| `pre-upgrade-success` | Upgrades available and about to be applied |
| `post-upgrade-success` | After successful upgrade |
| `post-upgrade-failure` | After failed upgrade |
| `post-upgrade` | After upgrade (regardless of result) |
| **Update Events** | |
| `pre-update` | Before updating package lists |
| `post-update-success` | After successful update |
| `post-update-failure` | After failed update |
| `post-update` | After update (regardless of result) |
| **Health Events** | |
| `pre-health` | Before applying health fixes |
| `health-check` | During health checks |
| `health-fix` | When fixing health issues |
| `post-health-success` | After successful health operation |
| `post-health-failure` | After failed health operation |
| `post-health` | After health operation (regardless of result) |
| **Session Events** | |
| `session-start` | When PAKA starts |
| `session-end` | When PAKA ends |
| **Error Events** | |
| `error` | When any error occurs |
| `warning` | When any warning occurs |
| **Configuration Events** | |
| `config-changed` | When configuration is modified |
| `plugin-enabled` | When a plugin is enabled |
| `plugin-disabled` | When a plugin is disabled |
| **Package Manager Events** | |
| `manager-detected` | When a package manager is detected |
| `manager-enabled` | When a package manager is enabled |
| `manager-disabled` | When a package manager is disabled |
| **History Events** | |
| `history-recorded` | When an operation is recorded in history |
| `history-cleared` | When history is cleared |
| **Cache Events** | |
| `cache-updated` | When package cache is updated |
| `cache-cleared` | When package cache is cleared |

## 🔧 Action Types

### `run:command`
Execute a shell command:
```ini
action=run:echo "Installing $packages" >> /tmp/paka.log
action=run:figlet "Success!"
```

### `script:filename`
Run a script file in the plugin directory:
```ini
action=script:backup-config.sh
action=script:cleanup.sh
```

### `notify:message`
Send a desktop notification:
```ini
action=notify:Successfully installed $packages!
action=notify:System upgrade completed!
```

### `log:message`
Log a message to the plugin log file:
```ini
action=log:Operation completed successfully
action=log:Installed $packages at $timestamp
```

## 📊 Available Variables

### Package Variables
- `$packages` - List of packages being processed
- `$package-count` - Number of packages
- `$package-manager` - Name of the package manager

### Operation Variables
- `$operation` - Current operation (install, remove, upgrade, etc.)
- `$success` - Whether the operation succeeded (true/false)
- `$error` - Error message if operation failed

### System Variables
- `$user` - Current username
- `$home` - User's home directory
- `$hostname` - System hostname

### Plugin Variables
- `$plugin-name` - Name of this plugin
- `$plugin-dir` - Plugin directory path

### Time Variables
- `$timestamp` - Current timestamp (YYYY-MM-DD HH:MM:SS)
- `$date` - Current date (YYYY-MM-DD)
- `$time` - Current time (HH:MM:SS)

## 🎨 Example Plugins

### 1. Smart Snapper Plugin (Only snapshots when packages are found)
```ini
[pre-install-success]
action=run:snapper create --description "Before install $packages"

[post-install-success]
action=run:snapper create --description "After successful install $packages"

[post-install-failure]
action=run:snapper create --description "After failed install $packages (rollback point)"
```

### 2. Health Check Snapshot Plugin
```ini
[pre-health]
action=run:snapper create --description "Before applying health fixes"

[post-health-success]
action=run:snapper create --description "After successful health check"
```

### 3. Search Notification Plugin
```ini
[search-success]
action=notify:Found packages: $packages

[search-failure]
action=notify:No packages found for: $packages
```

### 4. Figlet Celebration Plugin
```ini
[post-install-success]
action=run:figlet "Packages $packages were successfully installed, what a hero you are!"
action=notify:Successfully installed $packages!
```

### 5. Activity Logger Plugin
```ini
[post-install-success]
action=log:Successfully installed $packages
action=run:echo "[$timestamp] INSTALL SUCCESS: $packages" >> ~/paka-activity.log

[post-remove-success]
action=log:Successfully removed $packages
action=run:echo "[$timestamp] REMOVE SUCCESS: $packages" >> ~/paka-activity.log

[error]
action=run:echo "[$timestamp] ERROR: $error" >> ~/paka-activity.log
```

### 6. Custom Health Check Plugin
```ini
[health-check]
action=run:df -h | grep -E "(/$|/home)" >> /tmp/paka-health.log

[health-fix]
action=run:find /tmp -type f -atime +7 -delete 2>/dev/null || true
action=notify:Applied custom health fixes
```

### 7. Backup Plugin
```ini
[pre-install-success]
action=run:tar -czf ~/backup-$(date +%Y%m%d).tar.gz /etc 2>/dev/null || true
action=notify:Created backup before installation

[post-install-success]
action=notify:Installation completed! Backup available in ~/
```

### 8. Session Logger Plugin
```ini
[session-start]
action=run:echo "[$timestamp] PAKA session started" >> ~/paka-sessions.log

[session-end]
action=run:echo "[$timestamp] PAKA session ended" >> ~/paka-sessions.log
```

### 9. Error Handler Plugin
```ini
[error]
action=notify:An error occurred: $error
action=run:echo "[$timestamp] ERROR: $error" >> ~/paka-errors.log

[warning]
action=notify:Warning: $warning
action=run:echo "[$timestamp] WARNING: $warning" >> ~/paka-warnings.log
```

### 10. Package Manager Monitor Plugin
```ini
[manager-detected]
action=log:Detected package manager: $package-manager

[manager-enabled]
action=notify:Enabled package manager: $package-manager

[manager-disabled]
action=notify:Disabled package manager: $package-manager
```

## 🛠️ Plugin Management

### List All Plugins
```bash
paka config plugins list
```

### Enable/Disable Plugins
```bash
paka config plugins enable plugin-name
paka config plugins disable plugin-name
```

### Check Plugin Syntax
```bash
paka config plugins check
```

### Get Plugin Help
```bash
paka config plugins help
```

## 📁 Plugin Directory Structure

```
plugins/
├── my-plugin/
│   ├── plugin.conf          # Plugin configuration
│   ├── README.md            # Plugin documentation
│   └── my-script.sh         # Optional script files
├── another-plugin/
│   └── plugin.conf
└── README.md                # This file
```

## 🎯 Plugin Types Explained

### 1. Runtime Plugins
Actions that happen during PAKA operations:
- Notifications
- Logging
- Backups
- Celebrations
- Custom scripts

### 2. Health Check Plugins
Custom health checks and fixes:
- Disk usage monitoring
- Temp file cleanup
- Permission fixes
- Custom maintenance tasks

### 3. Package Manager Plugins
Support for custom package managers:
- Docker containers
- Custom package formats
- Specialized installers

## 💡 Tips & Best Practices

- Use short, clear action names
- Test your plugin before enabling
- Keep actions fast and non-blocking
- Use variables to customize your actions

## 🔍 Troubleshooting

### Plugin Not Working?
1. Check if plugin is enabled: `paka config plugins list`
2. Check plugin syntax: `paka config plugins check`
3. Look at plugin log: `cat plugins/your-plugin/plugin.log`
4. Test commands manually

### Common Issues
- **Permission denied**: Make scripts executable with `chmod +x script.sh`
- **Command not found**: Use full paths or check if command is installed
- **Variables not expanding**: Check variable syntax and spelling

### Getting Help
```bash
# Show comprehensive plugin help
paka config plugins help

# Check plugin syntax
paka config plugins check

# List all plugins
paka config plugins list
```

## 🎉 Ready to Create?

1. Run: `paka config plugins create`
2. Choose your plugin type
3. Edit the generated `plugin.conf` file
4. Uncomment and modify the actions you want
5. Enable your plugin: `paka config plugins enable your-plugin-name`
6. Test it by running a PAKA operation 