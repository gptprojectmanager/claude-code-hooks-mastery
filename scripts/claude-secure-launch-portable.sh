#!/bin/bash

# Claude Code Secure Launch Script - PORTABLE VERSION
# ====================================================
# 
# This portable version can be used from any project directory.
# Default hooks location: /Users/sam/claude-code-hooks-mastery
# Override with CLAUDE_HOOKS_HOME environment variable if needed.
#
# USAGE:
#   # Simple usage (uses default location automatically):
#   ./claude-secure-launch-portable.sh
#
#   # Or copy/link the script to any project:
#   ln -s /Users/sam/claude-code-hooks-mastery/scripts/claude-secure-launch-portable.sh ./claude-launch.sh
#   ./claude-launch.sh
#
#   # Override default location if needed:
#   CLAUDE_HOOKS_HOME="/custom/path/to/hooks" ./claude-secure-launch-portable.sh

set -euo pipefail  # Exit on any error

# Configuration - Support both standalone and integrated usage
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set default CLAUDE_HOOKS_HOME if not already set
# This makes the script work out-of-the-box without manual export
export CLAUDE_HOOKS_HOME="${CLAUDE_HOOKS_HOME:-/Users/sam/claude-code-hooks-mastery}"

# Determine HOOKS_HOME - where the hooks infrastructure lives
if [[ -d "$CLAUDE_HOOKS_HOME" ]]; then
    # Use the exported/default CLAUDE_HOOKS_HOME
    HOOKS_HOME="$CLAUDE_HOOKS_HOME"
    if [[ "$CLAUDE_HOOKS_HOME" == "/Users/sam/claude-code-hooks-mastery" ]]; then
        log_source="default location (auto-set)"
    else
        log_source="CLAUDE_HOOKS_HOME environment variable (custom)"
    fi
elif [[ -d "$SCRIPT_DIR/../.claude/hooks" ]]; then
    # Script is inside the hooks repository
    HOOKS_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
    log_source="local repository"
    # Update the export for consistency
    export CLAUDE_HOOKS_HOME="$HOOKS_HOME"
else
    echo "ERROR: Cannot find Claude hooks repository!"
    echo "Default location not found: /Users/sam/claude-code-hooks-mastery"
    echo "Please ensure the repository exists or set a custom path:"
    echo "  export CLAUDE_HOOKS_HOME='/path/to/claude-code-hooks-mastery'"
    exit 1
fi

# Project root is where we're launching from (current directory)
PROJECT_ROOT="$(pwd)"

# Core paths - always from HOOKS_HOME
PRE_CLAUDE_SCRIPT="$HOOKS_HOME/.claude/hooks/pre_claude_startup.py"
LITELLM_CONFIG="$HOOKS_HOME/litellm-claude-integration.yaml"

# Settings priority: local project > global home
if [[ -f "$PROJECT_ROOT/.claude/settings.json" ]]; then
    CLAUDE_SETTINGS="$PROJECT_ROOT/.claude/settings.json"
    settings_source="project-local"
else
    CLAUDE_SETTINGS="$HOME/.claude/settings.json"
    settings_source="global"
fi

# Claude Code binary path (npm global installation)
CLAUDE_BINARY="$HOME/.npm-global/bin/claude"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_config() {
    echo -e "${CYAN}[CONFIG]${NC} $1"
}

# Show configuration
show_configuration() {
    echo -e "\n${CYAN}🔧 Configuration${NC}"
    echo "=================="
    log_config "Hooks Repository: $HOOKS_HOME ($log_source)"
    log_config "Working Directory: $PROJECT_ROOT"
    log_config "Settings File: $CLAUDE_SETTINGS ($settings_source)"
    log_config "Pre-Claude Script: $(if [[ -f "$PRE_CLAUDE_SCRIPT" ]]; then echo "✓ Found"; else echo "✗ Missing"; fi)"
    echo ""
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if hooks repository exists
    if [[ ! -d "$HOOKS_HOME" ]]; then
        log_error "Hooks repository not found at: $HOOKS_HOME"
        exit 1
    fi
    
    # Check if Google Cloud is authenticated
    if ! gcloud auth list --filter="status:ACTIVE" --format="value(account)" | head -1 > /dev/null 2>&1; then
        log_warning "Google Cloud not authenticated. Some features may not work."
        log_info "To authenticate, run: gcloud auth login"
    fi
    
    # Check if uv is available
    if ! command -v uv &> /dev/null; then
        log_error "UV package manager not found. Install from: https://docs.astral.sh/uv/"
        exit 1
    fi
    
    # Check if Claude Code is available
    if [[ ! -x "$CLAUDE_BINARY" ]]; then
        log_error "Claude Code CLI not found at: $CLAUDE_BINARY"
        log_error "Install with: npm install -g @anthropic/claude-code"
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
    local force_refresh="${1:-false}"
    
    # Primary: Try loading from .env file first
    if [[ -f "$HOME/.env" ]]; then
        log_info "Loading credentials from ~/.env file..."
        
        # Source the .env file
        set -a
        source "$HOME/.env"
        set +a
        
        # Check if we got the essential keys
        if [[ -n "${GEMINI_API_KEY:-}" ]] || [[ -n "${GOOGLE_API_KEY:-}" ]]; then
            log_success "Credentials loaded from .env file"
            
            # Also set GEMINI_API_KEY from GOOGLE_API_KEY if not set
            if [[ -z "${GEMINI_API_KEY:-}" ]] && [[ -n "${GOOGLE_API_KEY:-}" ]]; then
                export GEMINI_API_KEY="$GOOGLE_API_KEY"
                log_info "Using GOOGLE_API_KEY as GEMINI_API_KEY"
            fi
            
            return 0
        fi
    fi
    
    # Check project-local .env as well
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        log_info "Loading additional credentials from project .env..."
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
    fi
    
    # Fallback: Try Secret Manager via pre-Claude script
    if [[ -z "${GEMINI_API_KEY:-}" ]]; then
        log_warning "No credentials in .env files, trying Google Secret Manager..."
        
        # Prepare arguments for pre-Claude script
        local args="--export --quiet"
        if [[ "$force_refresh" == "true" ]]; then
            args="$args --force-refresh"
        fi
        
        # Create temporary file for export commands
        local temp_file=$(mktemp)
        
        # Load credentials and capture export commands
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
    
    return 0
}

# Function to validate environment variables
validate_environment() {
    log_info "Validating environment variables..."
    
    local required_vars=("GEMINI_API_KEY" "GOOGLE_API_KEY")
    local optional_vars=("FIRECRAWL_API_KEY" "ELEVENLABS_API_KEY" "OPENAI_API_KEY" "ANTHROPIC_API_KEY")
    
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
    
    if [[ "$validation_passed" == "true" ]]; then
        log_success "Environment validation passed"
        return 0
    else
        return 1
    fi
}

# Function to validate Claude settings security
validate_claude_settings() {
    log_info "Validating Claude Code settings security..."
    
    if [[ ! -f "$CLAUDE_SETTINGS" ]]; then
        log_error "Claude settings file not found: $CLAUDE_SETTINGS"
        return 1
    fi
    
    # Check for hardcoded API keys in settings
    if grep -qE '(sk-[a-zA-Z0-9]{48,}|or-[a-zA-Z0-9]{10,})' "$CLAUDE_SETTINGS" 2>/dev/null; then
        log_error "Potential hardcoded API keys found in Claude settings"
        return 1
    fi
    
    log_success "Claude settings validation passed"
    return 0
}

# Function to launch Claude Code
launch_claude() {
    log_info "Launching Claude Code..."
    
    # Show configuration summary
    log_info "Working Directory: $PROJECT_ROOT"
    log_info "Hooks Repository: $HOOKS_HOME"
    log_info "Settings: $CLAUDE_SETTINGS"
    
    # Export hooks home for any child processes
    export CLAUDE_HOOKS_HOME="$HOOKS_HOME"
    
    # Launch Claude Code from the project directory
    cd "$PROJECT_ROOT"
    
    # Launch with npm global installation
    exec "$CLAUDE_BINARY"
}

# Main execution flow
main() {
    local mode="${1:-launch}"
    
    # Header
    echo -e "\n${CYAN}🔐 Claude Code Secure Launch - Portable${NC}"
    echo "=========================================="
    echo -e "Project: ${GREEN}$(basename "$PROJECT_ROOT")${NC}"
    echo -e "Hooks: ${BLUE}$HOOKS_HOME${NC}"
    echo ""
    
    # Show configuration
    show_configuration
    
    # Check prerequisites
    check_prerequisites
    
    # Load credentials
    if ! load_credentials false; then
        log_error "Failed to load credentials"
        exit 1
    fi
    
    # Validate environment
    if ! validate_environment; then
        log_error "Environment validation failed"
        exit 1
    fi
    
    # Validate Claude settings
    if ! validate_claude_settings; then
        log_warning "Claude settings validation failed (non-critical)"
    fi
    
    case "$mode" in
        --validate-only)
            log_success "Validation complete. Ready to launch Claude Code."
            exit 0
            ;;
        --help)
            cat << EOF

Usage: $(basename "$0") [OPTIONS]

Options:
    --validate-only    Validate configuration without launching Claude
    --force-refresh    Force refresh credentials from Secret Manager
    --help            Show this help message

Environment Variables:
    CLAUDE_HOOKS_HOME   Path to claude-code-hooks-mastery repository
                       (defaults to /Users/sam/claude-code-hooks-mastery)

Examples:
    # Launch from any project directory
    CLAUDE_HOOKS_HOME="/path/to/hooks" ./claude-secure-launch-portable.sh
    
    # Validate configuration only
    ./claude-secure-launch-portable.sh --validate-only

EOF
            exit 0
            ;;
        *)
            # Launch Claude Code
            launch_claude
            ;;
    esac
}

# Run main function with all arguments
main "$@"