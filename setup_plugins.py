#!/usr/bin/env python3
"""
PAKA Plugin Setup Script

Copies plugins from the codebase to the correct XDG-compliant directories
for testing and development purposes.
"""

import sys
import os
import shutil
from pathlib import Path
from typing import Dict, List

def get_plugin_directories() -> Dict[str, Path]:
    """Get the correct plugin directories according to XDG standards"""
    home = Path.home()
    
    # User plugins directory
    xdg_data_home = os.getenv('XDG_DATA_HOME')
    if xdg_data_home:
        user_plugins_dir = Path(xdg_data_home) / 'paka' / 'plugins'
    else:
        user_plugins_dir = home / '.local' / 'share' / 'paka' / 'plugins'
    
    # System plugins directory
    system_plugins_dir = Path('/usr/share/paka/plugins')
    
    return {
        'user': user_plugins_dir,
        'system': system_plugins_dir
    }

def copy_plugin(plugin_path: Path, target_dir: Path, plugin_name: str) -> bool:
    """Copy a plugin to the target directory"""
    try:
        target_plugin_dir = target_dir / plugin_name
        
        # Remove existing plugin if it exists
        if target_plugin_dir.exists():
            shutil.rmtree(target_plugin_dir)
        
        # Copy plugin directory
        shutil.copytree(plugin_path, target_plugin_dir)
        
        print(f"✅ Copied {plugin_name} to {target_plugin_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to copy {plugin_name}: {e}")
        return False

def setup_plugins():
    """Set up plugins in the correct directories"""
    print("🔧 Setting up PAKA plugins...")
    print("=" * 50)
    
    # Get plugin directories
    plugin_dirs = get_plugin_directories()
    user_plugins_dir = plugin_dirs['user']
    system_plugins_dir = plugin_dirs['system']
    
    # Create directories if they don't exist
    user_plugins_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if we can write to system plugins directory
    can_write_system = False
    if system_plugins_dir.exists():
        can_write_system = os.access(system_plugins_dir, os.W_OK)
    else:
        can_write_system = os.access(system_plugins_dir.parent, os.W_OK)
    
    if not can_write_system:
        print(f"⚠️  Cannot write to system plugins directory: {system_plugins_dir}")
        print("   System plugins will be copied to user directory instead")
        system_plugins_dir = user_plugins_dir / 'system'
        system_plugins_dir.mkdir(parents=True, exist_ok=True)
    
    # Get current working directory
    current_dir = Path.cwd()
    codebase_plugins_dir = current_dir / 'plugins'
    
    if not codebase_plugins_dir.exists():
        print(f"❌ Plugins directory not found: {codebase_plugins_dir}")
        return False
    
    print(f"📁 Source plugins directory: {codebase_plugins_dir}")
    print(f"📁 User plugins directory: {user_plugins_dir}")
    print(f"📁 System plugins directory: {system_plugins_dir}")
    print()
    
    # Copy system plugins (paka directory)
    paka_plugins_dir = codebase_plugins_dir / 'paka'
    if paka_plugins_dir.exists():
        print("📦 Copying system plugins...")
        success_count = 0
        total_count = 0
        
        for plugin_dir in paka_plugins_dir.iterdir():
            if plugin_dir.is_dir():
                total_count += 1
                if copy_plugin(plugin_dir, system_plugins_dir, plugin_dir.name):
                    success_count += 1
        
        print(f"✅ Copied {success_count}/{total_count} system plugins")
    else:
        print("⚠️  No system plugins found")
    
    # Copy user plugins (user directory)
    user_plugins_source_dir = codebase_plugins_dir / 'user'
    if user_plugins_source_dir.exists():
        print("\n📦 Copying user plugins...")
        success_count = 0
        total_count = 0
        
        for plugin_dir in user_plugins_source_dir.iterdir():
            if plugin_dir.is_dir():
                total_count += 1
                if copy_plugin(plugin_dir, user_plugins_dir, plugin_dir.name):
                    success_count += 1
        
        print(f"✅ Copied {success_count}/{total_count} user plugins")
    else:
        print("⚠️  No user plugins found")
    
    print("\n" + "=" * 50)
    print("🎉 Plugin setup completed!")
    print("\nPlugin locations:")
    print(f"  User plugins: {user_plugins_dir}")
    print(f"  System plugins: {system_plugins_dir}")
    print("\nYou can now run PAKA and it will find the plugins in the correct locations.")
    
    return True

def main():
    """Main function"""
    try:
        success = setup_plugins()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Plugin setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during plugin setup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 