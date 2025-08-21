#!/usr/bin/env python3
"""
Script to format the files modified for floating toolbar fixes with autopep8
"""

import subprocess
import sys
from pathlib import Path


def format_file(file_path):
    """Format a single Python file with autopep8"""
    try:
        print(f"Formatting: {file_path}")
        result = subprocess.run([
            'autopep8', '--in-place', '--aggressive', '--aggressive', str(file_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✅ Successfully formatted: {file_path}")
        else:
            print(f"  ❌ Error formatting: {file_path}")
            print(f"    Error: {result.stderr}")
            
    except Exception as e:
        print(f"  ❌ Exception formatting: {file_path}")
        print(f"    Exception: {e}")


def main():
    """Main function to format the modified files"""
    phase3_dir = Path(__file__).parent
    
    print("🚀 Starting formatting of floating toolbar fix files...")
    print(f"📁 Working directory: {phase3_dir}")
    print()
    
    # List of files that were modified for floating toolbar fixes
    files_to_format = [
        "apps/RBM5/BCF/source/controllers/visual_bcf/visual_bcf_controller.py",
        "apps/RBM5/BCF/gui/source/visual_bcf/floating_toolbar.py",
        "apps/RBM5/BCF/gui/source/visual_bcf/visual_bcf_manager.py"
    ]
    
    print(f"📊 Found {len(files_to_format)} files to format")
    print()
    
    # Format each file
    for file_path in files_to_format:
        full_path = phase3_dir / file_path
        if full_path.exists():
            print(f"Processing: {file_path}")
            format_file(full_path)
            print()
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print("🎉 Floating toolbar fix files formatting completed!")
    print(f"📊 Total files processed: {len(files_to_format)}")


if __name__ == "__main__":
    main()
