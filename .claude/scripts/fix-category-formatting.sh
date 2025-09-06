#!/bin/bash

# Fix della formattazione del campo category

AGENTS_DIR="/Users/sam/claude-code-hooks-mastery/.claude/agents"

echo "🔧 Fixing category field formatting..."

find "$AGENTS_DIR" -name "*.md" -not -name "*.bak" | while read -r file; do
    if grep -q "category: .*model:" "$file"; then
        echo "   🔧 Fixing $file"
        # Backup
        cp "$file" "$file.fix.bak"
        
        # Fix formatting: aggiungi newline tra category e model
        sed 's/category: \(.*\)model:/category: \1\nmodel:/' "$file.fix.bak" > "$file"
        
        echo "   ✅ Fixed $file"
    fi
done

echo "✅ Category formatting fixed!"