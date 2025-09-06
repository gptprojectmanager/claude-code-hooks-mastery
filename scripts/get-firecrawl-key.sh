#!/bin/bash
# Recupera la chiave Firecrawl da Secret Manager
gcloud secrets versions access latest --secret="firecrawl-api-key" 2>/dev/null || echo "FALLBACK_FIRECRAWL_KEY_FROM_ENV"