#!/bin/bash

# =============================================================================
# SECURE OPENAI API KEY STORAGE SCRIPT
# =============================================================================
# Purpose: Securely add OpenAI API key to Google Secret Manager
# Project: custom-mix-460500-g9
# Security: No API key exposure in logs or script source
# Author: Claude Code System
# =============================================================================

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Configuration
PROJECT_ID="custom-mix-460500-g9"
SECRET_NAME="openai-api-key"
SECRET_DESCRIPTION="OpenAI API key for Claude Code system integration"
LOG_FILE="/tmp/openai_secret_$(date +%s).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Security function: Clean sensitive data from memory
cleanup_sensitive_data() {
    if [[ -n "${API_KEY:-}" ]]; then
        unset API_KEY
    fi
    if [[ -f "$LOG_FILE" ]]; then
        rm -f "$LOG_FILE" 2>/dev/null || true
    fi
}

# Trap to ensure cleanup on exit
trap cleanup_sensitive_data EXIT INT TERM

# Logging function (NO SENSITIVE DATA)
log_action() {
    local level="$1"
    local message="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a "$LOG_FILE" >&2
}

# Validation functions
validate_gcloud_auth() {
    log_action "INFO" "Validating Google Cloud authentication..."
    
    if ! command -v gcloud &> /dev/null; then
        log_action "ERROR" "gcloud CLI not found. Please install Google Cloud SDK."
        return 1
    fi
    
    local auth_account
    auth_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")
    
    if [[ -z "$auth_account" ]]; then
        log_action "ERROR" "No active Google Cloud authentication found."
        log_action "INFO" "Please run: gcloud auth login"
        return 1
    fi
    
    log_action "INFO" "✅ Authenticated as: $auth_account"
    return 0
}

validate_project_access() {
    log_action "INFO" "Validating project access..."
    
    if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
        log_action "ERROR" "Cannot access project: $PROJECT_ID"
        return 1
    fi
    
    # Check Secret Manager API is enabled
    if ! gcloud services list --enabled --filter="name:secretmanager.googleapis.com" --format="value(name)" 2>/dev/null | grep -q secretmanager; then
        log_action "WARN" "Secret Manager API may not be enabled"
        log_action "INFO" "Attempting to enable Secret Manager API..."
        gcloud services enable secretmanager.googleapis.com --project="$PROJECT_ID" || {
            log_action "ERROR" "Failed to enable Secret Manager API"
            return 1
        }
    fi
    
    log_action "INFO" "✅ Project access validated"
    return 0
}

validate_api_key_format() {
    local key="$1"
    
    # Basic validation for OpenAI API key format (more flexible)
    if [[ ! "$key" =~ ^sk-[a-zA-Z0-9_-]{20,}$ ]]; then
        log_action "ERROR" "Invalid OpenAI API key format. Expected: sk-[20+ alphanumeric/underscore/hyphen chars]"
        return 1
    fi
    
    log_action "INFO" "✅ API key format validated"
    return 0
}

# Test API key functionality (without exposing the key)
test_api_key_functionality() {
    local key="$1"
    
    log_action "INFO" "Testing API key functionality..."
    
    # Test with OpenAI API
    local test_response
    test_response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $key" \
        -H "Content-Type: application/json" \
        -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}],"max_tokens":1}' \
        https://api.openai.com/v1/chat/completions 2>/dev/null || echo "000")
    
    local http_code
    http_code=$(echo "$test_response" | tail -n1)
    
    case "$http_code" in
        200|400) # 200 = success, 400 = bad request but auth worked
            log_action "INFO" "✅ API key authentication successful"
            return 0
            ;;
        401)
            log_action "ERROR" "❌ API key authentication failed (401 Unauthorized)"
            return 1
            ;;
        403)
            log_action "ERROR" "❌ API key authentication failed (403 Forbidden)"
            return 1
            ;;
        429)
            log_action "WARN" "⚠️  Rate limited (429) - API key appears valid but usage limited"
            return 0
            ;;
        *)
            log_action "WARN" "⚠️  Could not verify API key (HTTP $http_code) - proceeding anyway"
            return 0
            ;;
    esac
}

# Create or update secret in Google Secret Manager
create_secret() {
    local key="$1"
    
    log_action "INFO" "Creating/updating secret in Google Secret Manager..."
    
    # Check if secret already exists
    if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
        log_action "INFO" "Secret already exists, creating new version..."
        
        # Add new version
        echo -n "$key" | gcloud secrets versions add "$SECRET_NAME" \
            --project="$PROJECT_ID" \
            --data-file=- &>/dev/null || {
            log_action "ERROR" "Failed to add new secret version"
            return 1
        }
    else
        log_action "INFO" "Creating new secret..."
        
        # Create new secret
        echo -n "$key" | gcloud secrets create "$SECRET_NAME" \
            --project="$PROJECT_ID" \
            --replication-policy="automatic" \
            --data-file=- \
            --labels="service=openai,system=claude-code" &>/dev/null || {
            log_action "ERROR" "Failed to create secret"
            return 1
        }
    fi
    
    log_action "INFO" "✅ Secret stored successfully"
    return 0
}

# Verify secret storage and retrieval
verify_secret_storage() {
    log_action "INFO" "Verifying secret storage and retrieval..."
    
    # Test retrieval
    local retrieved_key
    retrieved_key=$(gcloud secrets versions access latest \
        --secret="$SECRET_NAME" \
        --project="$PROJECT_ID" 2>/dev/null || echo "")
    
    if [[ -z "$retrieved_key" ]]; then
        log_action "ERROR" "Failed to retrieve stored secret"
        return 1
    fi
    
    # Verify it matches (without logging the actual key)
    if [[ "$retrieved_key" == "$API_KEY" ]]; then
        log_action "INFO" "✅ Secret retrieval verification successful"
        return 0
    else
        log_action "ERROR" "❌ Retrieved secret does not match stored value"
        return 1
    fi
}

# Main execution function
main() {
    echo -e "${BLUE}"
    echo "🔐 SECURE OPENAI API KEY STORAGE"
    echo "================================="
    echo -e "${NC}"
    
    # Input validation
    if [[ $# -ne 1 ]]; then
        echo -e "${RED}Usage: $0 <OPENAI_API_KEY>${NC}"
        echo "Example: $0 sk-1234567890abcdef..."
        echo ""
        echo "Security note: API key will not be logged or exposed"
        exit 1
    fi
    
    API_KEY="$1"
    
    # Execute validation and storage pipeline
    log_action "INFO" "Starting secure API key storage process..."
    
    # Step 1: Authentication validation
    if ! validate_gcloud_auth; then
        log_action "ERROR" "❌ Authentication validation failed"
        exit 1
    fi
    
    # Step 2: Project access validation
    if ! validate_project_access; then
        log_action "ERROR" "❌ Project access validation failed"
        exit 1
    fi
    
    # Step 3: API key format validation
    if ! validate_api_key_format "$API_KEY"; then
        log_action "ERROR" "❌ API key format validation failed"
        exit 1
    fi
    
    # Step 4: API key functionality test
    if ! test_api_key_functionality "$API_KEY"; then
        log_action "WARN" "⚠️  API key functionality test inconclusive"
        echo -e "${YELLOW}Continue anyway? (y/N): ${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_action "INFO" "Operation cancelled by user"
            exit 0
        fi
    fi
    
    # Step 5: Store secret
    if ! create_secret "$API_KEY"; then
        log_action "ERROR" "❌ Secret storage failed"
        exit 1
    fi
    
    # Step 6: Verify storage
    if ! verify_secret_storage; then
        log_action "ERROR" "❌ Secret verification failed"
        exit 1
    fi
    
    # Success summary
    echo -e "${GREEN}"
    echo "✅ SUCCESS: OpenAI API key stored securely"
    echo "=================================="
    echo "• Project: $PROJECT_ID"
    echo "• Secret: $SECRET_NAME"
    echo "• Status: Available for Claude Code system"
    echo "• Next: Update session_start.py to load OPENAI_API_KEY"
    echo -e "${NC}"
    
    log_action "INFO" "✅ Secure storage process completed successfully"
}

# Execute main function with all arguments
main "$@"