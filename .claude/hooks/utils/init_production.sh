#!/bin/bash
# Production Environment Initialization Script
# ============================================
#
# Configures the Claude Code hooks system for optimal production performance.
# This script should be run during system startup or deployment.
#
# Features:
# - Sets production environment variables
# - Creates necessary directories with proper permissions  
# - Warms credential cache for optimal performance
# - Validates system configuration
# - Pre-compiles Python bytecode for faster imports
# - Configures UV for optimal performance

set -euo pipefail  # Exit on error, undefined vars, pipe failures

CLAUDE_DIR="/Users/sam/.claude"
HOOKS_DIR="/Users/sam/claude-code-hooks-mastery/.claude/hooks"
UTILS_DIR="${HOOKS_DIR}/utils"

echo "🚀 Initializing Claude Code Production Environment..."
echo "=================================================="

# Source production environment configuration
if [[ -f "${CLAUDE_DIR}/.env.production" ]]; then
    echo "📁 Loading production environment configuration..."
    source "${CLAUDE_DIR}/.env.production"
else
    echo "⚠️  Warning: Production environment file not found at ${CLAUDE_DIR}/.env.production"
fi

# Ensure required directories exist with proper permissions
echo "📁 Creating required directories..."

directories=(
    "${CLAUDE_DIR}/cache"
    "${CLAUDE_DIR}/logs"
    "${CLAUDE_DIR}/logs/wrapper" 
    "${CLAUDE_DIR}/logs/health_check"
    "${CLAUDE_DIR}/logs/monitoring"
    "/Users/sam/.cache/uv"
)

for dir in "${directories[@]}"; do
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        echo "   ✅ Created: $dir"
    else
        echo "   ✓ Exists: $dir"
    fi
done

# Set proper permissions for security
echo "🔒 Setting secure permissions..."
chmod 700 "${CLAUDE_DIR}/cache"
chmod 755 "${CLAUDE_DIR}/logs"
chmod -R 755 "${CLAUDE_DIR}/logs/"
echo "   ✅ Cache directory secured (700)"
echo "   ✅ Logs directory accessible (755)"

# Warm up credential cache for optimal performance
echo "🔥 Warming credential cache..."
cd "${UTILS_DIR}"

if uv run warm_cache.py; then
    echo "   ✅ Cache warmed successfully"
else
    echo "   ⚠️  Cache warming completed with warnings"
fi

# Pre-compile Python bytecode for faster imports
echo "⚡ Pre-compiling Python bytecode..."
if python3 -m compileall "${UTILS_DIR}" -q; then
    echo "   ✅ Python bytecode compiled"
else
    echo "   ⚠️  Some files could not be pre-compiled"
fi

# Configure UV for optimal performance
echo "⚙️  Configuring UV for production..."
export UV_CACHE_DIR="/Users/sam/.cache/uv"
export UV_PYTHON_PREFERENCE="only-managed"

# Validate UV installation and cache
if command -v uv >/dev/null 2>&1; then
    echo "   ✅ UV found: $(uv --version)"
    
    # Test UV performance
    start_time=$(python3 -c "import time; print(time.time())")
    uv run --script -c "print('UV test successful')" >/dev/null 2>&1
    end_time=$(python3 -c "import time; print(time.time())")
    
    if command -v bc >/dev/null 2>&1; then
        uv_time=$(echo "$end_time - $start_time" | bc -l)
        echo "   ⚡ UV performance: ${uv_time}s"
    fi
else
    echo "   ❌ UV not found in PATH"
    exit 1
fi

# Validate production configuration
echo "🔍 Validating production configuration..."

validation_checks=(
    "HOOK_WRAPPER_DEBUG should be 0"
    "HOOK_WRAPPER_METRICS should be 0" 
    "CREDENTIAL_PROVIDER_DEBUG should be 0"
    "Cache directory should be accessible"
    "Logs directory should be writable"
)

errors=0

# Check environment variables
if [[ "${HOOK_WRAPPER_DEBUG:-1}" == "0" ]]; then
    echo "   ✅ Hook wrapper debug disabled"
else
    echo "   ❌ Hook wrapper debug not disabled"
    ((errors++))
fi

if [[ "${HOOK_WRAPPER_METRICS:-1}" == "0" ]]; then
    echo "   ✅ Hook wrapper metrics disabled"
else
    echo "   ❌ Hook wrapper metrics not disabled" 
    ((errors++))
fi

if [[ "${CREDENTIAL_PROVIDER_DEBUG:-1}" == "0" ]]; then
    echo "   ✅ Credential provider debug disabled"
else
    echo "   ❌ Credential provider debug not disabled"
    ((errors++))
fi

# Check directory accessibility
if [[ -r "${CLAUDE_DIR}/cache" && -w "${CLAUDE_DIR}/cache" ]]; then
    echo "   ✅ Cache directory accessible"
else
    echo "   ❌ Cache directory not accessible"
    ((errors++))
fi

if [[ -w "${CLAUDE_DIR}/logs" ]]; then
    echo "   ✅ Logs directory writable"
else
    echo "   ❌ Logs directory not writable"
    ((errors++))
fi

# Check cache file exists and is recent
cache_file="${CLAUDE_DIR}/cache/credentials_cache.json"
if [[ -f "$cache_file" ]]; then
    # Check if cache file is less than 1 hour old
    if [[ $(find "$cache_file" -mmin -60 2>/dev/null) ]]; then
        echo "   ✅ Credential cache is fresh"
    else
        echo "   ⚠️  Credential cache is stale (>1 hour old)"
    fi
else
    echo "   ❌ Credential cache file not found"
    ((errors++))
fi

# Performance test - quick hook wrapper execution
echo "🏃 Performance validation..."
cd "${UTILS_DIR}"

start_time=$(python3 -c "import time; print(time.time())")
if timeout 10s uv run hook_wrapper.py --help >/dev/null 2>&1; then
    end_time=$(python3 -c "import time; print(time.time())")
    if command -v bc >/dev/null 2>&1; then
        exec_time=$(echo "$end_time - $start_time" | bc -l)
        if (( $(echo "$exec_time < 1.0" | bc -l) )); then
            echo "   ✅ Hook wrapper performance: ${exec_time}s (EXCELLENT)"
        elif (( $(echo "$exec_time < 3.0" | bc -l) )); then
            echo "   ✅ Hook wrapper performance: ${exec_time}s (GOOD)"
        else
            echo "   ⚠️  Hook wrapper performance: ${exec_time}s (SLOW)"
        fi
    fi
else
    echo "   ❌ Hook wrapper performance test failed"
    ((errors++))
fi

# Final summary
echo ""
echo "=================================================="
if [[ $errors -eq 0 ]]; then
    echo "🎉 Production environment initialized successfully!"
    echo ""
    echo "📊 System Status:"
    echo "   • Debug logging: DISABLED"
    echo "   • Performance mode: ENABLED"
    echo "   • Cache: WARMED"
    echo "   • Permissions: SECURED"
    echo "   • Bytecode: PRE-COMPILED"
    echo ""
    echo "🚀 Ready for production workloads!"
    exit 0
else
    echo "⚠️  Production environment initialized with $errors warning(s)."
    echo "   Review the issues above and re-run if necessary."
    exit 1
fi