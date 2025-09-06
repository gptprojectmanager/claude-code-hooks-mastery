#!/bin/bash

# Script per configurare Google Cloud Secret Manager
# Uso: ./setup-secrets.sh NEW_GEMINI_API_KEY

set -e

if [ -z "$1" ]; then
    echo "❌ Errore: Fornire la nuova chiave API Gemini come argomento"
    echo "Uso: ./setup-secrets.sh YOUR_NEW_GEMINI_API_KEY"
    exit 1
fi

NEW_API_KEY="$1"

echo "🔐 Configurazione Google Cloud Secret Manager..."

# Crea il secret per Gemini API Key
echo "📝 Creazione secret gemini-api-key..."
echo -n "$NEW_API_KEY" | gcloud secrets create gemini-api-key \
    --data-file=- \
    --locations=us-east5 \
    --replication-policy="user-managed" || \
echo "✅ Secret esistente, aggiornamento versione..."
echo -n "$NEW_API_KEY" | gcloud secrets versions add gemini-api-key --data-file=-

# Imposta le policy IAM per accedere al secret
echo "🔑 Configurazione permessi IAM..."
PROJECT_NUMBER=$(gcloud projects describe custom-mix-460500-g9 --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

# Crea script per recuperare la chiave
cat > /Users/sam/claude-code-hooks-mastery/scripts/get-gemini-key.sh << 'EOF'
#!/bin/bash
# Recupera la chiave Gemini da Secret Manager
gcloud secrets versions access latest --secret="gemini-api-key" 2>/dev/null || echo "FALLBACK_KEY_FROM_ENV"
EOF

chmod +x /Users/sam/claude-code-hooks-mastery/scripts/get-gemini-key.sh

echo "✅ Secret Manager configurato con successo!"
echo "📋 Comandi utili:"
echo "   Recupera chiave: gcloud secrets versions access latest --secret=gemini-api-key"
echo "   Lista secrets:   gcloud secrets list"
echo "   Aggiorna chiave: echo 'NUOVA_CHIAVE' | gcloud secrets versions add gemini-api-key --data-file=-"