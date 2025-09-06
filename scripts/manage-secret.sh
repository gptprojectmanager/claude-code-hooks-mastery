#!/bin/bash

# Script interattivo per gestire secrets in Google Cloud Secret Manager
# Uso: ./manage-secret.sh [secret-name] [api-key] (parametri opzionali)

set -e

# Colors per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validazione prerequisiti
validate_prerequisites() {
    echo "🔧 Validazione prerequisiti..."
    
    # Verifica gcloud CLI installato
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ Errore: gcloud CLI non trovato${NC}"
        echo "Installa Google Cloud SDK da: https://cloud.google.com/sdk/docs/install"
        return 1
    fi
    echo "✅ Google Cloud SDK installato"
    
    # Verifica autenticazione gcloud
    local auth_account
    auth_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")
    if [[ -z "$auth_account" ]]; then
        echo -e "${RED}❌ Errore: Nessuna autenticazione Google Cloud attiva${NC}"
        echo "Autentica con: gcloud auth login"
        return 1
    fi
    echo "✅ Autenticato come: $auth_account"
    
    # Verifica progetto configurato
    local project_id
    project_id=$(gcloud config get-value project 2>/dev/null)
    if [[ -z "$project_id" ]]; then
        echo -e "${RED}❌ Errore: Nessun progetto Google Cloud configurato${NC}"
        echo "Configura un progetto con: gcloud config set project YOUR_PROJECT_ID"
        return 1
    fi
    echo "✅ Progetto corrente: $project_id"
    
    # Verifica Secret Manager API abilitata
    if ! gcloud services list --enabled --filter="name:secretmanager.googleapis.com" --format="value(name)" 2>/dev/null | grep -q secretmanager; then
        echo -e "${YELLOW}⚠️  Secret Manager API non abilitata${NC}"
        echo "🔄 Tentativo di abilitazione Secret Manager API..."
        if gcloud services enable secretmanager.googleapis.com 2>/dev/null; then
            echo "✅ Secret Manager API abilitata"
        else
            echo -e "${RED}❌ Errore: Impossibile abilitare Secret Manager API${NC}"
            echo "Abilita manualmente con: gcloud services enable secretmanager.googleapis.com"
            return 1
        fi
    else
        echo "✅ Secret Manager API abilitata"
    fi
    
    return 0
}

# Input sicuro per API key (senza echo)
read_api_key() {
    echo -n "Inserisci l'API Key: "
    read -s api_key
    echo ""
    
    if [[ -z "$api_key" ]]; then
        echo -e "${RED}❌ Errore: API Key non può essere vuota${NC}"
        return 1
    fi
    
    echo "$api_key"
}

# Core logic per creare/aggiornare secret
manage_secret() {
    local secret_name="$1"
    local api_key="$2"
    
    echo -e "${BLUE}🔐 Gestione secret '$secret_name' in Secret Manager...${NC}"
    
    # Crea il secret (senza esporre l'API key nei log)
    echo "📝 Creazione/aggiornamento secret $secret_name..."
    echo -n "$api_key" | gcloud secrets create "$secret_name" \
        --data-file=- \
        --locations="us-east5" \
        --replication-policy="user-managed" 2>/dev/null || {
        echo "✅ Secret esistente, aggiornamento versione..."
        echo -n "$api_key" | gcloud secrets versions add "$secret_name" --data-file=- 2>/dev/null
    }
    
    # Configura IAM permissions
    echo "🔑 Configurazione permessi IAM..."
    local project_id
    project_id=$(gcloud config get-value project 2>/dev/null)
    local project_number
    project_number=$(gcloud projects describe "$project_id" --format="value(projectNumber)")
    local service_account="${project_number}-compute@developer.gserviceaccount.com"
    
    gcloud secrets add-iam-policy-binding "$secret_name" \
        --member="serviceAccount:${service_account}" \
        --role="roles/secretmanager.secretAccessor" &>/dev/null
    
    echo -e "${GREEN}✅ Secret '$secret_name' configurato con successo!${NC}"
    echo "📋 Recupera con: gcloud secrets versions access latest --secret=$secret_name"
}

# Funzione principale
main() {
    echo -e "${BLUE}"
    echo "🔐 GESTIONE SECRETS - GOOGLE CLOUD SECRET MANAGER"
    echo "==============================================="
    echo -e "${NC}"
    
    # Validazione prerequisiti
    if ! validate_prerequisites; then
        exit 1
    fi
    
    echo ""
    
    # Input del nome secret
    local secret_name="$1"
    if [[ -z "$secret_name" ]]; then
        echo -e "${BLUE}📝 Inserisci il nome del secret:${NC}"
        echo "   Esempi: anthropic-api-key, firecrawl-api-key, github-token"
        echo -n "Nome secret: "
        read -r secret_name
    fi
    
    # Validazione nome secret
    if [[ -z "$secret_name" ]]; then
        echo -e "${RED}❌ Errore: Nome secret non può essere vuoto${NC}"
        exit 1
    fi
    
    if [[ ! "$secret_name" =~ ^[a-zA-Z0-9-]+$ ]]; then
        echo -e "${RED}❌ Errore: Nome secret non valido${NC}"
        echo "Usa solo caratteri alfanumerici e trattini"
        exit 1
    fi
    
    # Input dell'API key
    local api_key="$2"
    if [[ -z "$api_key" ]]; then
        echo -e "${BLUE}🔑 Inserisci l'API Key (input nascosto per sicurezza):${NC}"
        api_key=$(read_api_key)
        if [[ $? -ne 0 ]]; then
            exit 1
        fi
    fi
    
    # Conferma operazione
    echo ""
    echo -e "${YELLOW}🔍 Riepilogo operazione:${NC}"
    echo "  Secret name: $secret_name"
    echo "  API Key: *** (nascosta per sicurezza)"
    echo ""
    echo -n "Procedere? (y/N): "
    read -r confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Operazione annullata dall'utente"
        exit 0
    fi
    
    # Esegui la gestione del secret
    echo ""
    manage_secret "$secret_name" "$api_key"
    
    echo ""
    echo -e "${GREEN}🎉 Operazione completata con successo!${NC}"
}

# Esegui funzione principale con tutti gli argomenti
main "$@"