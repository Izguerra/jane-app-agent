#!/usr/bin/env python3
"""
Fix Next.js 15 async params in all dynamic route handlers.
Handles all patterns of params usage.
"""

import re
import os
from pathlib import Path

def fix_route_file(filepath):
    """Fix a single route.ts file to use async params."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: Fix params type declaration
    # { params }: { params: { ... } } -> { params }: { params: Promise<{ ... }> }
    content = re.sub(
        r'\{ params \}: \{ params: (\{[^}]+\}) \}',
        r'{ params }: { params: Promise<\1> }',
        content
    )
    
    # Pattern 2: Find all function signatures with params
    # We need to add `const { ... } = await params;` at the start of each function
    
    # Find all route handler functions (GET, POST, PUT, PATCH, DELETE)
    function_pattern = r'export async function (GET|POST|PUT|PATCH|DELETE)\s*\([^)]*\{ params \}[^)]*\)\s*\{'
    
    def add_await_params(match):
        """Add await params destructuring at the start of the function."""
        func_start = match.group(0)
        
        # Extract param names from the function signature
        param_match = re.search(r'\{ params \}: \{ params: Promise<\{([^}]+)\}>', func_start)
        if not param_match:
            return func_start
        
        param_str = param_match.group(1).strip()
        # Parse param names (handle both "id: string" and "path: string[]" patterns)
        param_names = []
        for param in param_str.split(','):
            param_name = param.split(':')[0].strip()
            param_names.append(param_name)
        
        # Create destructuring statement
        if len(param_names) == 1:
            destructure = f"const {{ {param_names[0]} }} = await params;"
        else:
            destructure = f"const {{ {', '.join(param_names)} }} = await params;"
        
        # Add the destructuring right after the opening brace
        return func_start + f"\n    {destructure}"
    
    content = re.sub(function_pattern, add_await_params, content)
    
    # Pattern 3: Remove any remaining direct params.x usage
    # This is tricky because we need to make sure we're not replacing URLSearchParams
    # Only replace if we added the await params line
    if "await params;" in content:
        # Remove old const x = params.x; lines
        content = re.sub(r'\n\s*const \w+ = params\.\w+;', '', content)
    
    # Only write if content changed
    if content != original_content:
        # Create backup
        backup_path = str(filepath) + '.bak'
        with open(backup_path, 'w') as f:
            f.write(original_content)
        
        # Write fixed content
        with open(filepath, 'w') as f:
            f.write(content)
        
        return True
    return False

def main():
    """Find and fix all route.ts files."""
    api_dir = Path('app/api')
    fixed_count = 0
    
    for route_file in api_dir.rglob('route.ts'):
        if '.bak' in str(route_file):
            continue
        
        if fix_route_file(route_file):
            print(f"Fixed: {route_file}")
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")
    print("Backup files created with .bak extension")

if __name__ == '__main__':
    main()
