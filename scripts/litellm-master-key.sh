#!/bin/bash

# Gestione Master Key LiteLLM
MASTER_KEY_FILE="/Users/sam/claude-code-hooks-mastery/.litellm-master-key"

case "$1" in
    "generate")
        echo "🔐 Generazione nuova Master Key..."
        MASTER_KEY=$(openssl rand -hex 32)
        echo "$MASTER_KEY" > "$MASTER_KEY_FILE"
        chmod 600 "$MASTER_KEY_FILE"
        echo "✅ Master Key salvata in: $MASTER_KEY_FILE"
        echo "📋 Master Key: $MASTER_KEY"
        ;;
    "get")
        if [ -f "$MASTER_KEY_FILE" ]; then
            cat "$MASTER_KEY_FILE"
        else
            echo "❌ Nessuna Master Key trovata. Usa: $0 generate"
            exit 1
        fi
        ;;
    "show")
        if [ -f "$MASTER_KEY_FILE" ]; then
            echo "📋 Master Key: $(cat "$MASTER_KEY_FILE")"
            echo "🔗 Dashboard: http://localhost:4001/ui"
        else
            echo "❌ Nessuna Master Key trovata. Usa: $0 generate"
            exit 1
        fi
        ;;
    *)
        echo "Uso: $0 {generate|get|show}"
        echo ""
        echo "  generate  - Genera nuova master key"
        echo "  get       - Recupera master key esistente"  
        echo "  show      - Mostra master key e link dashboard"
        exit 1
        ;;
esac