#!/bin/bash
# PAKA Installation Script with Wizard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# PAKA version
PAKA_VERSION="0.1.0"

# Installation directories
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="/etc/paka"
USER_CONFIG_DIR="$HOME/.config/paka"
PLUGIN_DIR="/usr/local/share/paka/plugins"
USER_PLUGIN_DIR="$HOME/.local/share/paka/plugins"
TEMP_CONFIG="/tmp/paka_install_config.json"

# Installation configuration
INSTALL_CONFIG=""

# Function to display banner
show_banner() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    PAKA Package Manager                      ║${NC}"
    echo -e "${BLUE}║              Universal Package Manager Wrapper               ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${BLUE}Version: ${PAKA_VERSION}${NC}"
    echo ""
}

# Function to display section header
section_header() {
    local title="$1"
    echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    $title${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
}

# Function to display step
step() {
    local step_num="$1"
    local description="$2"
    echo -e "\n${YELLOW}[Step $step_num]${NC} $description"
    echo -e "${YELLOW}${'─' * 60}${NC}"
}

# Function to prompt for input
prompt() {
    local message="$1"
    local default="$2"
    local input
    
    if [[ -n "$default" ]]; then
        echo -e "${BLUE}$message${NC} [${GREEN}$default${NC}]: "
    else
        echo -e "${BLUE}$message${NC}: "
    fi
    
    read -r input
    if [[ -z "$input" && -n "$default" ]]; then
        echo "$default"
    else
        echo "$input"
    fi
}

# Function to prompt for yes/no
prompt_yes_no() {
    local message="$1"
    local default="$2"
    local input
    
    if [[ "$default" == "y" ]]; then
        echo -e "${BLUE}$message${NC} [${GREEN}Y${NC}/n]: "
    else
        echo -e "${BLUE}$message${NC} [y/${GREEN}N${NC}]: "
    fi
    
    read -r input
    input=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    
    if [[ -z "$input" ]]; then
        [[ "$default" == "y" ]]
    else
        [[ "$input" == "y" || "$input" == "yes" ]]
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect package managers
detect_package_managers() {
    local managers=()
    
    if command_exists dnf; then
        managers+=("dnf")
    fi
    
    if command_exists apt; then
        managers+=("apt")
    fi
    
    if command_exists pacman; then
        managers+=("pacman")
    fi
    
    if command_exists zypper; then
        managers+=("zypper")
    fi
    
    if command_exists emerge; then
        managers+=("emerge")
    fi
    
    if command_exists yay; then
        managers+=("yay")
    fi
    
    if command_exists slackpkg; then
        managers+=("slackpkg")
    fi
    
    if command_exists apk; then
        managers+=("apk")
    fi
    
    if command_exists xbps-install; then
        managers+=("xbps")
    fi
    
    if command_exists apx; then
        managers+=("apx")
    fi
    
    if command_exists flatpak; then
        managers+=("flatpak")
    fi
    
    if command_exists snap; then
        managers+=("snap")
    fi
    
    echo "${managers[@]}"
}

# Function to run installation wizard
run_installation_wizard() {
    section_header "PAKA Installation Wizard"
    
    # Step 1: System Check
    step "1" "System Requirements Check"
    
    echo -e "${YELLOW}Checking Python version...${NC}"
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required but not installed${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo -e "${GREEN}✓ Found Python ${PYTHON_VERSION}${NC}"
    
    PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 7 ]]; then
        echo -e "${RED}Error: Python 3.7 or higher is required${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Python version meets requirements${NC}"
    
    # Step 2: Package Manager Detection
    step "2" "Package Manager Detection"
    
    echo -e "${YELLOW}Detecting available package managers...${NC}"
    local detected_managers=($(detect_package_managers))
    
    if [[ ${#detected_managers[@]} -eq 0 ]]; then
        echo -e "${RED}Warning: No supported package managers detected${NC}"
        echo -e "${YELLOW}PAKA will still install but may have limited functionality${NC}"
    else
        echo -e "${GREEN}Detected package managers:${NC}"
        for manager in "${detected_managers[@]}"; do
            echo -e "  ✓ ${manager^^}"
        done
    fi
    
    # Step 3: Installation Options
    step "3" "Installation Options"
    
    local install_scope=$(prompt "Installation scope" "user")
    if [[ "$install_scope" != "system" && "$install_scope" != "user" ]]; then
        install_scope="user"
    fi
    
    local enable_shell_integration=$(prompt_yes_no "Enable shell integration (command-not-found suggestions)" "y")
    local enable_plugins=$(prompt_yes_no "Enable plugin system" "y")
    local create_sample_plugins=$(prompt_yes_no "Create sample plugins" "y")
    
    # Package manager selection
    echo -e "${CYAN}Select package managers to enable:${NC}"
    echo -e "${YELLOW}Note: PAKA will automatically detect available package managers${NC}"
    echo ""
    
    package_managers=(
        "dnf (Fedora/RHEL/CentOS)"
        "apt (Debian/Ubuntu)"
        "pacman (Arch Linux)"
        "flatpak (Universal)"
        "snap (Universal)"
        "appimage (Revolutionary AppImage manager)"
    )
    
    for i in "${!package_managers[@]}"; do
        echo -e "${GREEN}$((i+1)).${NC} ${package_managers[$i]}"
    done
    echo -e "${GREEN}7.${NC} All (recommended)"
    echo -e "${GREEN}8.${NC} Auto-detect (default)"
    
    read -p "Enter your choice (1-8): " pkg_choice
    
    case $pkg_choice in
        1) ENABLE_DNF=true ;;
        2) ENABLE_APT=true ;;
        3) ENABLE_PACMAN=true ;;
        4) ENABLE_FLATPAK=true ;;
        5) ENABLE_SNAP=true ;;
        6) ENABLE_APPIMAGE=true ;;
        7) ENABLE_ALL=true ;;
        8) ENABLE_AUTO=true ;;
        *) ENABLE_AUTO=true ;;
    esac
    
    # Step 4: Plugin Configuration
    if [[ "$enable_plugins" == "true" ]]; then
        step "4" "Plugin Configuration"
        
        if [[ "$create_sample_plugins" == "true" ]]; then
            local create_notification_plugin=$(prompt_yes_no "Create notification plugin" "y")
            local create_activity_logger=$(prompt_yes_no "Create activity logger plugin" "y")
            local create_celebration_plugin=$(prompt_yes_no "Create celebration plugin (figlet)" "n")
        fi
    fi
    
    # Step 5: Advanced Options
    step "5" "Advanced Options"
    
    local enable_health_checks=$(prompt_yes_no "Enable automatic health checks" "y")
    local enable_history_tracking=$(prompt_yes_no "Enable installation history tracking" "y")
    local enable_learning=$(prompt_yes_no "Enable preference learning" "y")
    
    # Create temporary configuration
    cat > "$TEMP_CONFIG" << EOF
{
    "install_scope": "$install_scope",
    "enable_shell_integration": $enable_shell_integration,
    "enable_plugins": $enable_plugins,
    "create_sample_plugins": $create_sample_plugins,
    "create_notification_plugin": ${create_notification_plugin:-false},
    "create_activity_logger": ${create_activity_logger:-false},
    "create_celebration_plugin": ${create_celebration_plugin:-false},
    "enable_health_checks": $enable_health_checks,
    "enable_history_tracking": $enable_history_tracking,
    "enable_learning": $enable_learning,
    "detected_managers": [$(printf '"%s"' "${detected_managers[@]}" | tr '\n' ',' | sed 's/,$//')]
}
EOF
    
    echo -e "${GREEN}✓ Installation configuration saved${NC}"
}

# Function to perform installation
perform_installation() {
    section_header "Installing PAKA"
    
    # Load configuration
    if [[ ! -f "$TEMP_CONFIG" ]]; then
        echo -e "${RED}Error: Installation configuration not found${NC}"
        echo -e "${YELLOW}Please run the installation wizard first${NC}"
        exit 1
    fi
    
    local install_scope=$(jq -r '.install_scope' "$TEMP_CONFIG")
    local enable_shell_integration=$(jq -r '.enable_shell_integration' "$TEMP_CONFIG")
    local enable_plugins=$(jq -r '.enable_plugins' "$TEMP_CONFIG")
    local create_sample_plugins=$(jq -r '.create_sample_plugins' "$TEMP_CONFIG")
    
    # Check if we need sudo
    local need_sudo=false
    if [[ "$install_scope" == "system" ]] || [[ "$enable_shell_integration" == "true" ]]; then
        need_sudo=true
    fi
    
    if [[ "$need_sudo" == "true" ]] && [[ $EUID -ne 0 ]]; then
        echo -e "${YELLOW}This installation requires system-wide access${NC}"
        echo -e "${YELLOW}You will be prompted for your password${NC}"
        
        if ! prompt_yes_no "Continue with installation?" "y"; then
            echo -e "${YELLOW}Installation cancelled${NC}"
            exit 0
        fi
    fi
    
    # Create directories
    step "1" "Creating directories"
    
    if [[ "$install_scope" == "system" ]] || [[ $EUID -eq 0 ]]; then
        sudo mkdir -p "$INSTALL_DIR"
        sudo mkdir -p "$CONFIG_DIR"
        sudo mkdir -p "$PLUGIN_DIR"
        echo -e "${GREEN}✓ System directories created${NC}"
    fi
    
    mkdir -p "$USER_CONFIG_DIR"
    mkdir -p "$USER_PLUGIN_DIR"
    echo -e "${GREEN}✓ User directories created${NC}"
    
    # Install PAKA executable
step "2" "Installing PAKA executable"
    
    if [[ "$install_scope" == "system" ]] || [[ $EUID -eq 0 ]]; then
        sudo cp paka "$INSTALL_DIR/"
sudo chmod +x "$INSTALL_DIR/paka"
echo -e "${GREEN}✓ PAKA installed to $INSTALL_DIR/paka${NC}"
    else
        # Install to user directory
        mkdir -p "$HOME/.local/bin"
        cp paka "$HOME/.local/bin/"
chmod +x "$HOME/.local/bin/paka"
echo -e "${GREEN}✓ PAKA installed to $HOME/.local/bin/paka${NC}"
        echo -e "${YELLOW}Note: Add $HOME/.local/bin to your PATH if not already there${NC}"
    fi
    
    # Install Python source
    step "3" "Installing Python source"
    
    if [[ "$install_scope" == "system" ]] || [[ $EUID -eq 0 ]]; then
        sudo mkdir -p "/usr/local/share/paka"
sudo cp -r src "/usr/local/share/paka/"
        echo -e "${GREEN}✓ Python source installed${NC}"
    else
        mkdir -p "$HOME/.local/share/paka"
cp -r src "$HOME/.local/share/paka/"
        echo -e "${GREEN}✓ Python source installed${NC}"
    fi
    
    # Setup configuration
    step "4" "Setting up configuration"
    
    if [[ ! -f "$USER_CONFIG_DIR/config.json" ]]; then
        cp src/core/config.py "$USER_CONFIG_DIR/config.json" 2>/dev/null || true
        echo -e "${GREEN}✓ User configuration created${NC}"
    fi
    
    # Setup plugins
    if [[ "$enable_plugins" == "true" ]]; then
        step "5" "Setting up plugins"
        
        # Copy existing plugins from codebase
        copy_existing_plugins
        
        if [[ "$create_sample_plugins" == "true" ]]; then
            local create_notification_plugin=$(jq -r '.create_notification_plugin' "$TEMP_CONFIG")
            local create_activity_logger=$(jq -r '.create_activity_logger' "$TEMP_CONFIG")
            local create_celebration_plugin=$(jq -r '.create_celebration_plugin' "$TEMP_CONFIG")
            
            if [[ "$create_notification_plugin" == "true" ]]; then
                create_notification_plugin
            fi
            
            if [[ "$create_activity_logger" == "true" ]]; then
                create_activity_logger_plugin
            fi
            
            if [[ "$create_celebration_plugin" == "true" ]]; then
                create_celebration_plugin
            fi
        fi
    fi
    
    # Setup shell integration
    if [[ "$enable_shell_integration" == "true" ]]; then
        step "6" "Setting up shell integration"
        setup_shell_integration
    fi
    
    # Create uninstaller
    step "7" "Creating uninstaller"
    create_uninstaller
    
    # Cleanup
    rm -f "$TEMP_CONFIG"
    
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Installation Complete!                    ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    
    echo -e "\n${GREEN}Quick Start:${NC}"
    if [[ "$install_scope" == "system" ]] || [[ $EUID -eq 0 ]]; then
        echo "  paka --help                    # Show help"
    else
        echo "  ~/.local/bin/paka --help       # Show help"
    fi
    echo "  paka health                    # Check system health"
    echo "  paka search firefox            # Search for packages"
    echo "  paka install vim               # Install a package"
    
    echo -e "\n${GREEN}Configuration:${NC}"
    echo "  User config: $USER_CONFIG_DIR"
    echo "  Plugins: $USER_PLUGIN_DIR"
    
    echo -e "\n${GREEN}To uninstall:${NC}"
    echo "  ./uninstall.sh"
}

# Function to create notification plugin
create_notification_plugin() {
    local plugin_dir="$USER_PLUGIN_DIR/notifications"
    mkdir -p "$plugin_dir"
    
    cat > "$plugin_dir/plugin.conf" << 'EOF'
# Notification Plugin
# This plugin sends desktop notifications for PAKA operations

# Plugin metadata
description=Desktop notifications for PAKA operations
version=1.0.0
author=PAKA Team
enabled=true

# Post-install actions (after installing packages)
[post-install]
action=notify:Successfully installed $packages!

# Post-remove actions (after removing packages)
[post-remove]
action=notify:Successfully removed $packages!

# Post-upgrade actions (after upgrading packages)
[post-upgrade]
action=notify:System upgrade completed!
EOF
    
    echo -e "${GREEN}✓ Notification plugin created${NC}"
}

# Function to create activity logger plugin
create_activity_logger_plugin() {
    local plugin_dir="$USER_PLUGIN_DIR/activity-logger"
    mkdir -p "$plugin_dir"
    
    cat > "$plugin_dir/plugin.conf" << 'EOF'
# Activity Logger Plugin
# This plugin logs all PAKA activities to a file

# Plugin metadata
description=Logs all PAKA activities to a file
version=1.0.0
author=PAKA Team
enabled=true

# Post-install actions (after installing packages)
[post-install]
action=log:Successfully installed $packages
action=run:echo "[$timestamp] INSTALL SUCCESS: $packages" >> ~/paka-activity.log

# Post-remove actions (after removing packages)
[post-remove]
action=log:Successfully removed $packages
action=run:echo "[$timestamp] REMOVE SUCCESS: $packages" >> ~/paka-activity.log

# Post-upgrade actions (after upgrading packages)
[post-upgrade]
action=log:Successfully upgraded packages
action=run:echo "[$timestamp] UPGRADE SUCCESS" >> ~/paka-activity.log
EOF
    
    echo -e "${GREEN}✓ Activity logger plugin created${NC}"
}

# Function to copy existing plugins from codebase
copy_existing_plugins() {
    local current_dir=$(pwd)
    local codebase_plugins_dir="$current_dir/plugins"
    
    if [[ -d "$codebase_plugins_dir" ]]; then
        echo -e "${YELLOW}Copying existing plugins from codebase...${NC}"
        
        # Copy system plugins (paka directory)
        if [[ -d "$codebase_plugins_dir/paka" ]]; then
            for plugin_dir in "$codebase_plugins_dir/paka"/*; do
                if [[ -d "$plugin_dir" ]]; then
                    local plugin_name=$(basename "$plugin_dir")
                    local target_dir="$PLUGIN_DIR/$plugin_name"
                    
                    if [[ -d "$target_dir" ]]; then
                        sudo rm -rf "$target_dir"
                    fi
                    
                    sudo cp -r "$plugin_dir" "$PLUGIN_DIR/"
                    echo -e "${GREEN}✓ Copied system plugin: $plugin_name${NC}"
                fi
            done
        fi
        
        # Copy user plugins (user directory)
        if [[ -d "$codebase_plugins_dir/user" ]]; then
            for plugin_dir in "$codebase_plugins_dir/user"/*; do
                if [[ -d "$plugin_dir" ]]; then
                    local plugin_name=$(basename "$plugin_dir")
                    local target_dir="$USER_PLUGIN_DIR/$plugin_name"
                    
                    if [[ -d "$target_dir" ]]; then
                        rm -rf "$target_dir"
                    fi
                    
                    cp -r "$plugin_dir" "$USER_PLUGIN_DIR/"
                    echo -e "${GREEN}✓ Copied user plugin: $plugin_name${NC}"
                fi
            done
        fi
        
        echo -e "${GREEN}✓ Existing plugins copied successfully${NC}"
    else
        echo -e "${YELLOW}No existing plugins found in codebase${NC}"
    fi
}

# Function to create celebration plugin
create_celebration_plugin() {
    local plugin_dir="$USER_PLUGIN_DIR/figlet-celebration"
    mkdir -p "$plugin_dir"
    
    cat > "$plugin_dir/plugin.conf" << 'EOF'
# Figlet Celebration Plugin
# This plugin celebrates successful package installations with ASCII art!

# Plugin metadata
description=Celebrates successful package installations with ASCII art
version=1.0.0
author=PAKA Team
enabled=true

# Post-install actions (after installing packages)
[post-install]
action=run:figlet "Packages $packages were successfully installed, what a hero you are!"
action=notify:Successfully installed $packages!

# Post-upgrade actions (after upgrading packages)
[post-upgrade]
action=run:figlet "System upgraded successfully! You're amazing!"
action=notify:System upgrade completed!
EOF
    
    echo -e "${GREEN}✓ Celebration plugin created${NC}"
}

# Function to setup shell integration
setup_shell_integration() {
    # Bash completion
    local bash_completion_dir="/etc/bash_completion.d"
    if [[ -d "$bash_completion_dir" ]]; then
        cat > /tmp/paka.bash << 'EOF'
# PAKA bash completion
_paka() {
    local cur prev opts cmds
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    cmds="install remove purge update upgrade search health history config shell-not-found"
    
    if [[ ${cur} == * ]] ; then
        case "${prev}" in
            paka)
                COMPREPLY=( $(compgen -W "${cmds}" -- ${cur}) )
                return 0
                ;;
            install|remove|purge)
                return 0
                ;;
            search)
                return 0
                ;;
            *)
                return 0
                ;;
        esac
    fi
}

complete -F _paka paka
EOF
        
        sudo cp /tmp/paka.bash "$bash_completion_dir/"
        rm /tmp/paka.bash
        echo -e "${GREEN}✓ Bash completion installed${NC}"
    fi
    
    # Zsh completion
    local zsh_completion_dir="/usr/local/share/zsh/site-functions"
    if [[ -d "$zsh_completion_dir" ]]; then
        sudo mkdir -p "$zsh_completion_dir"
        cat > /tmp/_paka << 'EOF'
#compdef paka

_paka() {
    local curcontext="$curcontext" state line
    typeset -A opt_args

    _arguments -C \
        '1: :->cmds' \
        '*:: :->args'

    case "$state" in
        cmds)
            local commands
            commands=(
                'install:Install packages'
                'remove:Remove packages'
                'purge:Remove packages and configuration'
                'update:Refresh package lists'
                'upgrade:Upgrade packages'
                'search:Search for packages'
                'health:Check system health'
                'history:Manage installation history'
                'config:Manage configuration'
                'shell-not-found:Handle command-not-found events'
            )
            _describe -t commands 'paka commands' commands
            ;;
        args)
            case $line[1] in
                install|remove|purge)
                    ;;
                search)
                    ;;
            esac
            ;;
    esac
}

_paka "$@"
EOF
        
        sudo cp /tmp/_paka "$zsh_completion_dir/"
        rm /tmp/_paka
        echo -e "${GREEN}✓ Zsh completion installed${NC}"
    fi
}

# Function to create uninstaller
create_uninstaller() {
    cat > uninstall.sh << 'EOF'
#!/bin/bash
# PAKA Uninstall Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    PAKA Uninstaller                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to prompt for yes/no
prompt_yes_no() {
    local message="$1"
    local default="$2"
    local input
    
    if [[ "$default" == "y" ]]; then
        echo -e "${BLUE}$message${NC} [${GREEN}Y${NC}/n]: "
    else
        echo -e "${BLUE}$message${NC} [y/${GREEN}N${NC}]: "
    fi
    
    read -r input
    input=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    
    if [[ -z "$input" ]]; then
        [[ "$default" == "y" ]]
    else
        [[ "$input" == "y" || "$input" == "yes" ]]
    fi
}

# Function to prompt for granular uninstall options
prompt_granular_uninstall() {
    echo -e "${YELLOW}Select components to remove (y/n):${NC}"
    read -p "Remove PAKA system executable (/usr/local/bin/paka)? [y/N]: " rm_bin
    read -p "Remove PAKA user executable (~/.local/bin/paka)? [y/N]: " rm_user_bin
    read -p "Remove PAKA system Python source (/usr/local/share/paka)? [y/N]: " rm_sys_py
    read -p "Remove PAKA user Python source (~/.local/share/paka)? [y/N]: " rm_user_py
    read -p "Remove system config (/etc/paka)? [y/N]: " rm_sys_cfg
    read -p "Remove user config (~/.config/paka)? [y/N]: " rm_user_cfg
    read -p "Remove system plugins (/usr/local/share/paka/plugins)? [y/N]: " rm_sys_plugins
    read -p "Remove user plugins (~/.local/share/paka/plugins)? [y/N]: " rm_user_plugins
    read -p "Remove user data dir (~/.local/share/paka)? [y/N]: " rm_user_data
    read -p "Remove bash completion (/etc/bash_completion.d/paka.bash)? [y/N]: " rm_bash_comp
    read -p "Remove zsh completion (/usr/local/share/zsh/site-functions/_paka)? [y/N]: " rm_zsh_comp
    read -p "Remove PAKA logs (~/.local/share/paka/logs)? [y/N]: " rm_user_logs
    echo
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}Error: This script should not be run as root${NC}"
   echo "Please run as a regular user. The script will use sudo when needed."
   exit 1
fi

echo -e "${YELLOW}This will completely remove PAKA from your system.${NC}"
echo -e "${YELLOW}This action cannot be undone.${NC}"
echo ""

if ! prompt_yes_no "Are you sure you want to uninstall PAKA?" "n"; then
    echo -e "${YELLOW}Uninstallation cancelled${NC}"
    exit 0
fi

echo -e "\n${YELLOW}Uninstallation Options:${NC}"
echo "1. Remove PAKA only (keep user data)"
echo "2. Remove PAKA and user data (recommended)"
echo "3. Remove PAKA and ALL data (complete cleanup)"

read -r -p "Choose option (1-3): " choice

case $choice in
    1)
        echo -e "${YELLOW}Removing PAKA only...${NC}"
        remove_paka_only=true
        remove_user_data=false
        remove_all_data=false
        ;;
    2)
        echo -e "${YELLOW}Removing PAKA and user data...${NC}"
        remove_paka_only=false
        remove_user_data=true
        remove_all_data=false
        ;;
    3)
        echo -e "${YELLOW}Removing PAKA and ALL data...${NC}"
        remove_paka_only=false
        remove_user_data=true
        remove_all_data=true
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "\n${YELLOW}Starting uninstallation...${NC}"

prompt_granular_uninstall

# Remove selected components
if [[ "$rm_bin" =~ ^[Yy]$ ]]; then
    if [[ -f "/usr/local/bin/paka" ]]; then
        sudo rm -f /usr/local/bin/paka
        echo -e "${GREEN}✓ Removed system executable${NC}"
    fi
fi
if [[ "$rm_user_bin" =~ ^[Yy]$ ]]; then
    if [[ -f "$HOME/.local/bin/paka" ]]; then
        rm -f "$HOME/.local/bin/paka"
        echo -e "${GREEN}✓ Removed user executable${NC}"
    fi
fi
if [[ "$rm_sys_py" =~ ^[Yy]$ ]]; then
    if [[ -d "/usr/local/share/paka" ]]; then
        sudo rm -rf /usr/local/share/paka
        echo -e "${GREEN}✓ Removed system Python source${NC}"
    fi
fi
if [[ "$rm_user_py" =~ ^[Yy]$ ]]; then
    if [[ -d "$HOME/.local/share/paka" ]]; then
        rm -rf "$HOME/.local/share/paka"
        echo -e "${GREEN}✓ Removed user Python source${NC}"
    fi
fi
if [[ "$rm_sys_cfg" =~ ^[Yy]$ ]]; then
    if [[ -d "/etc/paka" ]]; then
        sudo rm -rf /etc/paka
        echo -e "${GREEN}✓ Removed system configuration${NC}"
    fi
fi
if [[ "$rm_user_cfg" =~ ^[Yy]$ ]]; then
    if [[ -d "$HOME/.config/paka" ]]; then
        rm -rf "$HOME/.config/paka"
        echo -e "${GREEN}✓ Removed user configuration${NC}"
    fi
fi
if [[ "$rm_sys_plugins" =~ ^[Yy]$ ]]; then
    if [[ -d "/usr/local/share/paka/plugins" ]]; then
        sudo rm -rf /usr/local/share/paka/plugins
        echo -e "${GREEN}✓ Removed system plugins${NC}"
    fi
fi
if [[ "$rm_user_plugins" =~ ^[Yy]$ ]]; then
    if [[ -d "$HOME/.local/share/paka/plugins" ]]; then
        rm -rf "$HOME/.local/share/paka/plugins"
        echo -e "${GREEN}✓ Removed user plugins${NC}"
    fi
fi
if [[ "$rm_user_data" =~ ^[Yy]$ ]]; then
    if [[ -d "$HOME/.local/share/paka" ]]; then
        rm -rf "$HOME/.local/share/paka"
        echo -e "${GREEN}✓ Removed user data directory${NC}"
    fi
fi
if [[ "$rm_bash_comp" =~ ^[Yy]$ ]]; then
    if [[ -f "/etc/bash_completion.d/paka.bash" ]]; then
        sudo rm -f /etc/bash_completion.d/paka.bash
        echo -e "${GREEN}✓ Removed bash completion${NC}"
    fi
fi
if [[ "$rm_zsh_comp" =~ ^[Yy]$ ]]; then
    if [[ -f "/usr/local/share/zsh/site-functions/_paka" ]]; then
        sudo rm -f /usr/local/share/zsh/site-functions/_paka
        echo -e "${GREEN}✓ Removed zsh completion${NC}"
    fi
fi
if [[ "$rm_user_logs" =~ ^[Yy]$ ]]; then
    if [[ -d "$HOME/.local/share/paka/logs" ]]; then
        rm -rf "$HOME/.local/share/paka/logs"
        echo -e "${GREEN}✓ Removed user logs${NC}"
    fi
fi

# Remove this uninstaller
echo -e "${YELLOW}Removing uninstaller...${NC}"
rm -f "$0"
echo -e "${GREEN}✓ Removed uninstaller${NC}"

echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Uninstallation Complete!                   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${GREEN}PAKA has been completely removed from your system.${NC}"
if [[ "$remove_user_data" == "true" ]]; then
    echo -e "${GREEN}All user data and configuration has been removed.${NC}"
fi
if [[ "$remove_all_data" == "true" ]]; then
    echo -e "${GREEN}All system data and configuration has been removed.${NC}"
fi

echo -e "\n${YELLOW}Note: You may need to restart your shell or run 'source ~/.bashrc'${NC}"
echo -e "${YELLOW}to remove command completion.${NC}"
EOF

    chmod +x uninstall.sh
    echo -e "${GREEN}✓ Uninstaller created${NC}"
}

# Function to show help
show_help() {
    echo -e "${BLUE}PAKA Installation Script${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -w, --wizard     Run installation wizard (default)"
    echo "  -i, --install    Perform installation using saved configuration"
    echo "  -u, --uninstall  Run uninstaller"
    echo "  -h, --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                # Run installation wizard"
    echo "  $0 --install      # Install using saved configuration"
    echo "  $0 --uninstall    # Run uninstaller"
    echo ""
}

# Main script logic
main() {
    show_banner
    
    case "${1:-wizard}" in
        -w|--wizard|wizard)
            run_installation_wizard
            echo -e "\n${GREEN}Wizard completed!${NC}"
            echo -e "${YELLOW}Run '$0 --install' to perform the installation${NC}"
            ;;
        -i|--install|install)
            perform_installation
            ;;
        -u|--uninstall|uninstall)
            if [[ -f "uninstall.sh" ]]; then
                ./uninstall.sh
            else
                echo -e "${RED}Uninstaller not found${NC}"
                echo -e "${YELLOW}Please run the installer first${NC}"
                exit 1
            fi
            ;;
        -h|--help|help)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 