"""
BCF Package Initialization
Handles central path configuration for the entire BCF project.
"""
import os
import sys

# Add apps directory to sys.path for consistent imports
_bcf_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_bcf_dir)))
_apps_dir = os.path.join(_project_root, 'apps')

if _apps_dir not in sys.path:
    sys.path.insert(0, _apps_dir)
