"""
Project-wide path setup utility.
Import this module from anywhere in the project to ensure proper path configuration.
"""
import os
import sys

def setup_project_paths():
    """Setup all necessary paths for the project."""
    # Get the directory containing this file (project root)
    project_root = os.path.dirname(os.path.abspath(__file__))

    # Add apps directory to sys.path
    apps_dir = os.path.join(project_root, 'apps')

    if apps_dir not in sys.path:
        sys.path.insert(0, apps_dir)
        print(f"Added {apps_dir} to sys.path")

    return {
        'project_root': project_root,
        'apps_dir': apps_dir
    }

# Automatically setup paths when this module is imported
_paths = setup_project_paths()

# Export the paths for use by other modules if needed
PROJECT_ROOT = _paths['project_root']
APPS_DIR = _paths['apps_dir']
