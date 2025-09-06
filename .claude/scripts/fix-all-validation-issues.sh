#!/bin/bash

# Script per fixare tutti i problemi di validazione identificati

AGENTS_DIR="/Users/sam/claude-code-hooks-mastery/.claude/agents"
COMMANDS_DIR="/Users/sam/claude-code-hooks-mastery/.claude/commands"

echo "🔧 Fixing all validation issues..."

# 1. Fix YAML formatting issues (category senza newline)
echo "   📝 Fixing YAML formatting..."
find "$AGENTS_DIR" -name "*.md" -not -name "*.bak" | while read -r file; do
    if grep -q "category: .*tools:" "$file"; then
        echo "      🔧 Fixing $file"
        cp "$file" "$file.validation.bak"
        sed 's/category: \(.*\)tools:/category: \1\ntools:/' "$file.validation.bak" > "$file"
    fi
done

# 2. Fix agenti con nomi non conformi
echo "   🏷️  Fixing agent names..."

# iOS Developer Specialist -> ios-developer-sonnet
IOS_FILE="$AGENTS_DIR/language-specialists/ios-developer-sonnet.md"
if [ -f "$IOS_FILE" ]; then
    echo "      🔧 Fixing ios-developer-sonnet name"
    sed -i.validation.bak 's/name: "iOS Developer Specialist"/name: ios-developer-sonnet/' "$IOS_FILE"
fi

# SQL Professional Specialist -> sql-pro-sonnet  
SQL_FILE="$AGENTS_DIR/language-specialists/sql-pro-sonnet.md"
if [ -f "$SQL_FILE" ]; then
    echo "      🔧 Fixing sql-pro-sonnet name"
    sed -i.validation.bak 's/name: "SQL Professional Specialist"/name: sql-pro-sonnet/' "$SQL_FILE"
fi

# 3. Fix primary-agent-opusplan model field
OPUSPLAN_FILE="$AGENTS_DIR/specialized-domains/primary-agent-opusplan.md"
if [ -f "$OPUSPLAN_FILE" ]; then
    echo "      🔧 Adding model field to primary-agent-opusplan"
    if ! grep -q "^model:" "$OPUSPLAN_FILE"; then
        sed -i.validation.bak '/^category:/a\
model: opus' "$OPUSPLAN_FILE"
    fi
fi

# 4. Fix commands argument-hint arrays to strings
echo "   ⚡ Fixing command argument-hint fields..."

fix_command_hint() {
    local file="$1"
    if grep -q "argument-hint: \[" "$file"; then
        echo "      🔧 Fixing $file argument-hint"
        cp "$file" "$file.validation.bak"
        sed 's/argument-hint: \[\([^]]*\)\]/argument-hint: \1/' "$file.validation.bak" > "$file"
    fi
}

# Fix specific commands
for cmd in "architect" "optimize" "planner" "research" "validate" "crypto_research" "crypto_research_haiku"; do
    cmd_file="$COMMANDS_DIR/${cmd}.md"
    if [ -f "$cmd_file" ]; then
        fix_command_hint "$cmd_file"
    fi
done

echo "✅ All validation issues fixed!"

# Test validation
echo ""
echo "🧪 Running validation test..."
cd "/Users/sam/claude-code-hooks-mastery/.claude/scripts"
node validate-agents.js