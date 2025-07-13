#!/usr/bin/env python3
"""
Enhanced AppImage Package Manager

Supports multiple sources with trust levels and user configuration.
"""

import os
import re
import json
import logging
import requests
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import sqlite3
from urllib.parse import urljoin, urlparse

from ..package_managers.base import BasePackageManager, PackageResult


class AppImageSource:
    """Represents an AppImage source with trust level"""
    
    def __init__(self, name: str, url: str, trust_level: str, description: str):
        self.name = name
        self.url = url
        self.trust_level = trust_level
        self.description = description


class AppImagePackageManager(BasePackageManager):
    """Enhanced AppImage package manager with multiple sources and trust levels"""
    
    # Trust level definitions
    TRUST_LEVELS = {
        'official': {
            'level': 1,
            'icon': '🟢',
            'description': 'Official source from application developers',
            'color': 'green'
        },
        'verified_community': {
            'level': 2,
            'icon': '🟡',
            'description': 'Verified community builds from trusted sources',
            'color': 'yellow'
        },
        'unofficial': {
            'level': 3,
            'icon': '🔴',
            'description': 'Unofficial builds, use with caution',
            'color': 'red'
        }
    }
    
    # Predefined sources with trust levels
    SOURCES = {
        # Official sources (from application developers)
        'krita': AppImageSource('Krita Official', 'https://krita.org/en/download/krita-desktop/', 'official', 'Official Krita AppImage'),
        'kdenlive': AppImageSource('Kdenlive Official', 'https://kdenlive.org/en/download/', 'official', 'Official Kdenlive AppImage'),
        'digikam': AppImageSource('digiKam Official', 'https://www.digikam.org/download/', 'official', 'Official digiKam AppImage'),
        'openshot': AppImageSource('OpenShot Official', 'https://www.openshot.org/download/', 'official', 'Official OpenShot AppImage'),
        'shotcut': AppImageSource('Shotcut Official', 'https://shotcut.org/download/', 'official', 'Official Shotcut AppImage'),
        'lmms': AppImageSource('LMMS Official', 'https://github.com/LMMS/lmms/releases', 'official', 'Official LMMS AppImage'),
        'musescore': AppImageSource('MuseScore Official', 'https://musescore.org/en/download', 'official', 'Official MuseScore AppImage'),
        'onlyoffice': AppImageSource('OnlyOffice Official', 'https://www.onlyoffice.com/download-desktop.aspx', 'official', 'Official OnlyOffice AppImage'),
        'joplin': AppImageSource('Joplin Official', 'https://joplinapp.org/desktop/', 'official', 'Official Joplin AppImage'),
        'obsidian': AppImageSource('Obsidian Official', 'https://obsidian.md/download', 'official', 'Official Obsidian AppImage'),
        'nextcloud': AppImageSource('Nextcloud Official', 'https://nextcloud.com/install/#install-clients', 'official', 'Official Nextcloud AppImage'),
        'librewolf': AppImageSource('LibreWolf Official', 'https://librewolf.net/installation/linux/', 'official', 'Official LibreWolf AppImage'),
        'balena_etcher': AppImageSource('Balena Etcher Official', 'https://etcher.balena.io/#download-etcher', 'official', 'Official Balena Etcher AppImage'),
        'cursor': AppImageSource('Cursor AI Official', 'https://cursor.sh/download', 'official', 'Official Cursor AI AppImage'),
        
        # Verified community sources
        'appimagehub': AppImageSource('AppImageHub', 'https://appimagehub.github.io', 'verified_community', 'Official Community Catalog'),
        'appimage_official': AppImageSource('AppImage Official', 'https://appimage.github.io/apps/', 'verified_community', 'AppImage Official Repository'),
        'portablelinuxapps': AppImageSource('Portable Linux Apps', 'https://portablelinuxapps.org/', 'verified_community', 'Community-Driven Catalog'),
        'getappimage': AppImageSource('GetAppImage', 'https://getappimage.org/', 'verified_community', 'All-in-One AppImage Search'),
        
        # Community builds (mixed trust)
        'inkscape': AppImageSource('Inkscape Community', 'https://inkscape.org/release/', 'verified_community', 'Community AppImage Builds'),
        'blender': AppImageSource('Blender Community', 'https://www.blender.org/download/', 'verified_community', 'Community AppImage Builds'),
        'audacity': AppImageSource('Audacity Community', 'https://github.com/audacity/audacity/releases', 'verified_community', 'Community AppImage Builds'),
        
        # Tools and utilities
        'appimagelauncher': AppImageSource('AppImageLauncher', 'https://github.com/TheAssassin/AppImageLauncher/releases', 'verified_community', 'AppImage Integration Tool'),
        'appimageupdate': AppImageSource('AppImageUpdate', 'https://github.com/AppImage/AppImageUpdate/releases', 'verified_community', 'Delta Updater for AppImages'),
    }
    
    def __init__(self, name: str = 'appimage', config: Optional[Dict[str, Any]] = None):
        """Initialize the enhanced AppImage manager"""
        super().__init__(name, config or {})
        
        # Load configuration
        self.config = config or {}
        self.trust_settings = self.config.get('trust_settings', {
            'allow_unofficial_builds': False,
            'allow_community_builds': True,
            'prefer_official_sources': True,
            'enabled_trust_levels': ['official', 'verified_community'],
            'include_sources': [],
            'exclude_sources': []
        })
        
        # Initialize database
        self.db_path = Path.home() / '.local' / 'share' / 'paka' / 'appimages.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        self.logger = logging.getLogger(__name__)
    
    def _init_database(self):
        """Initialize the AppImage database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS appimages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    version TEXT,
                    source_name TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    trust_level TEXT NOT NULL,
                    download_url TEXT NOT NULL,
                    file_size INTEGER,
                    description TEXT,
                    installed_path TEXT,
                    installed_date TEXT,
                    last_updated TEXT,
                    UNIQUE(name, version, source_name)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    trust_level TEXT NOT NULL,
                    description TEXT,
                    last_checked TEXT,
                    enabled BOOLEAN DEFAULT 1
                )
            ''')
            
            # Insert default sources
            for source_id, source in self.SOURCES.items():
                conn.execute('''
                    INSERT OR IGNORE INTO sources (name, url, trust_level, description)
                    VALUES (?, ?, ?, ?)
                ''', (source.name, source.url, source.trust_level, source.description))
            
            conn.commit()
    
    def search(self, query: str, options: Optional[Dict[str, Any]] = None) -> PackageResult:
        """Search for AppImages across multiple sources with trust filtering"""
        options = options or {}
        
        # Get trust level filter from options
        trust_levels = options.get('trust_levels', self.trust_settings['enabled_trust_levels'])
        include_unofficial = options.get('include_unofficial', self.trust_settings['allow_unofficial_builds'])
        
        # Update trust levels based on user preferences
        if not include_unofficial and 'unofficial' in trust_levels:
            trust_levels.remove('unofficial')
        
        self.logger.info(f"Searching for '{query}' with trust levels: {trust_levels}")
        
        # Search database for matching AppImages
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT name, version, source_name, source_url, trust_level, 
                       download_url, file_size, description, installed_path
                FROM appimages 
                WHERE name LIKE ? AND trust_level IN ({})
                ORDER BY 
                    CASE trust_level 
                        WHEN 'official' THEN 1 
                        WHEN 'verified_community' THEN 2 
                        WHEN 'unofficial' THEN 3 
                    END,
                    version DESC
            '''.format(','.join('?' * len(trust_levels))), 
            [f'%{query}%'] + trust_levels)
            
            results = []
            for row in cursor.fetchall():
                name, version, source_name, source_url, trust_level, download_url, file_size, description, installed_path = row
                
                # Get trust level info
                trust_info = self.TRUST_LEVELS.get(trust_level, {})
                
                results.append({
                    'name': name,
                    'version': version,
                    'source_name': source_name,
                    'source_url': source_url,
                    'trust_level': trust_level,
                    'trust_icon': trust_info.get('icon', '❓'),
                    'trust_description': trust_info.get('description', 'Unknown trust level'),
                    'download_url': download_url,
                    'file_size': file_size,
                    'description': description,
                    'installed': bool(installed_path),
                    'installed_path': installed_path,
                    'manager': 'appimage'
                })
        
        # Group by name and version to show multiple sources
        grouped_results = self._group_results_by_package(results)
        
        return PackageResult(
            success=True,
            packages=grouped_results,
            details={
                'query': query,
                'trust_levels_used': trust_levels,
                'total_found': len(grouped_results)
            }
        )
    
    def _group_results_by_package(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group results by package name and version, showing multiple sources"""
        grouped = {}
        
        for result in results:
            key = f"{result['name']}-{result['version']}"
            
            if key not in grouped:
                grouped[key] = {
                    'name': result['name'],
                    'version': result['version'],
                    'description': result['description'],
                    'sources': [],
                    'best_source': None,
                    'installed': result['installed'],
                    'installed_path': result['installed_path'],
                    'manager': 'appimage'
                }
            
            # Add this source to the package
            source_info = {
                'source_name': result['source_name'],
                'source_url': result['source_url'],
                'trust_level': result['trust_level'],
                'trust_icon': result['trust_icon'],
                'trust_description': result['trust_description'],
                'download_url': result['download_url'],
                'file_size': result['file_size']
            }
            
            grouped[key]['sources'].append(source_info)
            
            # Determine best source (lowest trust level number = best)
            if (grouped[key]['best_source'] is None or 
                self.TRUST_LEVELS[source_info['trust_level']]['level'] < 
                self.TRUST_LEVELS[grouped[key]['best_source']['trust_level']]['level']):
                grouped[key]['best_source'] = source_info
        
        return list(grouped.values())
    
    def install(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> PackageResult:
        """Install AppImages with source selection"""
        options = options or {}
        installed_packages = []
        errors = []
        
        for package_name in packages:
            # Search for the package
            search_result = self.search(package_name, options)
            if not search_result.success or not search_result.packages:
                self.logger.error(f"No AppImage found for '{package_name}'")
                errors.append(f"No AppImage found for '{package_name}'")
                continue
            package_info = search_result.packages[0]  # Get first match
            # If multiple sources, let user choose
            if len(package_info['sources']) > 1:
                source_choice = self._select_source(package_info)
                if not source_choice:
                    errors.append(f"No source selected for '{package_name}'")
                    continue
                selected_source = source_choice
            else:
                selected_source = package_info['sources'][0]
            # Install the selected AppImage
            success = self._install_appimage(package_info, selected_source)
            if success:
                self.logger.info(f"Successfully installed {package_name} from {selected_source['source_name']}")
                installed_packages.append(package_info)
            else:
                self.logger.error(f"Failed to install {package_name}")
                errors.append(f"Failed to install {package_name}")
        return PackageResult(success=(len(errors) == 0), packages=installed_packages, error='; '.join(errors) if errors else None)
    
    def _select_source(self, package_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Let user select which source to use for installation"""
        print(f"\nMultiple sources found for {package_info['name']} {package_info['version']}:")
        print("=" * 60)
        
        for i, source in enumerate(package_info['sources'], 1):
            size_mb = source['file_size'] / (1024 * 1024) if source['file_size'] else 'Unknown'
            print(f"{i}. {source['trust_icon']} {source['source_name']}")
            print(f"   Trust: {source['trust_description']}")
            print(f"   Size: {size_mb:.1f} MB" if isinstance(size_mb, float) else f"   Size: {size_mb}")
            print(f"   URL: {source['source_url']}")
            print()
        
        try:
            choice = int(input("Select source (1-{}): ".format(len(package_info['sources']))))
            if 1 <= choice <= len(package_info['sources']):
                return package_info['sources'][choice - 1]
        except (ValueError, KeyboardInterrupt):
            pass
        
        return None
    
    def _install_appimage(self, package_info: Dict[str, Any], source: Dict[str, Any]) -> bool:
        """Install a specific AppImage"""
        try:
            # Download the AppImage
            download_path = self._download_appimage(source['download_url'], package_info['name'])
            
            if not download_path:
                return False
            
            # Make it executable
            os.chmod(download_path, 0o755)
            
            # Create desktop entry
            self._create_desktop_entry(package_info, source, download_path)
            
            # Record installation in database
            self._record_installation(package_info, source, download_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing AppImage: {e}")
            return False
    
    def _download_appimage(self, url: str, name: str) -> Optional[Path]:
        """Download an AppImage file"""
        try:
            # Create download directory
            download_dir = Path.home() / '.local' / 'bin'
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Download file
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Determine filename
            if 'content-disposition' in response.headers:
                filename = response.headers['content-disposition'].split('filename=')[-1].strip('"')
            else:
                filename = f"{name}.AppImage"
            
            file_path = download_dir / filename
            
            # Download with progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rDownloading: {percent:.1f}%", end='', flush=True)
            
            print()  # New line after progress
            return file_path
            
        except Exception as e:
            self.logger.error(f"Error downloading AppImage: {e}")
            return None
    
    def _create_desktop_entry(self, package_info: Dict[str, Any], source: Dict[str, Any], appimage_path: Path):
        """Create a desktop entry for the AppImage"""
        desktop_dir = Path.home() / '.local' / 'share' / 'applications'
        desktop_dir.mkdir(parents=True, exist_ok=True)
        
        desktop_entry = f"""[Desktop Entry]
Name={package_info['name']}
Comment={package_info.get('description', 'AppImage application')}
Exec={appimage_path}
Icon={appimage_path}
Terminal=false
Type=Application
Categories=Utility;
Comment[en]={package_info.get('description', 'AppImage application')}
"""
        
        desktop_file = desktop_dir / f"{package_info['name'].lower()}.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_entry)
    
    def _record_installation(self, package_info: Dict[str, Any], source: Dict[str, Any], appimage_path: Path):
        """Record the installation in the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO appimages 
                (name, version, source_name, source_url, trust_level, download_url, 
                 file_size, description, installed_path, installed_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                package_info['name'],
                package_info['version'],
                source['source_name'],
                source['source_url'],
                source['trust_level'],
                source['download_url'],
                source['file_size'],
                package_info['description'],
                str(appimage_path),
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def remove_appimage(self, appimage_path: Path, package_name: str, source_name: str) -> bool:
        """Remove a specific AppImage"""
        try:
            # Remove the AppImage file
            if appimage_path.exists():
                appimage_path.unlink()
            # Remove desktop entry
            desktop_file = Path.home() / '.local' / 'share' / 'applications' / f"{package_name.lower()}.desktop"
            if desktop_file.exists():
                desktop_file.unlink()
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE appimages 
                    SET installed_path = NULL, installed_date = NULL
                    WHERE name = ? AND source_name = ?
                ''', (package_name, source_name))
                conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error removing AppImage: {e}")
            return False

    def remove(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> PackageResult:
        """Remove installed AppImages"""
        options = options or {}
        removed_packages = []
        errors = []
        for package_name in packages:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT installed_path, source_name FROM appimages 
                    WHERE name LIKE ? AND installed_path IS NOT NULL
                ''', [f'%{package_name}%'])
                installed = cursor.fetchall()
                if not installed:
                    self.logger.warning(f"No installed AppImage found for '{package_name}'")
                    errors.append(f"No installed AppImage found for '{package_name}'")
                    continue
                for appimage_path, source_name in installed:
                    success = self.remove_appimage(Path(appimage_path), package_name, source_name)
                    if success:
                        self.logger.info(f"Successfully removed {package_name} from {source_name}")
                        removed_packages.append(package_name)
                    else:
                        self.logger.error(f"Failed to remove {package_name}")
                        errors.append(f"Failed to remove {package_name}")
        return PackageResult(success=(len(errors) == 0), packages=removed_packages, error='; '.join(errors) if errors else None)

    def purge(self, packages: List[str], options: Optional[Dict[str, Any]] = None) -> PackageResult:
        """Purge AppImages (alias for remove)"""
        return self.remove(packages, options)

    def update(self, options: Optional[Dict[str, Any]] = None) -> PackageResult:
        """Update AppImage sources and package information"""
        try:
            updated = self.update_sources(options)
            return PackageResult(success=updated, details={"updated": updated})
        except Exception as e:
            self.logger.error(f"Failed to update AppImage sources: {e}")
            return PackageResult(success=False, error=str(e))

    def list_installed(self, options: Optional[Dict[str, Any]] = None) -> List[str]:
        """List installed AppImage package names"""
        installed = self.get_installed_packages()
        return [pkg['name'] for pkg in installed]

    def is_enabled(self) -> bool:
        return super().is_enabled()

    def is_available(self) -> bool:
        return super().is_available()

    def update_sources(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Update AppImage sources and refresh the database"""
        self.logger.info("Updating AppImage sources...")
        
        # This would involve scraping the various sources
        # For now, we'll just mark sources as updated
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE sources 
                SET last_checked = ?
                WHERE enabled = 1
            ''', (datetime.now().isoformat(),))
            conn.commit()
        
        self.logger.info("AppImage sources updated")
        return True
    
    def get_installed_packages(self) -> List[Dict[str, Any]]:
        """Get list of installed AppImages"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT name, version, source_name, trust_level, installed_path, installed_date
                FROM appimages 
                WHERE installed_path IS NOT NULL
                ORDER BY name
            ''')
            
            return [
                {
                    'name': row[0],
                    'version': row[1],
                    'source_name': row[2],
                    'trust_level': row[3],
                    'installed_path': row[4],
                    'installed_date': row[5]
                }
                for row in cursor.fetchall()
            ]
    
    def initialize(self) -> bool:
        """Initialize the AppImage manager"""
        try:
            self._init_database()
            self.logger.info("AppImage manager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize AppImage manager: {e}")
            return False
    
    def cleanup(self):
        """Cleanup AppImage manager resources"""
        try:
            # Close any open database connections
            pass
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def upgrade(self, options: Optional[Dict[str, Any]] = None) -> bool:
        """Upgrade installed AppImages to newer versions"""
        try:
            # Get installed packages
            installed = self.get_installed_packages()
            if not installed:
                self.logger.info("No AppImages installed to upgrade")
                return True
            # Check for updates for each installed package
            updated_count = 0
            for pkg in installed:
                # Search for newer versions
                search_results = self.search(pkg['name'], options)
                if search_results.packages:
                    # Find the latest version
                    latest = max(search_results.packages, key=lambda x: x.get('version', '0.0.0'))
                    if latest.get('version', '0.0.0') > pkg.get('version', '0.0.0'):
                        # Install the newer version
                        install_result = self.install([pkg['name']], options)
                        if install_result.success:
                            updated_count += 1
            self.logger.info(f"Upgraded {updated_count} AppImages")
            return True
        except Exception as e:
            self.logger.error(f"Failed to upgrade AppImages: {e}")
            return False 