#!/bin/bash

# Fix Next.js 15 async params in all dynamic route handlers

echo "Fixing async params in dynamic routes..."

# Find all route.ts files with dynamic params
find app/api -name "route.ts" -type f | while read file; do
    # Check if file contains old params pattern
    if grep -q "{ params }: { params: {" "$file"; then
        echo "Fixing: $file"
        
        # Create backup
        cp "$file" "$file.bak"
        
        # Fix the params type to be Promise
        sed -i '' 's/{ params }: { params: { \([^}]*\) }}/{ params }: { params: Promise<{ \1 }> }/g' "$file"
        
        # Fix params access - need to handle different patterns
        # Pattern 1: const x = params.x;
        sed -i '' 's/const \([a-zA-Z_][a-zA-Z0-9_]*\) = params\.\1;/const { \1 } = await params;/g' "$file"
        
        # Pattern 2: const { x } = params; (already correct, just needs await)
        sed -i '' 's/const { \([^}]*\) } = params;/const { \1 } = await params;/g' "$file"
        
        # Pattern 3: params.x direct usage (need to destructure first)
        # This is more complex and might need manual fixing
    fi
done

echo "Done! Backup files created with .bak extension"
