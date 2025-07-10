# PACA - Universal Package Manager Wrapper

PACA (Package Manager Command Aggregator) is a smart, user-friendly wrapper for multiple package managers that provides a consistent and beautiful interface across different Linux distributions.

## Features

- **Unified Interface**: Single command syntax for multiple package managers
- **Intelligent Search**: Smart filtering, categorization, and fuzzy matching
- **Advanced Plugin System**: Simple templates for non-technical users, sophisticated hooks for advanced users
- **Learning System**: Remembers user preferences and learns from behavior
- **Comprehensive History**: Track installations with dependency trees and rollback capabilities
- **Health System**: Multi-manager health checks with risk assessment and interactive fixes
- **Profile System**: Configurable dependency profiles with learning capabilities
- **Shell Integration**: Optional command-not-found suggestions
- **Beautiful Output**: Colorful, easy-to-read tables and progress indicators

## Supported Package Managers

### Native Package Managers
- **DNF** (Fedora, RHEL, CentOS)
- **APT** (Debian, Ubuntu)
- **Pacman** (Arch Linux)
- **Zypper** (openSUSE)
- **Portage/Emerge** (Gentoo)
- **Yay** (AUR helper)
- **Slackpkg** (Slackware)
- **APK** (Alpine)
- **XBPS** (Void Linux)
- **APX** (Vanilla OS)
- **Nix** (NixOS, Universal)
- **Slpkg** (Slackware)

### Universal Package Managers
- **Flatpak** (Universal)
- **Snap** (Universal)

### Plugin-Based Managers
- **Docker** (via plugin)

## Quick Start

```bash
# Clone and install
git clone https://github.com/luvis/paca.git
cd paca
./install.sh

# Basic usage
paca search <package>          # Search across all package managers
paca install <package>         # Interactive package installation
paca remove <package>          # Remove packages
paca update                    # Update package lists
paca upgrade                   # Install available updates
paca health                    # Comprehensive health check
paca history                   # View installation history
paca config                    # Interactive configuration
```

## Architecture

PACA is built with extensibility and user experience in mind:
- **Core Engine**: Command orchestration and session management
- **Package Manager Registry**: Manages all package manager implementations
- **Session Manager**: Tracks user behavior and preferences
- **History Manager**: Comprehensive installation tracking with rollback
- **Health Manager**: Multi-manager health monitoring and fixes
- **UI Manager**: Beautiful, colorful output with progress indicators
- **Plugin Manager**: Extensible plugin system with simple templates
- **Config Manager**: Hierarchical configuration management

## Licensing

PACA is dual-licensed to accommodate both open-source and commercial use:

### Open Source License (GPLv3)
You may use, modify, and redistribute PACA under the terms of the GNU General Public License v3 (GPLv3). This means:
- You can freely use PACA for personal and open-source projects
- You can modify the source code and distribute your modifications
- Any derivative works must also be licensed under the GPLv3
- See the [LICENSE](LICENSE) file for the full GPLv3 text

### Commercial License
If you wish to use PACA in proprietary, closed-source, or commercial products, a separate commercial license is required. This includes:
- Using PACA in proprietary software
- Distributing PACA as part of a commercial product
- Using PACA in enterprise environments with proprietary modifications
- Any use that would otherwise violate the GPLv3 terms

**For commercial licensing inquiries, please contact:** hello@hoozter.com

## Repository

https://github.com/luvis/paca

## Contact

- **Commercial Licensing**: hello@hoozter.com
- **Support & General Inquiries**: hello@hoozter.com
- **Bug Reports**: Please use GitHub Issues
- **Feature Requests**: Please use GitHub Issues

## License

See [LICENSE](LICENSE) for the full GNU GPLv3 text. 