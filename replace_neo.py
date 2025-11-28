#!/usr/bin/env python3
import os
import re
from pathlib import Path

# Define replacements
replacements = [
    # Card styling
    (r'neo-shadow border-none bg-\[var\(--neo-bg\)\]', 'card-modern'),
    (r'neo-shadow', 'shadow-modern-md'),
    (r'neo-shadow-sm', 'shadow-modern-sm'),
    
    # Input styling
    (r'neo-inset bg-transparent border-none', ''),
    (r'neo-inset', 'glass'),
    
    # Button styling
    (r'neo-btn bg-\[var\(--neo-bg\)\] text-primary hover:bg-\[var\(--neo-bg\)\] border-none', ''),
    (r'neo-btn', 'btn-modern'),
    
    # Background
    (r'bg-\[var\(--neo-bg\)\]', 'bg-card'),
]

def replace_in_file(file_path):
    """Replace neomorphic classes in a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")
        return True
    return False

def main():
    """Main function to process all TSX files."""
    base_dir = Path(__file__).parent
    directories = [
        base_dir / 'app' / '(dashboard)',
        base_dir / 'components',
    ]
    
    updated_count = 0
    for directory in directories:
        if directory.exists():
            for tsx_file in directory.rglob('*.tsx'):
                if replace_in_file(tsx_file):
                    updated_count += 1
    
    print(f"\nTotal files updated: {updated_count}")

if __name__ == '__main__':
    main()
