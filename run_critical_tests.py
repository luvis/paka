#!/usr/bin/env python3
"""
PAKA Critical Tests Runner

Runs only the most essential tests to verify core functionality without memory issues.
"""

import sys
import os
import subprocess
import psutil
import gc
import time
import resource
from pathlib import Path

# Ultra-conservative memory limits
MAX_MEMORY_USAGE = 1000  # 1GB limit
PROCESS_TIMEOUT = 60  # 1 minute timeout per test

def set_memory_limit():
    """Set hard memory limit for the process"""
    try:
        resource.setrlimit(resource.RLIMIT_AS, (1 * 1024 * 1024 * 1024, -1))
        print("📊 Set hard memory limit to 1GB")
    except Exception as e:
        print(f"⚠️  Could not set memory limit: {e}")

def get_memory_usage() -> float:
    """Get current memory usage in MB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def force_garbage_collection():
    """Force aggressive garbage collection"""
    gc.collect()
    gc.collect()
    time.sleep(0.5)

def run_critical_test(test_file: str, description: str) -> bool:
    """Run a single critical test"""
    print(f"\n🧪 Running critical test: {description}")
    print("=" * 50)
    
    start_memory = get_memory_usage()
    print(f"📊 Memory before: {start_memory:.1f}MB")
    
    try:
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        
        result = subprocess.run(
            [sys.executable, test_file], 
            capture_output=False, 
            text=True, 
            timeout=PROCESS_TIMEOUT,
            env=env
        )
        
        end_memory = get_memory_usage()
        print(f"📊 Memory after: {end_memory:.1f}MB (used: {end_memory - start_memory:.1f}MB)")
        
        force_garbage_collection()
        time.sleep(2)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"❌ {description} timed out")
        return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    """Run only critical tests"""
    print("🧪 PAKA Critical Tests Runner")
    print("=" * 50)
    print(f"📊 Memory limit: {MAX_MEMORY_USAGE}MB")
    print(f"⏱️  Timeout: {PROCESS_TIMEOUT} seconds")
    
    set_memory_limit()
    
    initial_memory = get_memory_usage()
    print(f"📊 Initial memory: {initial_memory:.1f}MB")
    
    # Only run the most critical tests
    critical_tests = [
        ('test_plugins.py', 'Plugin System Test'),
        ('test_suite.py', 'Comprehensive Test Suite'),
    ]
    
    results = {}
    
    for test_file, description in critical_tests:
        if not Path(test_file).exists():
            print(f"❌ Test file not found: {test_file}")
            continue
            
        if get_memory_usage() > MAX_MEMORY_USAGE:
            print("🚨 Memory limit reached, stopping")
            break
            
        success = run_critical_test(test_file, description)
        results[description] = success
        
        if not success:
            print(f"❌ Critical test failed: {description}")
            break
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 CRITICAL TEST RESULTS")
    print("=" * 50)
    
    final_memory = get_memory_usage()
    print(f"📊 Final memory: {final_memory:.1f}MB")
    
    all_passed = True
    for description, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {description}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All critical tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Critical tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main() 