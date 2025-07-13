#!/usr/bin/env python3
"""
Health UI Module

Handles the user interface for health checks and fixes.
"""

import subprocess
import logging
from typing import Dict, List, Any

from .base import HealthCheck
from ..plugin_manager import PluginEvent


class HealthUI:
    """Handles health check user interface"""
    
    def __init__(self):
        """Initialize health UI"""
        self.logger = logging.getLogger(__name__)
    
    def display_header(self, message: str):
        """Display health check header"""
        print(f"🔍 {message}")
        print()
    
    def display_section(self, message: str):
        """Display health check section"""
        print(f"📦 {message}")
    
    def interactive_health_overview(self, checks: List[HealthCheck], engine=None) -> int:
        """Show interactive health overview"""
        if not checks:
            print("✅ All health checks passed! Your system is healthy.")
            return 0
        
        # Group checks by category
        grouped_checks = self._group_checks_by_category(checks)
        
        print("📊 Health Check Overview")
        print("=" * 30)
        
        # Show summary by category
        for category, category_checks in grouped_checks.items():
            icon = self._get_category_status_icon(category_checks)
            print(f"{icon} {category}: {len(category_checks)} issues")
        
        print()
        
        # Show detailed view
        while True:
            print("Options:")
            print("1. View all issues")
            print("2. View by category")
            print("3. Fix all issues")
            print("4. Exit")
            
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == '1':
                self._show_all_issues(checks)
            elif choice == '2':
                self._show_by_category(grouped_checks, checks, engine)
            elif choice == '3':
                return self.fix_all_issues(checks, engine)
            elif choice == '4':
                return 0
            else:
                print("Invalid choice")
    
    def _show_all_issues(self, checks: List[HealthCheck]):
        """Show all health issues"""
        print("\nAll Health Issues:")
        print("=" * 20)
        
        for i, check in enumerate(checks, 1):
            status_icon = self._get_status_icon(check.status)
            print(f"{i}. {status_icon} {check.name}")
            print(f"   {check.message}")
            if check.fix_description:
                print(f"   Fix: {check.fix_description}")
            print()
    
    def _show_by_category(self, grouped_checks: Dict[str, List[HealthCheck]], all_checks: List[HealthCheck], engine=None):
        """Show issues by category"""
        print("\nCategories:")
        categories = list(grouped_checks.keys())
        for i, category in enumerate(categories, 1):
            icon = self._get_category_status_icon(grouped_checks[category])
            print(f"{i}. {icon} {category}")
        
        choice = input("Enter category number: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(categories):
                category = categories[idx]
                return self._show_category_details(category, grouped_checks[category], all_checks, engine)
            else:
                print("Invalid category number")
        except ValueError:
            print("Invalid input")
    
    def _show_category_details(self, category: str, category_checks: List[HealthCheck], all_checks: List[HealthCheck], engine=None) -> int:
        """Show details for a specific category"""
        print(f"\n{category} Issues:")
        print("=" * (len(category) + 8))
        
        for i, check in enumerate(category_checks, 1):
            status_icon = self._get_status_icon(check.status)
            print(f"{i}. {status_icon} {check.name}")
            print(f"   {check.message}")
            if check.fix_description:
                print(f"   Fix: {check.fix_description}")
            print()
        
        print("Options:")
        print("1. Fix all issues in this category")
        print("2. Fix individual issues")
        print("3. Back to categories")
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            return self._fix_category_issues(category_checks, engine)
        elif choice == '2':
            return self._fix_individual_issues(category_checks, engine)
        elif choice == '3':
            return 0
        else:
            print("Invalid choice")
            return 0
    
    def _fix_category_issues(self, checks: List[HealthCheck], engine=None) -> int:
        """Fix all issues in a category"""
        # Trigger pre-health event before applying fixes
        if engine:
            health_context = {
                'checks': checks,
                'fix_count': len([c for c in checks if c.fix_command]),
                'options': {}
            }
            engine._trigger_plugin_event(PluginEvent.PRE_HEALTH, health_context)
        
        print(f"Fixing {len(checks)} issues...")
        
        success_count = 0
        for check in checks:
            if self._fix_single_issue(check):
                success_count += 1
        
        print(f"Fixed {success_count}/{len(checks)} issues")
        return 0
    
    def _fix_individual_issues(self, checks: List[HealthCheck], engine=None) -> int:
        """Fix individual issues"""
        print("\nSelect issues to fix:")
        for i, check in enumerate(checks, 1):
            status_icon = self._get_status_icon(check.status)
            print(f"{i}. {status_icon} {check.name}")
        
        choice = input("Enter issue number (or 'all'): ").strip()
        
        if choice.lower() == 'all':
            return self._fix_category_issues(checks, engine)
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(checks):
                check = checks[idx]
                if self._fix_single_issue(check):
                    print("Issue fixed successfully")
                else:
                    print("Failed to fix issue")
            else:
                print("Invalid issue number")
        except ValueError:
            print("Invalid input")
        
        return 0
    
    def _fix_single_issue(self, check: HealthCheck) -> bool:
        """Fix a single health issue"""
        if not check.fix_command:
            print(f"No fix available for: {check.name}")
            return False
        
        print(f"Fixing: {check.name}")
        print(f"Command: {check.fix_command}")
        
        confirm = input("Proceed? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Skipped")
            return False
        
        try:
            result = subprocess.run(check.fix_command.split(), 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print("✅ Fixed successfully")
                return True
            else:
                print(f"❌ Fix failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Fix timed out")
            return False
        except Exception as e:
            print(f"❌ Fix error: {e}")
            return False
    
    def fix_all_issues(self, checks: List[HealthCheck], engine=None) -> int:
        """Fix all health issues automatically"""
        # Trigger pre-health event before applying fixes
        if engine:
            health_context = {
                'checks': checks,
                'fix_count': len([c for c in checks if c.fix_command]),
                'options': {}
            }
            engine._trigger_plugin_event(PluginEvent.PRE_HEALTH, health_context)
        
        print("🔧 Fixing all health issues...")
        print()
        
        success_count = 0
        total_count = len(checks)
        
        for check in checks:
            if not check.fix_command:
                print(f"⚠️  No fix available for: {check.name}")
                continue
            
            print(f"Fixing: {check.name}")
            try:
                result = subprocess.run(check.fix_command.split(), 
                                      capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    print(f"✅ {check.name} - Fixed")
                    success_count += 1
                else:
                    print(f"❌ {check.name} - Failed: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print(f"❌ {check.name} - Timed out")
            except Exception as e:
                print(f"❌ {check.name} - Error: {e}")
        
        print()
        print(f"📊 Results: {success_count}/{total_count} issues fixed")
        
        if success_count == total_count:
            print("🎉 All issues fixed successfully!")
        elif success_count > 0:
            print("⚠️  Some issues were fixed, but some failed")
        else:
            print("❌ No issues were fixed")
        
        return 0
    
    def _group_checks_by_category(self, checks: List[HealthCheck]) -> Dict[str, List[HealthCheck]]:
        """Group health checks by category"""
        grouped = {}
        for check in checks:
            category = self._get_check_category(check)
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(check)
        return grouped
    
    def _get_check_category(self, check: HealthCheck) -> str:
        """Get category for a health check"""
        name = check.name.lower()
        
        if 'cache' in name:
            return 'Package Caches'
        elif 'lock' in name or 'partial' in name:
            return 'System Locks'
        elif 'broken' in name or 'corrupted' in name:
            return 'Package Manager Issues'
        elif 'repository' in name or 'repo' in name:
            return 'Repository Issues'
        elif 'disk' in name or 'bloat' in name:
            return 'Disk Usage'
        elif 'orphaned' in name or 'purge' in name:
            return 'Package Cleanup'
        else:
            return 'Other Issues'
    
    def _get_category_status_icon(self, checks: List[HealthCheck]) -> str:
        """Get status icon for a category"""
        if any(check.status == 'error' for check in checks):
            return '🔴'
        elif any(check.status == 'warning' for check in checks):
            return '🟡'
        else:
            return '🟢'
    
    def _get_status_icon(self, status: str) -> str:
        """Get status icon for a check"""
        if status == 'error':
            return '🔴'
        elif status == 'warning':
            return '🟡'
        else:
            return '🟢' 