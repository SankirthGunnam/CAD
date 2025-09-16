#!/usr/bin/env python3
"""
Launcher script for the Search Feature Demo

This script checks for required dependencies and launches the search demo.
"""

import sys
import subprocess
import importlib.util

def check_pyside6():
    """Check if PySide6 is available."""
    try:
        import PySide6
        return True
    except ImportError:
        return False

def install_pyside6():
    """Install PySide6 if not available."""
    print("PySide6 not found. Installing...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PySide6"])
        print("PySide6 installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install PySide6. Please install it manually:")
        print("pip install PySide6")
        return False

def main():
    """Main launcher function."""
    print("Search Feature Demo Launcher")
    print("=" * 40)

    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        print(f"Current version: {sys.version}")
        return 1

    # Check PySide6
    if not check_pyside6():
        print("PySide6 is required but not installed.")
        response = input("Would you like to install it now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            if not install_pyside6():
                return 1
        else:
            print("Please install PySide6 manually and try again.")
            return 1

    # Import and run the demo
    try:
        from search_demo import main as run_demo
        print("Starting Search Feature Demo...")
        run_demo()
    except ImportError as e:
        print(f"Error importing search demo: {e}")
        return 1
    except Exception as e:
        print(f"Error running demo: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
