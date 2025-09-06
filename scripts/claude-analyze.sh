#!/bin/bash

# Claude Code Headless Analysis Script
# =====================================
# 
# Wrapper script for analyzing codebases using Claude in headless mode
# with LiteLLM proxy routing to Gemini 2.5 models
#
# USAGE:
#   ./scripts/claude-analyze.sh "file_or_directory" "analysis prompt"
#   ./scripts/claude-analyze.sh --all "full project analysis prompt"
#   ./scripts/claude-analyze.sh --test
#
# EXAMPLES:
#   ./scripts/claude-analyze.sh "src/" "Analyze the architecture and identify patterns"
#   ./scripts/claude-analyze.sh "src/main.py" "Explain this file's purpose and structure"
#   ./scripts/claude-analyze.sh --all "Give me an overview of this entire project"

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLAUDE_LAUNCH_SCRIPT="$SCRIPT_DIR/claude-secure-launch.sh"

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

# Function to show usage
show_usage() {
    cat << EOF
Claude Code Headless Analysis Tool

USAGE:
    $(basename "$0") [OPTIONS] <target> <prompt>
    $(basename "$0") --all <prompt>
    $(basename "$0") --test

OPTIONS:
    <target>        File or directory to analyze
    <prompt>        Analysis prompt/question
    --all           Analyze entire project
    --test          Run test analysis
    --model MODEL   Specify model (gemini-2.5-pro, gemini-2.5-flash)
    --help          Show this help message

EXAMPLES:
    $(basename "$0") "src/" "Analyze the architecture"
    $(basename "$0") "src/main.py" "Explain this file"
    $(basename "$0") --all "Project overview"
    $(basename "$0") --model gemini-2.5-flash "src/" "Quick analysis"

NOTE:
    This script uses Claude in headless mode with LiteLLM proxy
    routing to Gemini 2.5 models for large context analysis.
EOF
}

# Function to prepare file content for analysis
prepare_file_content() {
    local target="$1"
    local content=""
    
    if [[ -f "$target" ]]; then
        # Single file
        log_info "Preparing single file: $target"
        content=$(cat "$target" 2>/dev/null || echo "Error reading file")
    elif [[ -d "$target" ]]; then
        # Directory
        log_info "Preparing directory content: $target"
        # Find all relevant files (excluding common non-code files)
        local files=$(find "$target" -type f \
            ! -path "*/node_modules/*" \
            ! -path "*/.git/*" \
            ! -path "*/dist/*" \
            ! -path "*/build/*" \
            ! -name "*.log" \
            ! -name "*.pdf" \
            ! -name "*.jpg" \
            ! -name "*.png" \
            ! -name "*.gif" \
            ! -name "*.ico" \
            2>/dev/null | head -100)  # Limit to first 100 files
        
        for file in $files; do
            content+="=== File: $file ===\n"
            content+=$(cat "$file" 2>/dev/null || echo "Error reading file")
            content+="\n\n"
        done
    else
        log_error "Target not found: $target"
        return 1
    fi
    
    echo "$content"
}

# Function to run headless analysis
run_analysis() {
    local target="$1"
    local prompt="$2"
    local model="${3:-gemini-2.5-pro}"
    
    log_info "Starting Claude headless analysis..."
    log_info "Target: $target"
    log_info "Model: $model (via LiteLLM proxy)"
    
    # Prepare analysis payload
    local analysis_request=""
    
    if [[ "$target" == "--all" ]]; then
        # Analyze entire project
        analysis_request="Analyze the entire project in $PROJECT_ROOT:\n\n$prompt"
        target="$PROJECT_ROOT"
    else
        # Prepare file/directory content
        local content=$(prepare_file_content "$target")
        if [[ $? -ne 0 ]]; then
            return 1
        fi
        
        analysis_request="Analyze the following code:\n\n$content\n\n$prompt"
    fi
    
    # Create temporary file for analysis request
    local temp_file=$(mktemp)
    echo "$analysis_request" > "$temp_file"
    
    # Run Claude in headless mode with proxy
    log_info "Executing analysis via LiteLLM proxy..."
    
    # Use the secure launch script in headless mode
    "$CLAUDE_LAUNCH_SCRIPT" --proxy-headless 2>&1 | tee -a "$temp_file.log"
    
    local exit_code=$?
    
    # Clean up
    rm -f "$temp_file" "$temp_file.log"
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Analysis completed successfully"
    else
        log_error "Analysis failed with exit code: $exit_code"
    fi
    
    return $exit_code
}

# Function to run test analysis
run_test() {
    log_info "Running test analysis..."
    
    # Simple test prompt
    local test_prompt="Test analysis: What is 2+2?"
    
    # Run headless test via proxy
    "$CLAUDE_LAUNCH_SCRIPT" --proxy-headless
    
    if [[ $? -eq 0 ]]; then
        log_success "Test analysis passed"
        return 0
    else
        log_error "Test analysis failed"
        return 1
    fi
}

# Main execution
main() {
    # Check if secure launch script exists
    if [[ ! -f "$CLAUDE_LAUNCH_SCRIPT" ]]; then
        log_error "Claude secure launch script not found: $CLAUDE_LAUNCH_SCRIPT"
        exit 1
    fi
    
    # Parse arguments
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 0
    fi
    
    case "$1" in
        --help|-h)
            show_usage
            exit 0
            ;;
        --test)
            run_test
            exit $?
            ;;
        --all)
            if [[ $# -lt 2 ]]; then
                log_error "Missing prompt for --all option"
                show_usage
                exit 1
            fi
            run_analysis "--all" "$2"
            exit $?
            ;;
        --model)
            if [[ $# -lt 4 ]]; then
                log_error "Missing arguments for --model option"
                show_usage
                exit 1
            fi
            run_analysis "$3" "$4" "$2"
            exit $?
            ;;
        *)
            if [[ $# -lt 2 ]]; then
                log_error "Missing prompt argument"
                show_usage
                exit 1
            fi
            run_analysis "$1" "$2"
            exit $?
            ;;
    esac
}

# Run main function
main "$@"