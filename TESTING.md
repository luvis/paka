# PAKA Testing Guide

This document describes the comprehensive testing framework for PAKA, including how to run tests and what each test suite covers.

## Test Suites Overview

PAKA includes four comprehensive test suites that validate different aspects of the system:

1. **Comprehensive Test Suite** (`test_suite.py`) - Core functionality and API testing
2. **Interactive Test Suite** (`test_interactive.py`) - Menu system and UI testing
3. **Dry-Run Test Suite** (`test_dry_run.py`) - Command execution testing
4. **Plugin System Test Suite** (`test_plugins.py`) - Plugin functionality testing

## Quick Start

Run all test suites:

```bash
python3 run_tests.py
```

Run individual test suites:

```bash
python3 test_suite.py          # Comprehensive tests
python3 test_interactive.py    # Interactive tests
python3 test_dry_run.py        # Dry-run tests
python3 test_plugins.py        # Plugin tests
```

## Test Suite Details

### 1. Comprehensive Test Suite (`test_suite.py`)

**Purpose**: Tests core PAKA functionality using mocked components and simulated responses.

**What it tests**:
- Core engine initialization
- Package manager registry functionality
- Package operations (search, install, remove) with dry-run mode
- Plugin system loading and management
- Health system functionality
- History management
- Session management
- UI components
- Configuration management
- Error handling
- Menu system initialization
- Plugin event handling
- Package manager simulation
- Advanced features
- Privilege management
- Directory management

**Key Features**:
- Uses `MockPackageManager` to simulate package manager responses
- Tests all operations in dry-run mode
- Validates error handling without system changes
- Tests plugin system with mock configurations

**Example Output**:
```
🚀 Starting PAKA Comprehensive Test Suite
============================================================

🧪 Running test: Core Engine Initialization
✅ Core Engine Initialization - PASSED

🧪 Running test: Package Manager Registry
✅ Package Manager Registry - PASSED

...

📊 TEST RESULTS SUMMARY
============================================================
✅ Passed: 16
❌ Failed: 0
📈 Success Rate: 100.0%

🎉 All tests passed! PAKA is ready for release.
```

### 2. Interactive Test Suite (`test_interactive.py`)

**Purpose**: Tests interactive features like menus, prompts, and user interface components.

**What it tests**:
- UI manager components (info, success, warning, error messages)
- Menu system initialization
- Configuration menu functions
- Package manager menu functions
- Plugin menu functions
- Preferences menu functions
- Shell integration menu functions
- Plugin template creation
- Uninstaller functions
- UI prompt functions (with mocked input)
- UI selection functions
- UI display functions (tables, search results, progress bars)

**Key Features**:
- Mocks user input to test interactive components
- Tests all menu systems without requiring user interaction
- Validates UI component rendering
- Tests plugin template creation process

**Example Output**:
```
🚀 Starting PAKA Interactive Features Test Suite
============================================================

🧪 Running interactive test: UI Manager Components
✅ UI Manager Components - PASSED

🧪 Running interactive test: Menu System Initialization
✅ Menu System Initialization - PASSED

...

📊 INTERACTIVE TEST RESULTS SUMMARY
============================================================
✅ Passed: 12
❌ Failed: 0
📈 Success Rate: 100.0%

🎉 All interactive tests passed!
```

### 3. Dry-Run Test Suite (`test_dry_run.py`)

**Purpose**: Tests actual PAKA commands using dry-run mode to validate real command execution.

**What it tests**:
- Basic PAKA commands (version, help, search, install, remove, update, upgrade)
- Manager-specific commands (search with specific package managers)
- Advanced commands (plugin management, history reconciliation)
- Error handling with invalid commands
- Command output validation

**Key Features**:
- Runs actual PAKA commands with `--dry-run` flag
- Tests all package managers without making system changes
- Validates command-line interface functionality
- Tests error handling for invalid inputs

**Example Output**:
```
🧪 PAKA Dry-Run Test Suite
============================================================

🚀 Testing Basic PAKA Commands
==================================================

🧪 Testing: Version information
Command: paka --version
✅ Command executed successfully
Output:
PAKA version 0.1.0
Universal Package Manager Wrapper

🧪 Testing: Search for firefox (dry run)
Command: paka search firefox --dry-run
✅ Command executed successfully

...

📊 DRY-RUN TEST RESULTS
============================================================
✅ Passed: 25
❌ Failed: 0
📈 Success Rate: 100.0%

🎉 All dry-run tests passed!
PAKA commands are working correctly.
```

### 4. Plugin System Test Suite (`test_plugins.py`)

**Purpose**: Tests the plugin system including template creation, loading, and event handling.

**What it tests**:
- Plugin manager initialization
- Plugin template creation (all types: runtime, health, package manager, advanced)
- Plugin loading and parsing
- Plugin event handling
- Plugin syntax checking
- Plugin enable/disable functionality
- Plugin variable substitution
- Plugin action types (run, log, notify, script)

**Key Features**:
- Creates temporary plugin directories for testing
- Tests all plugin template types
- Validates plugin configuration parsing
- Tests plugin event system
- Tests variable substitution in plugin actions

**Example Output**:
```
🚀 Starting PAKA Plugin System Test Suite
============================================================

🧪 Running plugin test: Plugin Manager Initialization
✅ Plugin Manager Initialization - PASSED

🧪 Running plugin test: Plugin Template Creation
✅ Plugin Template Creation - PASSED

...

📊 PLUGIN TEST RESULTS SUMMARY
============================================================
✅ Passed: 8
❌ Failed: 0
📈 Success Rate: 100.0%

🎉 All plugin tests passed!
```

## Test Environment

### Requirements

- Python 3.7+
- No additional dependencies (uses only standard library)
- No actual package managers required (uses mocks and dry-run mode)

### Test Isolation

All tests use isolated environments:
- Temporary directories for test data
- Mocked package managers
- Simulated user input
- Dry-run mode for all operations

### Test Data

Tests use realistic but safe test data:
- Common package names (firefox, vlc, gimp, krita, blender)
- Standard package manager names (dnf, apt, flatpak, snap, appimage)
- Simulated package information and versions

## Running Tests

### Full Test Suite

```bash
# Run all test suites
python3 run_tests.py
```

### Individual Test Suites

```bash
# Run comprehensive tests
python3 test_suite.py

# Run interactive tests
python3 test_interactive.py

# Run dry-run tests
python3 test_dry_run.py

# Run plugin tests
python3 test_plugins.py
```

### Test Options

All test suites support:
- **Timeout protection**: Tests timeout after 5 minutes to prevent hanging
- **Detailed output**: Shows exactly what's being tested
- **Error reporting**: Detailed error messages for failed tests
- **Success metrics**: Shows pass/fail counts and success rates

## Test Results Interpretation

### Success Criteria

A test suite is considered successful if:
- All tests pass (no failures)
- No exceptions are thrown
- All expected functionality is validated

### Common Issues

**Import Errors**: Usually indicate missing dependencies or path issues
```bash
# Fix: Ensure you're in the PAKA root directory
cd /path/to/paka
python3 test_suite.py
```

**Timeout Errors**: Indicate tests are hanging
```bash
# Fix: Check for infinite loops or blocking operations
# Increase timeout in test files if needed
```

**Mock Errors**: Indicate issues with test setup
```bash
# Fix: Check test environment setup
# Ensure temporary directories are created properly
```

## Continuous Integration

These test suites are designed to be run in CI/CD environments:

```yaml
# Example GitHub Actions workflow
name: PAKA Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: python3 run_tests.py
```

## Test Maintenance

### Adding New Tests

1. **Comprehensive Tests**: Add to `test_suite.py` for core functionality
2. **Interactive Tests**: Add to `test_interactive.py` for UI components
3. **Command Tests**: Add to `test_dry_run.py` for CLI functionality
4. **Plugin Tests**: Add to `test_plugins.py` for plugin system

### Test Best Practices

- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies
- Use isolated test environments
- Provide clear error messages
- Keep tests fast and reliable

### Updating Tests

When adding new features:
1. Update relevant test suites
2. Add new test cases for new functionality
3. Update test documentation
4. Ensure all tests still pass

## Troubleshooting

### Test Failures

1. **Check environment**: Ensure you're in the correct directory
2. **Check dependencies**: Ensure Python 3.7+ is available
3. **Check permissions**: Ensure write access for temporary directories
4. **Check output**: Read error messages for specific issues

### Common Fixes

```bash
# Fix path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Fix permission issues
chmod +x test_*.py
chmod +x run_tests.py

# Fix import issues
python3 -c "import sys; sys.path.insert(0, 'src'); import core.engine"
```

## Test Coverage

The test suites provide comprehensive coverage of:

- ✅ Core engine functionality
- ✅ Package manager interactions
- ✅ Plugin system
- ✅ Health system
- ✅ History management
- ✅ Session management
- ✅ UI components
- ✅ Configuration management
- ✅ Error handling
- ✅ Menu system
- ✅ Command-line interface
- ✅ Interactive features
- ✅ Template generation
- ✅ Event system
- ✅ Variable substitution

## Conclusion

The PAKA testing framework provides comprehensive validation of all system components without requiring actual system changes or package manager installations. This ensures reliable testing across different environments and prevents accidental system modifications during testing.

For questions or issues with the test suites, please refer to the main PAKA documentation or create an issue in the project repository. 