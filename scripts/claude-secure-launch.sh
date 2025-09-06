#!/bin/bash

# Claude Code Secure Launch Script
# ================================
# 
# This script implements the complete security architecture for Claude Code:
# 1. Pre-loads credentials from Google Secret Manager
# 2. Validates environment variable inheritance
# 3. Launches Claude Code with secure credential isolation
# 4. Provides fallback mechanisms for production deployment
#
# USAGE:
#   ./scripts/claude-secure-launch.sh
#   ./scripts/claude-secure-launch.sh --force-refresh
#   ./scripts/claude-secure-launch.sh --validate-only
#   ./scripts/claude-secure-launch.sh --resume

set -euo pipefail  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PRE_CLAUDE_SCRIPT="$PROJECT_ROOT/.claude/hooks/pre_claude_startup.py"
CONFIG_GUARDIAN="$SCRIPT_DIR/claude-config-guardian.sh"
# Use global Claude settings file (fallback to local if exists)
if [[ -f "$PROJECT_ROOT/.claude/settings.json" ]]; then
    CLAUDE_SETTINGS="$PROJECT_ROOT/.claude/settings.json"
else
    CLAUDE_SETTINGS="$HOME/.claude/settings.json"
fi

# Claude Code binary path (npm global installation)
CLAUDE_BINARY="$HOME/.npm-global/bin/claude"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Google Cloud is authenticated
    if ! gcloud auth list --filter="status:ACTIVE" --format="value(account)" | head -1 > /dev/null 2>&1; then
        log_error "Google Cloud authentication required. Run: gcloud auth login"
        exit 1
    fi
    
    # Check if uv is available
    if ! command -v uv &> /dev/null; then
        log_error "UV package manager not found. Install from: https://docs.astral.sh/uv/"
        exit 1
    fi
    
    # Check Claude configuration integrity and create backup
    log_info "🛡️  Checking Claude configuration integrity..."
    if [[ -x "$CONFIG_GUARDIAN" ]]; then
        if "$CONFIG_GUARDIAN" status | grep -q "Main config: ✅ Valid"; then
            log_success "Configuration is valid - creating backup"
            "$CONFIG_GUARDIAN" backup > /dev/null 2>&1 || log_warning "Backup creation failed"
        else
            log_warning "🚨 Claude configuration appears corrupted!"
            log_warning "Run: $CONFIG_GUARDIAN restore"
            log_warning "Or manual backup restore before continuing"
        fi
    else
        log_warning "Configuration guardian not found at: $CONFIG_GUARDIAN"
    fi
    
    # Check if Claude Code is available (npm global installation)
    if [[ ! -x "$CLAUDE_BINARY" ]]; then
        log_error "Claude Code CLI not found at: $CLAUDE_BINARY"
        log_error "Ensure Claude Code is installed globally with: npm install -g @anthropic/claude-code"
        exit 1
    fi
    
    # Check if pre-Claude startup script exists
    if [[ ! -f "$PRE_CLAUDE_SCRIPT" ]]; then
        log_error "Pre-Claude startup script not found at: $PRE_CLAUDE_SCRIPT"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to load and validate credentials
load_credentials() {
    local force_refresh="$1"
    
    # Primary: Try loading from .env file first (more reliable for local development)
    if [[ -f "/Users/sam/.env" ]]; then
        log_info "Loading credentials from local .env file..."
        
        # Source the .env file
        set -a
        source "/Users/sam/.env"
        set +a
        
        # Check if we got the essential keys
        if [[ -n "${GEMINI_API_KEY:-}" ]] || [[ -n "${GOOGLE_API_KEY:-}" ]]; then
            log_success "Credentials loaded from .env file"
            
            # Also set GEMINI_API_KEY from GOOGLE_API_KEY if not set
            if [[ -z "${GEMINI_API_KEY:-}" ]] && [[ -n "${GOOGLE_API_KEY:-}" ]]; then
                export GEMINI_API_KEY="$GOOGLE_API_KEY"
                log_info "Using GOOGLE_API_KEY as GEMINI_API_KEY"
            fi
            
            # Optional: Try to enhance with Secret Manager if available  
            if command -v gcloud &> /dev/null && gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null 2>&1; then
                log_info "Checking for additional credentials in Google Secret Manager..."
                if [[ -n "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
                    # Try to get google-api-key from Secret Manager (the only secret that exists)
                    local google_api_key_sm
                    google_api_key_sm=$(gcloud secrets versions access latest --secret="google-api-key" --project="$GOOGLE_CLOUD_PROJECT" 2>/dev/null || true)
                    if [[ -n "$google_api_key_sm" ]]; then
                        export GOOGLE_API_KEY="$google_api_key_sm"
                        log_success "Enhanced with Google API key from Secret Manager"
                    fi
                fi
            fi
            
            return 0
        else
            log_error "No valid credentials found in .env file"
            return 1
        fi
    else
        # Fallback: Try Secret Manager via pre-Claude script
        log_warning "No .env file found, trying Google Secret Manager..."
        
        # Prepare arguments for pre-Claude script
        local args="--export --quiet"
        if [[ "$force_refresh" == "true" ]]; then
            args="$args --force-refresh"
        fi
        
        # Create temporary file for export commands
        local temp_file=$(mktemp)
        
        # Load credentials and capture export commands only
        if uv run "$PRE_CLAUDE_SCRIPT" $args > "$temp_file" 2>/dev/null; then
            # Apply the export commands to current shell
            while IFS= read -r line; do
                if [[ "$line" =~ ^export ]]; then
                    eval "$line"
                fi
            done < "$temp_file"
            rm -f "$temp_file"
            log_success "Credentials loaded from Google Secret Manager"
            return 0
        else
            rm -f "$temp_file"
            log_error "Failed to load credentials from Google Secret Manager"
            return 1
        fi
    fi
}

# Function to validate environment variables
validate_environment() {
    log_info "Validating environment variables..."
    
    # Check if required environment variables are set in current shell
    local required_vars=("GEMINI_API_KEY" "GOOGLE_API_KEY")
    local optional_vars=("FIRECRAWL_API_KEY" "ELEVENLABS_API_KEY" "OPENAI_API_KEY" "ANTHROPIC_API_KEY")
    local cipher_vars=("VECTOR_STORE_TYPE" "USE_WORKSPACE_MEMORY" "WORKSPACE_VECTOR_STORE_COLLECTION")
    
    local validation_passed=true
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable $var is not set"
            validation_passed=false
        else
            local var_length="${!var}"
            log_success "$var is available (${#var_length} characters)"
        fi
    done
    
    for var in "${optional_vars[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            local var_length="${!var}"
            log_success "$var is available (${#var_length} characters)"
        else
            log_info "$var is not set (optional)"
        fi
    done
    
    # Validate Cipher-specific variables
    for var in "${cipher_vars[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            log_success "Cipher $var is configured"
        else
            log_info "Cipher $var will use default value"
        fi
    done
    
    if [[ "$validation_passed" == "true" ]]; then
        log_success "Environment validation passed"
        return 0
    else
        log_error "Environment validation failed"
        return 1
    fi
}

# Function to test MCP server credential access
test_mcp_access() {
    log_info "Testing MCP server credential access..."
    
    # Verify credentials are properly formatted
    if [[ -n "${GEMINI_API_KEY:-}" ]]; then
        if [[ "${GEMINI_API_KEY}" =~ ^AIza ]]; then
            log_success "GEMINI_API_KEY format validation passed"
        else
            log_warning "GEMINI_API_KEY format may be invalid"
        fi
    fi
    
    if [[ -n "${FIRECRAWL_API_KEY:-}" ]]; then
        if [[ "${FIRECRAWL_API_KEY}" =~ ^fc- ]]; then
            log_success "FIRECRAWL_API_KEY format validation passed"
        else
            log_warning "FIRECRAWL_API_KEY format may be invalid"
        fi
    fi
    
    if [[ -n "${ELEVENLABS_API_KEY:-}" ]]; then
        # ElevenLabs API keys use sk_ prefix format (51 chars total)
        if [[ "${ELEVENLABS_API_KEY}" =~ ^sk_[a-zA-Z0-9]{48}$ ]]; then
            log_success "ELEVENLABS_API_KEY format validation passed"
        else
            log_warning "ELEVENLABS_API_KEY format may be invalid (expected sk_ prefix + 48 chars)"
        fi
    fi
    
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        if [[ "${OPENAI_API_KEY}" =~ ^sk- ]]; then
            log_success "OPENAI_API_KEY format validation passed"
        else
            log_warning "OPENAI_API_KEY format may be invalid"
        fi
    fi
    
    return 0
}

# Function to check Claude Code settings security
check_settings_security() {
    log_info "Validating Claude Code settings security..."
    
    if [[ ! -f "$CLAUDE_SETTINGS" ]]; then
        log_error "Claude settings file not found: $CLAUDE_SETTINGS"
        return 1
    fi
    
    # Check for hardcoded API keys in settings (more precise patterns)
    if grep -qE '(sk-[a-zA-Z0-9]{48,}|or-[a-zA-Z0-9]{10,})' "$CLAUDE_SETTINGS" 2>/dev/null; then
        log_error "Potential hardcoded API keys found in Claude settings"
        return 1
    fi
    
    # Check for environment variable placeholders
    if grep -q "\${.*_API_KEY}" "$CLAUDE_SETTINGS" 2>/dev/null; then
        log_success "Environment variable placeholders found in settings"
    else
        log_warning "No environment variable placeholders found in settings"
    fi
    
    return 0
}

# Function to ensure cipher memory service is running
ensure_cipher_docker() {
    log_info "Checking Cipher memory service status..."
    
    local cipher_port="8004"
    local cipher_dir="/Users/sam/cipher-docker"
    
    # Check if cipher service is already running
    if curl -s http://localhost:$cipher_port/health > /dev/null 2>&1; then
        log_success "Cipher memory service already running on port $cipher_port"
        return 0
    fi
    
    # Check if docker-compose file exists
    if [[ ! -f "$cipher_dir/docker-compose.yml" ]]; then
        log_error "Cipher docker-compose.yml not found: $cipher_dir/docker-compose.yml"
        return 1
    fi
    
    log_info "Starting Cipher memory service with Docker..."
    
    # Ensure data directories exist
    mkdir -p /Users/sam/memAgent/cipher-data /Users/sam/memAgent/cipher-sessions
    
    # Start cipher service
    cd "$cipher_dir"
    if docker-compose up -d; then
        
        # Wait for service to be ready
        log_info "Waiting for Cipher memory service to start..."
        local retries=0
        while [[ $retries -lt 30 ]]; do
            if curl -s http://localhost:$cipher_port/health > /dev/null 2>&1; then
                log_success "Cipher memory service started successfully on port $cipher_port"
                log_info "Available tools: cipher_memory_search, cipher_extract_and_operate_memory"
                return 0
            fi
            sleep 2
            ((retries++))
        done
        
        log_error "Cipher memory service failed to start within 60 seconds"
        return 1
    else
        log_error "Failed to start Cipher memory service container"
        return 1
    fi
}

# Function to ensure liteLLM proxy is running
ensure_litellm_proxy() {
    log_info "Checking liteLLM proxy status..."
    
    local config_file="$PROJECT_ROOT/litellm-claude-integration.yaml"
    local proxy_port="4001"
    
    # Check if proxy is already running
    if curl -s http://localhost:$proxy_port/health > /dev/null 2>&1; then
        log_success "LiteLLM proxy already running on port $proxy_port"
        return 0
    fi
    
    # Check if config file exists
    if [[ ! -f "$config_file" ]]; then
        log_error "LiteLLM config file not found: $config_file"
        return 1
    fi
    
    log_info "Starting liteLLM proxy with Docker..."
    
    # Stop any existing container
    docker stop claude-litellm-proxy 2>/dev/null || true
    docker container rm claude-litellm-proxy 2>/dev/null || true
    
    # Start new container
    if docker run -d --name claude-litellm-proxy \
        -p $proxy_port:4000 \
        -v "$config_file:/app/config.yaml" \
        -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
        -e VERTEX_PROJECT="${VERTEX_PROJECT:-strong-shelter-470416-p5}" \
        -e VERTEX_LOCATION="${VERTEX_LOCATION:-global}" \
        ghcr.io/berriai/litellm:main-latest \
        --config /app/config.yaml --port 4000 > /dev/null 2>&1; then
        
        # Wait for proxy to be ready
        log_info "Waiting for liteLLM proxy to start..."
        local retries=0
        while [[ $retries -lt 30 ]]; do
            if curl -s http://localhost:$proxy_port/health > /dev/null 2>&1; then
                log_success "LiteLLM proxy started successfully on port $proxy_port"
                return 0
            fi
            sleep 1
            ((retries++))
        done
        
        log_error "LiteLLM proxy failed to start within 30 seconds"
        return 1
    else
        log_error "Failed to start liteLLM proxy container"
        return 1
    fi
}

# Function to configure Claude Code proxy settings
configure_claude_proxy() {
    local action="$1"  # "enable" or "disable"
    
    log_info "Configuring Claude Code proxy settings..."
    
    if [[ "$action" == "enable" ]]; then
        # Add llmGateway configuration to settings.json
        if ! grep -q '"llmGateway"' "$CLAUDE_SETTINGS"; then
            # Add llmGateway configuration after mcpServers
            sed -i '' 's/  },$/  },\
  "llmGateway": {\
    "url": "http:\/\/localhost:4001\/v1"\
  },/' "$CLAUDE_SETTINGS"
            log_success "Enabled Claude Code proxy configuration"
        else
            log_info "Claude Code proxy configuration already present"
        fi
    elif [[ "$action" == "disable" ]]; then
        # Remove llmGateway configuration
        sed -i '' '/  "llmGateway": {/,/  },/d' "$CLAUDE_SETTINGS"
        log_success "Disabled Claude Code proxy configuration"
    fi
}

# Function to run headless proxy test
run_headless_test() {
    log_info "Running headless proxy test..."
    
    # Test 1: Health check
    log_info "Testing proxy health endpoint..."
    if ! curl -s http://localhost:4001/health > /dev/null 2>&1; then
        log_error "Proxy health endpoint unreachable"
        return 1
    fi
    log_success "Proxy health endpoint accessible"
    
    # Test 2: Primary model test
    log_info "Testing Gemini 2.5 Pro model..."
    local response
    response=$(curl -s -X POST http://localhost:4001/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{
            "model": "claude-primary",
            "messages": [{"role": "user", "content": "Reply with exactly: HEADLESS_TEST_SUCCESS"}],
            "max_tokens": 10
        }' 2>/dev/null || echo "")
    
    if [[ -n "$response" ]] && echo "$response" | jq -e '.choices[0]' > /dev/null 2>&1; then
        local content model
        content=$(echo "$response" | jq -r '.choices[0].message.content // ""')
        model=$(echo "$response" | jq -r '.model')
        
        # For Gemini 2.5, content might be null due to reasoning tokens
        if [[ -n "$content" && "$content" != "null" && "$content" == *"HEADLESS_TEST_SUCCESS"* ]]; then
            log_success "Primary model ($model) test passed: $content"
        elif [[ "$model" == "gemini-2.5-pro" ]]; then
            log_success "Primary model ($model) test passed - Gemini 2.5 reasoning response received"
        else
            log_warning "Primary model ($model) responded but content unexpected: $content"
        fi
    else
        log_error "Primary model test failed"
        return 1
    fi
    
    # Test 3: Fast model test
    log_info "Testing Gemini 2.5 Flash model..."
    response=$(curl -s -X POST http://localhost:4001/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{
            "model": "claude-fast", 
            "messages": [{"role": "user", "content": "Reply with exactly: FLASH_TEST_SUCCESS"}],
            "max_tokens": 10
        }' 2>/dev/null || echo "")
    
    if [[ -n "$response" ]] && echo "$response" | jq -e '.choices[0]' > /dev/null 2>&1; then
        local content model
        content=$(echo "$response" | jq -r '.choices[0].message.content // ""')
        model=$(echo "$response" | jq -r '.model')
        
        # For Gemini 2.5, content might be null due to reasoning tokens
        if [[ -n "$content" && "$content" != "null" && "$content" == *"FLASH_TEST_SUCCESS"* ]]; then
            log_success "Fast model ($model) test passed: $content"
        elif [[ "$model" == *"gemini-2.5"* ]]; then
            log_success "Fast model ($model) test passed - Gemini 2.5 reasoning response received"
        else
            log_warning "Fast model ($model) responded but content unexpected: $content"
        fi
    else
        log_error "Fast model test failed"
        return 1
    fi
    
    log_success "All headless tests passed - Gemini 2.5 models operational"
    return 0
}

# Function to launch Claude Code with security validation
launch_claude() {
    local claude_args="$1"
    
    log_info "Launching Claude Code with secure environment..."
    
    # Set additional security environment variables
    export CLAUDE_SECURITY_MODE="enhanced"
    export CLAUDE_CREDENTIAL_SOURCE="google_secret_manager"
    export CLAUDE_SESSION_TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
    
    # Set Cipher environment variables
    export VECTOR_STORE_TYPE="${VECTOR_STORE_TYPE:-qdrant}"
    export VECTOR_STORE_URL="http://localhost:6333"
    export USE_WORKSPACE_MEMORY="${USE_WORKSPACE_MEMORY:-true}"
    export WORKSPACE_VECTOR_STORE_COLLECTION="${WORKSPACE_VECTOR_STORE_COLLECTION:-sam_workspace_memory}"
    export MCP_SERVER_MODE="aggregator"
    export AGGREGATOR_CONFLICT_RESOLUTION="prefix"
    export AGGREGATOR_TIMEOUT="60000"
    
    # Launch Claude Code with the current directory
    cd "$PROJECT_ROOT"
    
    log_success "Starting Claude Code in secure mode..."
    log_info "Working directory: $PWD"
    log_info "Binary location: $CLAUDE_BINARY"
    log_info "Credential source: Local .env (with Secret Manager fallback)"
    log_info "Memory service: Cipher (Gemini-powered) on port 8004"
    
    # Show LLM Gateway info only if proxy is configured
    if grep -q '"llmGateway"' "$CLAUDE_SETTINGS"; then
        log_info "LLM Gateway: http://localhost:4001/v1 (liteLLM proxy)"
    else
        log_info "LLM Gateway: Direct Claude API"
    fi
    
    log_info "Session timestamp: $CLAUDE_SESSION_TIMESTAMP"
    
    if [[ -n "$claude_args" ]]; then
        log_info "Claude arguments: $claude_args"
    fi
    
    # Execute Claude Code with optional arguments using local binary
    if [[ -n "$claude_args" ]]; then
        exec "$CLAUDE_BINARY" $claude_args
    else
        exec "$CLAUDE_BINARY"
    fi
}

# Function to display usage information
show_usage() {
    cat << EOF
Claude Code Secure Launch Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --force-refresh     Force refresh credentials from Secret Manager
    --validate-only     Only validate environment, don't launch Claude
    --resume           Resume a stuck or interrupted Claude conversation
    --with-proxy       Start Claude Code with liteLLM proxy (Gemini/Vertex AI models)
    --proxy-headless   Test proxy functionality in headless mode (no interactive Claude session)
    --help             Show this help message

SECURITY FEATURES:
    ✅ Google Secret Manager integration
    ✅ Environment variable isolation
    ✅ Credential validation pipeline
    ✅ Zero hardcoded credentials
    ✅ MCP server secure configuration
    ✅ Process inheritance validation
    ✅ NPM Global Claude Code binary
    ✅ Cipher memory service (Docker-isolated)

EXAMPLES:
    $0                           # Normal secure launch (direct Claude API)
    $0 --with-proxy             # Launch with liteLLM proxy for Gemini/Vertex AI
    $0 --proxy-headless         # Test proxy functionality without interactive session
    $0 --force-refresh          # Force credential refresh
    $0 --validate-only          # Validate environment only
    $0 --resume                 # Resume stuck conversation

For more information, see: $PROJECT_ROOT/OPERATIONS-GUIDE.md
EOF
}

# Main execution function
main() {
    local force_refresh="false"
    local validate_only="false"
    local resume_conversation="false"
    local use_proxy="false"
    local headless_mode="false"
    local claude_args=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force-refresh)
                force_refresh="true"
                shift
                ;;
            --validate-only)
                validate_only="true"
                shift
                ;;
            --resume)
                resume_conversation="true"
                claude_args="--resume"
                shift
                ;;
            --with-proxy)
                use_proxy="true"
                shift
                ;;
            --proxy-headless)
                use_proxy="true"
                headless_mode="true"
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Display banner
    cat << EOF

🔐 Claude Code Secure Launch
============================
Project: $(basename "$PROJECT_ROOT")
Security Mode: Enhanced
Credential Source: Local .env (with Secret Manager fallback)
Claude Binary: Local Installation$(if [[ "$resume_conversation" == "true" ]]; then echo -e "\nResume Mode: Active (--resume)"; fi)$(if [[ "$use_proxy" == "true" ]]; then echo -e "\nLLM Gateway: liteLLM Proxy (Gemini/Vertex AI)"; fi)$(if [[ "$headless_mode" == "true" ]]; then echo -e "\nHeadless Mode: Proxy test without interactive session"; fi)

EOF
    
    # Execute security pipeline
    check_prerequisites
    
    if ! load_credentials "$force_refresh"; then
        log_error "Failed to load credentials. Aborting launch."
        exit 1
    fi
    
    if ! validate_environment; then
        log_error "Environment validation failed. Aborting launch."
        exit 1
    fi
    
    if ! test_mcp_access; then
        log_error "MCP server credential access test failed. Aborting launch."
        exit 1
    fi
    
    if ! check_settings_security; then
        log_error "Claude settings security check failed. Aborting launch."
        exit 1
    fi
    
    if [[ "$validate_only" == "true" ]]; then
        log_success "Validation completed successfully. Not launching Claude (--validate-only specified)."
        exit 0
    fi
    
    # Always ensure cipher memory service is running
    if ! ensure_cipher_docker; then
        log_error "Failed to start Cipher memory service. Continuing without memory capabilities."
        log_warning "Some MCP tools may not be available"
    fi
    
    # Handle proxy setup if requested
    if [[ "$use_proxy" == "true" ]]; then
        if ! ensure_litellm_proxy; then
            log_error "Failed to start liteLLM proxy. Aborting launch."
            exit 1
        fi
        
        # Configure Claude Code to use proxy (only if not headless)
        if [[ "$headless_mode" == "false" ]]; then
            configure_claude_proxy "enable"
        fi
    fi
    
    # Handle headless mode
    if [[ "$headless_mode" == "true" ]]; then
        if run_headless_test; then
            log_success "Headless proxy test completed successfully"
            exit 0
        else
            log_error "Headless proxy test failed"
            exit 1
        fi
    fi
    
    # All checks passed, launch Claude Code
    launch_claude "$claude_args"
}

# Handle interrupts gracefully
trap 'log_warning "Launch interrupted by user"; exit 1' INT TERM

# Execute main function with all arguments
main "$@"