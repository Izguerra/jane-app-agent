#!/usr/bin/env python3
"""
Remove duplicate 'const { ... } = await params;' lines from route files.
"""

import re
from pathlib import Path

def remove_duplicate_await_params(filepath):
    """Remove duplicate await params declarations."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    original_content = ''.join(lines)
    new_lines = []
    seen_await_params = {}
    
    for i, line in enumerate(lines):
        # Check if this line is a 'const { ... } = await params;' declaration
        if re.match(r'\s*const\s*\{[^}]+\}\s*=\s*await\s+params;', line):
            # Extract the function context (look backwards for function declaration)
            func_context = None
            for j in range(i-1, max(0, i-20), -1):
                if 'export async function' in lines[j]:
                    func_context = j
                    break
            
            # Use function context as key to track duplicates
            if func_context is not None:
                if func_context in seen_await_params:
                    # Skip this duplicate line
                    print(f"Removing duplicate at line {i+1} in {filepath}")
                    continue
                else:
                    seen_await_params[func_context] = True
        
        # Also remove old 'const path = params.path.join('/')' style lines
        if re.match(r'\s*const\s+path\s*=\s*params\.path\.join\(', line):
            print(f"Removing old path declaration at line {i+1} in {filepath}")
            continue
            
        new_lines.append(line)
    
    new_content = ''.join(new_lines)
    
    if new_content != original_content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    """Find and fix all route.ts files."""
    api_dir = Path('app/api')
    fixed_count = 0
    
    for route_file in api_dir.rglob('route.ts'):
        if '.bak' in str(route_file):
            continue
        
        if remove_duplicate_await_params(route_file):
            print(f"Fixed: {route_file}")
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()
