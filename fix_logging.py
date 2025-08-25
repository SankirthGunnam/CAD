#!/usr/bin/env python3
"""
Script to fix logging f-string interpolation issues in Python files.
Converts logger calls from f-string format to lazy % formatting.
"""

import os
import re
import glob

def fix_logging_fstrings(file_path):
    """Fix logging f-string interpolation issues in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match logger calls with f-strings
        # Matches: logger.info(f"message {var}"), logger.error(f"message {var}"), etc.
        pattern = r'logger\.(info|warning|error|debug|critical)\(f"([^"]*)"\)'
        
        def replace_logger_call(match):
            log_level = match.group(1)
            message = match.group(2)
            
            # Extract variables from the f-string
            var_pattern = r'\{([^}]+)\}'
            variables = re.findall(var_pattern, message)
            
            if not variables:
                # No variables, just remove the f prefix
                return f'logger.{log_level}("{message}")'
            
            # Replace f-string variables with %s placeholders
            new_message = re.sub(var_pattern, '%s', message)
            
            # Create the new logger call with variables as arguments
            if len(variables) == 1:
                return f'logger.{log_level}("{new_message}", {variables[0]})'
            else:
                # For multiple variables, we need to handle them carefully
                # This is a simplified approach - in practice, you might need more complex logic
                return f'logger.{log_level}("{new_message}", {", ".join(variables)})'
        
        # Apply the replacement
        new_content = re.sub(pattern, replace_logger_call, content)
        
        # If content changed, write it back
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed logging issues in: {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix logging issues in all Python files."""
    phase3_dir = "/home/sankirth/Projects/CAD/SDTS/development_phases/phase3"
    
    if not os.path.exists(phase3_dir):
        print(f"Directory {phase3_dir} not found!")
        return
    
    # Find all Python files
    python_files = glob.glob(f"{phase3_dir}/**/*.py", recursive=True)
    
    print(f"Found {len(python_files)} Python files to process...")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_logging_fstrings(file_path):
            fixed_count += 1
    
    print(f"\nFixed logging issues in {fixed_count} files.")

if __name__ == "__main__":
    main()
