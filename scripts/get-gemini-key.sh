#!/bin/bash
# Recupera la chiave Gemini da Secret Manager
gcloud secrets versions access latest --secret="gemini-api-key" 2>/dev/null || echo "FALLBACK_KEY_FROM_ENV"
