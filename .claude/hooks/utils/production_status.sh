#!/bin/bash
# Production Environment Status Check
# ===================================
#
# Quick status check and control script for Claude Code production environment

set -euo pipefail

CLAUDE_DIR="/Users/sam/.claude"
HOOKS_UTILS="/Users/sam/claude-code-hooks-mastery/.claude/hooks/utils"

show_status() {
    echo "🚀 Claude Code Production Environment Status"
    echo "============================================="
    
    # Check if production environment is loaded
    if [[ "${HOOK_WRAPPER_DEBUG:-1}" == "0" ]]; then
        echo "✅ Production mode: ACTIVE"
    else
        echo "⚠️  Production mode: NOT ACTIVE"
    fi
    
    # Check cache status
    cache_file="${CLAUDE_DIR}/cache/credentials_cache.json"
    if [[ -f "$cache_file" ]]; then
        cache_age=$(find "$cache_file" -mmin +60 2>/dev/null && echo "old" || echo "fresh")
        cache_size=$(stat -f%z "$cache_file" 2>/dev/null || echo "unknown")
        echo "✅ Credential cache: EXISTS (${cache_size} bytes, ${cache_age})"
    else
        echo "❌ Credential cache: MISSING"
    fi
    
    # Check directories
    if [[ -d "${CLAUDE_DIR}/cache" ]]; then
        echo "✅ Cache directory: EXISTS"
    else
        echo "❌ Cache directory: MISSING"
    fi
    
    if [[ -d "${CLAUDE_DIR}/logs/wrapper" ]]; then
        echo "✅ Wrapper logs: EXISTS"
    else
        echo "❌ Wrapper logs: MISSING"
    fi
    
    # Check environment variables
    echo ""
    echo "📊 Environment Variables:"
    echo "   HOOK_WRAPPER_DEBUG: ${HOOK_WRAPPER_DEBUG:-not set}"
    echo "   HOOK_WRAPPER_METRICS: ${HOOK_WRAPPER_METRICS:-not set}"
    echo "   CREDENTIAL_PROVIDER_DEBUG: ${CREDENTIAL_PROVIDER_DEBUG:-not set}"
    echo "   PYTHONOPTIMIZE: ${PYTHONOPTIMIZE:-not set}"
    
    # Performance quick test
    echo ""
    echo "⚡ Quick Performance Test:"
    cd "$HOOKS_UTILS"
    
    start_time=$(python3 -c "import time; print(time.time())")
    if python3 -c "from credential_provider import CredentialProvider; CredentialProvider().get_api_key('OPENAI_API_KEY')" >/dev/null 2>&1; then
        end_time=$(python3 -c "import time; print(time.time())")
        exec_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0.000")
        echo "   Cache access: ${exec_time}s"
    else
        echo "   Cache access: FAILED"
    fi
}

enable_production() {
    echo "🔧 Enabling production mode..."
    source "${CLAUDE_DIR}/.env.production"
    echo "✅ Production environment loaded"
}

disable_production() {
    echo "🔧 Disabling production mode (enabling debug)..."
    export HOOK_WRAPPER_DEBUG=1
    export HOOK_WRAPPER_METRICS=1
    export CREDENTIAL_PROVIDER_DEBUG=1
    unset PYTHONOPTIMIZE
    echo "✅ Debug mode enabled"
}

warm_cache() {
    echo "🔥 Warming credential cache..."
    cd "$HOOKS_UTILS"
    if uv run warm_cache.py; then
        echo "✅ Cache warmed successfully"
    else
        echo "❌ Cache warming failed"
    fi
}

run_performance_test() {
    echo "🏃 Running performance validation..."
    cd "$HOOKS_UTILS"
    if ./performance_test.py; then
        echo "✅ Performance test completed"
    else
        echo "❌ Performance test failed"
    fi
}

show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  status      Show current production environment status (default)"
    echo "  enable      Enable production mode"
    echo "  disable     Disable production mode (enable debug)"
    echo "  warm        Warm credential cache"
    echo "  test        Run performance validation"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Show status"
    echo "  $0 enable            # Enable production mode"
    echo "  $0 warm              # Warm cache"
    echo "  $0 test              # Run performance test"
}

# Main command processing
case "${1:-status}" in
    "status")
        show_status
        ;;
    "enable")
        enable_production
        show_status
        ;;
    "disable")
        disable_production
        show_status
        ;;
    "warm")
        warm_cache
        ;;
    "test")
        run_performance_test
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_help
        exit 1
        ;;
esac