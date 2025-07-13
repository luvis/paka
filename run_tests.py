#!/usr/bin/env python3
"""
PAKA Ultra Memory-Optimized Test Runner

Runs comprehensive, interactive, and dry-run test suites to validate PAKA functionality
with extremely aggressive memory usage limits and monitoring to prevent system crashes.
"""

import sys
import os
import subprocess
import psutil
import gc
import time
import signal
import resource
from pathlib import Path
from typing import Dict, List, Tuple

# Ultra-conservative memory limits (in MB)
MAX_MEMORY_USAGE = 2000  # 2GB limit (much lower)
MEMORY_CHECK_INTERVAL = 2  # Check memory every 2 seconds
BATCH_SIZE = 1  # Run tests one at a time
PROCESS_TIMEOUT = 120  # 2 minute timeout per test
MEMORY_WARNING_THRESHOLD = 1500  # Warn at 1.5GB

def set_memory_limit():
    """Set hard memory limit for the process"""
    try:
        # Set memory limit to 2GB (in bytes)
        resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, -1))
        print("📊 Set hard memory limit to 2GB")
    except Exception as e:
        print(f"⚠️  Could not set memory limit: {e}")

def get_memory_usage() -> float:
    """Get current memory usage in MB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def check_memory_limit() -> bool:
    """Check if memory usage is within limits"""
    memory_usage = get_memory_usage()
    if memory_usage > MAX_MEMORY_USAGE:
        print(f"🚨 Memory usage ({memory_usage:.1f}MB) exceeds limit ({MAX_MEMORY_USAGE}MB)")
        return False
    elif memory_usage > MEMORY_WARNING_THRESHOLD:
        print(f"⚠️  Memory usage ({memory_usage:.1f}MB) approaching limit")
    return True

def force_garbage_collection():
    """Force aggressive garbage collection to free memory"""
    gc.collect()
    gc.collect()  # Run twice for better cleanup
    time.sleep(0.2)  # Longer delay to allow memory cleanup

def run_single_test_memory_safe(test_file: str, description: str) -> Tuple[bool, float]:
    """Run a single test with extreme memory monitoring"""
    print(f"\n🚀 Running {description}")
    print("=" * 60)
    
    start_memory = get_memory_usage()
    print(f"📊 Starting memory usage: {start_memory:.1f}MB")
    
    try:
        # Set memory limit for subprocess
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['PYTHONDONTWRITEBYTECODE'] = '1'  # Don't create .pyc files
        
        # Run with strict memory monitoring and shorter timeout
        result = subprocess.run(
            [sys.executable, test_file], 
            capture_output=False, 
            text=True, 
            timeout=PROCESS_TIMEOUT,  # 2 minute timeout
            env=env
        )
        
        end_memory = get_memory_usage()
        memory_used = end_memory - start_memory
        
        print(f"📊 Final memory usage: {end_memory:.1f}MB (used: {memory_used:.1f}MB)")
        
        # Force cleanup
        force_garbage_collection()
        
        return result.returncode == 0, memory_used
        
    except subprocess.TimeoutExpired:
        print(f"❌ {description} timed out after {PROCESS_TIMEOUT} seconds")
        return False, 0
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False, 0

def run_test_batch(test_batch: List[Tuple[str, str]], batch_num: int) -> Dict[str, bool]:
    """Run a batch of tests with extreme memory monitoring"""
    print(f"\n📦 Running Test Batch {batch_num}")
    print("=" * 60)
    
    results = {}
    total_memory_used = 0
    
    for test_file, description in test_batch:
        # Check memory before each test
        if not check_memory_limit():
            print(f"🚨 Skipping {description} due to memory constraints")
            results[description] = False
            continue
        
        success, memory_used = run_single_test_memory_safe(test_file, description)
        results[description] = success
        total_memory_used += memory_used
        
        # Force cleanup between tests
        force_garbage_collection()
        
        # Longer delay to allow system to stabilize
        time.sleep(3)
        
        # Check memory again after test
        current_memory = get_memory_usage()
        if current_memory > MEMORY_WARNING_THRESHOLD:
            print(f"⚠️  High memory usage after test: {current_memory:.1f}MB")
            force_garbage_collection()
    
    print(f"📊 Batch {batch_num} completed. Total memory used: {total_memory_used:.1f}MB")
    return results

def setup_plugins():
    """Set up plugins for testing"""
    print("🔧 Setting up plugins for testing...")
    try:
        result = subprocess.run([sys.executable, 'setup_plugins.py'], 
                              capture_output=True, 
                              text=True, 
                              timeout=30)  # Shorter timeout
        if result.returncode == 0:
            print("✅ Plugins set up successfully")
            return True
        else:
            print(f"⚠️  Plugin setup had issues: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️  Could not set up plugins: {e}")
        return False

def main():
    """Main ultra memory-optimized test runner"""
    print("🧪 PAKA Ultra Memory-Optimized Test Suite Runner")
    print("=" * 60)
    print(f"📊 Memory limit: {MAX_MEMORY_USAGE}MB (ultra-conservative)")
    print(f"📦 Batch size: {BATCH_SIZE} test per batch")
    print(f"⏱️  Memory check interval: {MEMORY_CHECK_INTERVAL} seconds")
    print(f"⏱️  Process timeout: {PROCESS_TIMEOUT} seconds")
    
    # Set memory limit for this process
    set_memory_limit()
    
    # Check initial memory
    initial_memory = get_memory_usage()
    print(f"📊 Initial system memory usage: {initial_memory:.1f}MB")
    
    # Set up plugins first
    setup_plugins()
    
    # Check if test files exist
    test_files = {
        'test_suite.py': 'Comprehensive Test Suite',
        'test_interactive.py': 'Interactive Features Test Suite',
        'test_dry_run.py': 'Dry-Run Command Test Suite',
        'test_plugins.py': 'Plugin System Test Suite'
    }
    
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print(f"❌ Missing test files: {', '.join(missing_files)}")
        print("Please ensure all test files are present.")
        sys.exit(1)
    
    # Split tests into single-test batches
    test_items = list(test_files.items())
    test_batches = [test_items[i:i + BATCH_SIZE] for i in range(0, len(test_items), BATCH_SIZE)]
    
    print(f"\n📦 Split {len(test_items)} tests into {len(test_batches)} batches")
    
    # Run test batches
    all_results = {}
    batch_num = 1
    
    for batch in test_batches:
        batch_results = run_test_batch(batch, batch_num)
        all_results.update(batch_results)
        
        # Check memory after each batch
        current_memory = get_memory_usage()
        print(f"📊 Memory after batch {batch_num}: {current_memory:.1f}MB")
        
        if not check_memory_limit():
            print("🚨 Memory limit reached, stopping test execution")
            break
        
        batch_num += 1
        
        # Much longer delay between batches
        time.sleep(5)
        
        # Force cleanup between batches
        force_garbage_collection()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    final_memory = get_memory_usage()
    total_memory_used = final_memory - initial_memory
    
    print(f"📊 Total memory used: {total_memory_used:.1f}MB")
    print(f"📊 Final memory usage: {final_memory:.1f}MB")
    
    all_passed = True
    for description, success in all_results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {description}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TEST SUITES PASSED!")
        print("PAKA is ready for release.")
        sys.exit(0)
    else:
        print("⚠️  SOME TEST SUITES FAILED!")
        print("Please review and fix the issues before release.")
        sys.exit(1)

if __name__ == '__main__':
    main() 