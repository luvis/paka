# Snapper Plugin for PAKA

The Snapper plugin creates automatic system snapshots before and after package operations and health checks, providing a safety net for system recovery.

## Features

- **Smart Package Operation Snapshots**: Automatic snapshots only when packages are found and about to be installed
- **Health Fix Snapshots**: Snapshots before applying health fixes, not before health checks
- **Success/Failure Tracking**: Different snapshot descriptions based on operation success
- **Rollback Points**: Special snapshots for failed operations to enable easy rollback
- **Interactive Configuration**: Easy setup with granular control over which events create snapshots
- **Availability Checking**: Automatically detects if Snapper is installed and available

## Installation

### Enable the Plugin
```bash
# Enable the plugin
paka config plugins enable snapper

# The plugin will automatically run interactive configuration
```

### Interactive Configuration

When you enable the Snapper plugin, it will automatically run an interactive configuration wizard that asks you which events should create snapshots:

```
Snapper Plugin Configuration
===================================
Configure which events should create snapshots:

Create snapshots Before installing packages (only when packages are found)? [Y/n]: y
Create snapshots After installing packages (with success/failure status)? [Y/n]: y
Create snapshots Before removing packages? [Y/n]: y
Create snapshots After removing packages (with success/failure status)? [Y/n]: y
Create snapshots Before upgrading system packages? [Y/n]: y
Create snapshots After upgrading system packages (with success/failure status)? [Y/n]: y
Create snapshots Before applying health fixes? [Y/n]: y
Create snapshots After successful health checks? [y/N]: n
Create snapshots After failed health checks (rollback point)? [Y/n]: y
Create snapshots Before applying health fixes? [Y/n]: y

Snapper plugin configuration saved!

Enabled events:
  ✓ Before installing packages (only when packages are found)
  ✓ After installing packages (with success/failure status)
  ✓ Before removing packages
  ✓ After removing packages (with success/failure status)
  ✓ Before upgrading system packages
  ✓ After upgrading system packages (with success/failure status)
  ✓ Before applying health fixes
  ✓ After failed health checks (rollback point)
  ✓ Before applying health fixes
```

### Verify Snapper Installation
```bash
# Check if snapper is available
which snapper

# List existing snapshots
snapper list
```

## Configuration

### Manual Configuration
You can manually edit the configuration file at `~/.config/paka/snapper_config.json`:

```json
{
  "pre_install": true,
  "post_install": true,
  "pre_remove": true,
  "post_remove": true,
  "pre_upgrade": true,
  "post_upgrade": true,
  "pre_health": true,
  "post_health_success": false,
  "post_health_failure": true,
  "health_fix": true
}
```

### Reconfigure the Plugin
```bash
# Reconfigure the plugin
paka config plugins configure snapper
```

## Events Covered

### Package Operations
- **pre-install-success**: Before installing packages (only when packages are found)
- **post-install**: After installing packages (with success/failure status)
- **pre-remove**: Before removing packages
- **post-remove**: After removing packages (with success/failure status)
- **pre-upgrade**: Before upgrading system packages
- **post-upgrade**: After upgrading system packages (with success/failure status)

### Health Operations
- **pre-health**: Before applying health fixes
- **post-health-success**: After successful health checks
- **post-health-failure**: After failed health checks (creates rollback point)
- **health-fix**: Before applying health fixes

## Usage Examples

### Package Installation
```bash
# Install packages (creates pre/post snapshots automatically)
paka install firefox vim

# Snapshots created:
# - "PAKA pre-install: firefox vim"
# - "PAKA post-install: firefox vim (success)"
```

### Health Checks
```bash
# Run health checks (creates post snapshots)
paka health

# Snapshots created:
# - "PAKA post-health: after successful health check"

# Apply fixes (creates pre-fix snapshot)
paka health --fix-all

# Snapshots created:
# - "PAKA pre-health: before applying health fixes"
# - "PAKA pre-health-fix: before applying fixes"
```

### System Upgrades
```bash
# Upgrade system (creates pre/post snapshots)
paka upgrade

# Snapshots created:
# - "PAKA pre-upgrade: system packages"
# - "PAKA post-upgrade: system packages (success)"
```

## Rollback and Recovery

### List Snapshots
```bash
# List all PAKA snapshots
snapper list | grep PAKA

# List recent snapshots
snapper list -t pre-post
```

### Rollback to Previous State
```bash
# Rollback to a specific snapshot
snapper undochange <snapshot_number>

# Rollback to the last good state
snapper undochange $(snapper list | grep "PAKA post-install.*success" | tail -1 | awk '{print $1}')
```

### Recovery from Failed Operations
```bash
# If a package installation failed, rollback to pre-install snapshot
snapper undochange $(snapper list | grep "PAKA pre-install" | tail -1 | awk '{print $1}')

# If health fixes caused issues, rollback to pre-health snapshot
snapper undochange $(snapper list | grep "PAKA pre-health" | tail -1 | awk '{print $1}')
```

## Safety Features

### Automatic Availability Check
- Plugin automatically checks if Snapper is available
- Gracefully skips snapshots if Snapper is not installed
- Provides installation instructions if Snapper is missing

### Error Handling
- Failed snapshot creation doesn't stop PAKA operations
- Detailed error logging for troubleshooting
- Graceful degradation when Snapper fails

### Context Awareness
- Includes package names in snapshot descriptions
- Tracks operation success/failure status
- Provides meaningful rollback points

### Granular Control
- Choose exactly which events create snapshots
- Disable specific events you don't want
- Easy reconfiguration at any time

## Troubleshooting

### Snapper Not Available
```bash
# Install Snapper (Fedora/RHEL)
sudo dnf install snapper

# Install Snapper (Ubuntu/Debian)
sudo apt install snapper

# Install Snapper (Arch)
sudo pacman -S snapper
```

### Permission Issues
```bash
# Ensure user can run snapper
sudo usermod -a -G snapper $USER

# Check snapper configuration
sudo snapper list-configs
```

### Snapshot Cleanup
```bash
# Clean old snapshots (keep last 10)
snapper list | grep PAKA | tail -n +11 | awk '{print $1}' | xargs -r snapper delete

# Clean snapshots older than 30 days
snapper list | grep PAKA | awk '$2 < "'$(date -d '30 days ago' +%Y-%m-%d)'" {print $1}' | xargs -r snapper delete
```

## Integration with PAKA

The Snapper plugin integrates seamlessly with PAKA's ecosystem:

- **Event System**: Responds to all relevant PAKA events
- **History Integration**: Snapshots are logged in PAKA's history
- **Health System**: Provides safety net for health check operations
- **Configuration**: Interactive configuration through PAKA's config system
- **Plugin Management**: Can be enabled/disabled through PAKA's plugin system

## Best Practices

1. **Enable Early**: Enable the plugin before making system changes
2. **Configure Carefully**: Choose which events you want snapshots for
3. **Monitor Space**: Regularly clean old snapshots to save disk space
4. **Test Rollbacks**: Periodically test rollback functionality
5. **Document Snapshots**: Use meaningful descriptions for manual snapshots
6. **Backup Strategy**: Combine with other backup solutions for comprehensive protection

## Configuration Tips

### Conservative Setup (Minimal Snapshots)
- Enable only `pre_install`, `pre_upgrade`, and `pre_health`
- Good for systems with limited disk space

### Balanced Setup (Recommended)
- Enable all events except `post_health_success`
- Provides good coverage without excessive snapshots

### Comprehensive Setup (Maximum Safety)
- Enable all events
- Best for critical systems or when testing new packages 