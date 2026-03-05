#!/usr/bin/env python3
"""Update footer links and clean up FAQ UI"""

# Read the file
with open('public/landing.html', 'r') as f:
    content = f.read()

# Update footer Legal links
content = content.replace(
    '<li><a href="#" class="hover:text-primary transition-colors">Privacy</a></li>',
    '<li><a href="/privacy" class="hover:text-primary transition-colors">Privacy</a></li>'
)

content = content.replace(
    '<li><a href="#" class="hover:text-primary transition-colors">Terms</a></li>',
    '<li><a href="/terms" class="hover:text-primary transition-colors">Terms</a></li>'
)

# Clean up FAQ UI - remove the icon circles and simplify
# Replace the complex icon div with simpler version
old_icon_pattern = '''<div class="shrink-0 pt-1">
                            <div
                                class="size-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                <span class="material-symbols-outlined" style="font-size: 20px;">'''

new_icon_pattern = '''<div class="shrink-0 pt-1">
                            <span class="material-symbols-outlined text-primary" style="font-size: 24px;">'''

content = content.replace(old_icon_pattern, new_icon_pattern)

# Close the icon properly
content = content.replace(
    '''</span>
                            </div>
                        </div>''',
    '''</span>
                        </div>'''
)

# Write back
with open('public/landing.html', 'w') as f:
    f.write(content)

print("✅ Updated footer links and cleaned up FAQ UI")
