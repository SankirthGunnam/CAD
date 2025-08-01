# Pytest Test Package Naming Conventions

This document outlines the naming conventions and best practices for test packages when using **pytest** in Python projects. It is designed for clarity and compatibility, making it easy to store and reference in Notion.

## Overview

Pytest is flexible with test package naming, allowing you to choose names that suit your project. However, following conventions and best practices ensures better organization and maintainability.

## Key Points

### 1. Flexible Package Naming

- Pytest does **not** enforce strict naming rules for test packages (directories containing test files).
- You can use any valid Python package name (e.g., no spaces, no reserved keywords).

### 2. Common Conventions

- **Standard Name**: The most common test package name is `tests` or `test`.
- **Subdirectories**: Use descriptive names for subdirectories based on functionality, such as:
    - `tests/unit` for unit tests
    - `tests/integration` for integration tests
    - `tests/api` for API-related tests

### 3. Test File Naming

- Test files **must** follow pytest’s default naming patterns for automatic discovery:
    - `test_*.py` (e.g., `test_module.py`)
    - `_test.py` (e.g., `module_test.py`)
- Ensure test files are placed inside a valid Python package (a directory with an `__init__.py` file).

### 4. Package Structure

- A test package must include an `__init__.py` file (even if empty) to be recognized as a Python package.
- Example structure:
    
    ```
    my_project/
    ├── src/
    │   └── my_module.py
    ├── custom_tests/  # Custom test package name
    │   ├── __init__.py
    │   ├── test_module.py
    │   └── test_utils.py
    └── pytest.ini
    
    ```
    

### 5. Best Practices

- Use **descriptive names** that reflect the purpose of the tests (e.g., `tests/database`, `tests/api_endpoints`).
- Avoid generic or ambiguous names to prevent confusion.
- Align the test package structure with your project’s codebase for easier navigation.

### 6. Customizing Test Discovery

If you prefer non-standard package or file names, configure pytest to discover tests in specific directories:

- **Command Line**: Use the `-testpaths` option:
    
    ```bash
    pytest --testpaths custom_tests
    
    ```
    
- **Configuration File**: Specify test paths in `pytest.ini` or `pyproject.toml`:
    
    ```
    [pytest]
    testpaths = custom_tests another_test_dir
    
    ```
    

## Key Takeaway

You can name test packages freely in pytest, but using conventions like `tests` or descriptive names improves readability and maintainability. Ensure test files follow pytest’s naming patterns (`test_*.py` or `*_test.py`) for automatic discovery.