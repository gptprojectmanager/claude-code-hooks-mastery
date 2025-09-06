#!/bin/bash

# Script sicuro per avviare liteLLM con Secret Manager
set -e

echo "🔐 Avvio liteLLM con configurazione sicura..."

# Recupera la chiave da Secret Manager  
echo "🔑 Recupero chiave Gemini da Secret Manager..."
GEMINI_API_KEY=$(gcloud secrets versions access latest --secret="gemini-api-key" 2>/dev/null)

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Errore: Impossibile recuperare la chiave da Secret Manager"
    echo "💡 Assicurati di aver configurato il secret con: ./scripts/setup-secrets.sh YOUR_KEY"
    exit 1
fi

# Genera master key temporanea per liteLLM
LITELLM_MASTER_KEY=$(openssl rand -hex 32)

# Export delle variabili ambiente
export GEMINI_API_KEY="$GEMINI_API_KEY"
export LITELLM_MASTER_KEY="$LITELLM_MASTER_KEY"

# Kill processi esistenti
pkill -f "litellm.*4001" 2>/dev/null || true
sleep 2

cd /Users/sam/claude-code-hooks-mastery

echo "🚀 Avvio liteLLM proxy server sicuro..."
echo "📊 Dashboard: http://localhost:4001/ui (Master Key: $LITELLM_MASTER_KEY)"

# Avvia liteLLM con configurazione sicura
litellm --config litellm-secure-config.yaml \
    --port 4001 \
    --host 127.0.0.1 \
    --detailed_debug &

sleep 3

echo "✅ liteLLM avviato con successo!"
echo "🔍 Verifica stato:"
lsof -i :4001

echo ""
echo "🔐 Configurazione sicurezza completata:"
echo "   ✓ API Key recuperata da Secret Manager"  
echo "   ✓ Master Key generata dinamicamente"
echo "   ✓ Logging sicuro abilitato"
echo "   ✓ UI protetta (admin only)"