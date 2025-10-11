"""
Central path configuration for the BCF project.
This module ensures the apps directory is in sys.path for consistent imports.
"""
import os
import sys

def setup_project_path():
    """
    Add the apps directory to sys.path if it's not already there.
    This should be called once at the start of the application.
    """
    # Get the directory containing this file (BCF)
    bcf_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up to the project root (development_phases/phase2.5)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(bcf_dir)))

    # Add apps directory to sys.path
    apps_dir = os.path.join(project_root, 'apps')

    if apps_dir not in sys.path:
        sys.path.insert(0, apps_dir)

    return apps_dir


# Call this when the module is imported
setup_project_path()
