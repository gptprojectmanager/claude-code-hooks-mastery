#!/bin/bash
# Script generico per recuperare secrets da Google Cloud Secret Manager
# Uso: ./get-secret.sh <secret-name>
# Esempi: ./get-secret.sh gemini-api-key
#         ./get-secret.sh firecrawl-api-key
#         ./get-secret.sh anthropic-api-key

# Verifica parametro secret name
if [[ -z "$1" ]]; then
    echo "FALLBACK_FROM_ENV"
    exit 0
fi

SECRET_NAME="$1"

# Recupera il secret da Google Cloud Secret Manager
# In caso di errore, restituisce fallback generico
gcloud secrets versions access latest --secret="$SECRET_NAME" 2>/dev/null || echo "FALLBACK_FROM_ENV"