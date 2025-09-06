#!/bin/bash

# Script per aggiungere il campo category agli agenti esistenti
# Basato sulla directory di appartenenza

AGENTS_DIR="/Users/sam/claude-code-hooks-mastery/.claude/agents"

echo "🏷️  Aggiungendo campo category agli agenti..."

# Funzione per aggiungere category a file specifico
add_category_to_file() {
    local file_path="$1"
    local category="$2"
    
    # Verifica se il file contiene già il campo category
    if grep -q "^category:" "$file_path"; then
        echo "   ✅ $file_path - category già presente"
        return
    fi
    
    # Verifica se ha frontmatter YAML
    if ! head -n 1 "$file_path" | grep -q "^---$"; then
        echo "   ⚠️  $file_path - non ha frontmatter YAML"
        return
    fi
    
    # Crea backup
    cp "$file_path" "$file_path.bak"
    
    # Aggiungi category dopo description line
    sed '/^description:/a\
category: '"$category" "$file_path.bak" > "$file_path"
    
    echo "   ✅ $file_path - category: $category aggiunta"
}

# Agenti in backend-architecture/
for file in "$AGENTS_DIR"/backend-architecture/*.md; do
    if [ -f "$file" ]; then
        add_category_to_file "$file" "backend-architecture"
    fi
done

# Agenti in business-marketing/
for file in "$AGENTS_DIR"/business-marketing/*.md; do
    if [ -f "$file" ]; then
        add_category_to_file "$file" "business-marketing"
    fi
done

# Agenti in crypto/
for file in "$AGENTS_DIR"/crypto/*.md; do
    if [ -f "$file" ]; then
        add_category_to_file "$file" "crypto"
    fi
done

# Agenti in data-ai/
for file in "$AGENTS_DIR"/data-ai/*.md; do
    if [ -f "$file" ]; then
        add_category_to_file "$file" "data-ai"
    fi
done

# Agenti in development-architecture/
for file in "$AGENTS_DIR"/development-architecture/*.md; do
    if [ -f "$file" ]; then
        add_category_to_file "$file" "development-architecture"
    fi
done

# Agenti in infrastructure-operations/
for file in "$AGENTS_DIR"/infrastructure-operations/*.md; do
    if [ -f "$file" ]; then
        add_category_to_file "$file" "infrastructure-operations"
    fi
done

# Agenti in language-specialists/ (già fatto python-pro-sonnet)
for file in "$AGENTS_DIR"/language-specialists/*.md; do
    if [ -f "$file" ]; then
        add_category_to_file "$file" "language-specialists"
    fi
done

# Agenti in quality-security/
for file in "$AGENTS_DIR"/quality-security/*.md; do
    if [ -f "$file" ]; then
        add_category_to_file "$file" "quality-security"
    fi
done

# Agenti in specialized-domains/
for file in "$AGENTS_DIR"/specialized-domains/*.md; do
    if [ -f "$file" ]; then
        add_category_to_file "$file" "specialized-domains"
    fi
done

# Agenti nella root (meta-agent-sonnet.md)
for file in "$AGENTS_DIR"/*.md; do
    if [ -f "$file" ]; then
        add_category_to_file "$file" "meta-agents"
    fi
done

echo ""
echo "✅ Category system aggiunto a tutti gli agenti!"
echo ""
echo "📋 Categorie definite:"
echo "   - backend-architecture"
echo "   - business-marketing" 
echo "   - crypto"
echo "   - data-ai"
echo "   - development-architecture"
echo "   - infrastructure-operations"
echo "   - language-specialists"
echo "   - quality-security"
echo "   - specialized-domains"
echo "   - meta-agents"
echo ""
echo "💾 Backup files creati con estensione .bak"