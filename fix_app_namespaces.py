#!/usr/bin/env python
"""
Script to add app_name to all Django app URL files to fix namespace issues.
Run this from the project root directory.
"""

import os
import re

# List of app directories to check
APP_DIRS = [
    'Apps/users',
    'Apps/entity',
    'Apps/project',
    'Apps/rbac',
    'Apps/documents',
    'Apps/automation',
    'Apps/communication',
    'Apps/data_import_export',
    'Apps/data_transfer',
    'Apps/time_management'
]

def add_app_name_to_urls(app_dir, app_name):
    """
    Add app_name to urls.py file in the given app directory.
    """
    urls_file = os.path.join(app_dir, 'urls.py')
    
    if not os.path.exists(urls_file):
        print(f"Warning: {urls_file} does not exist.")
        return False
    
    with open(urls_file, 'r') as f:
        content = f.read()
    
    # Check if app_name is already defined
    if re.search(r'^app_name\s*=', content, re.MULTILINE):
        print(f"App name already defined in {urls_file}")
        return False
    
    # Find insertion point after imports
    import_pattern = r'((?:from|import).*?\n)+'
    match = re.search(import_pattern, content)
    
    if match:
        # Insert after imports with a blank line
        end_of_imports = match.end()
        modified_content = (
            content[:end_of_imports] +
            f"\n# Define the app name for namespacing\napp_name = '{app_name}'\n\n" +
            content[end_of_imports:]
        )
    else:
        # Just insert at the top if imports not found
        modified_content = f"# Define the app name for namespacing\napp_name = '{app_name}'\n\n" + content
    
    # Write the modified content back
    with open(urls_file, 'w') as f:
        f.write(modified_content)
    
    print(f"Added app_name = '{app_name}' to {urls_file}")
    return True

def main():
    """Main function to process all app directories."""
    total_fixed = 0
    
    for app_dir in APP_DIRS:
        # App name is the last part of the directory path
        app_name = app_dir.split('/')[-1].replace('_', '-')
        
        if add_app_name_to_urls(app_dir, app_name):
            total_fixed += 1
    
    print(f"\nFixed {total_fixed} URL files to include app_name.")

if __name__ == "__main__":
    main() 