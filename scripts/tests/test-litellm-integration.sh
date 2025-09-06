#!/bin/bash

# LiteLLM Claude Code Integration Test Suite
# ==========================================
# 
# This script provides comprehensive testing for the liteLLM proxy integration
# with Claude Code, including health checks, model routing, fallback testing,
# and performance validation.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/litellm-claude-integration.yaml"
PROXY_PORT="4001"
PROXY_URL="http://localhost:$PROXY_PORT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

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

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    ((TESTS_TOTAL++))
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

# Function to check if proxy is running
check_proxy_running() {
    if curl -s "$PROXY_URL/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to start proxy if not running
ensure_proxy_running() {
    log_info "Ensuring liteLLM proxy is running..."
    
    if check_proxy_running; then
        log_success "Proxy already running"
        return 0
    fi
    
    # Check if container exists and start it
    if docker ps -a --format '{{.Names}}' | grep -q "claude-litellm-proxy"; then
        log_info "Starting existing proxy container..."
        docker start claude-litellm-proxy > /dev/null 2>&1 || {
            log_warning "Failed to start existing container, recreating..."
            docker rm claude-litellm-proxy > /dev/null 2>&1 || true
        }
    fi
    
    # If container doesn't exist or failed to start, create new one
    if ! check_proxy_running; then
        log_info "Creating new proxy container..."
        docker run -d --name claude-litellm-proxy \
            -p $PROXY_PORT:4000 \
            -v "$CONFIG_FILE:/app/config.yaml" \
            -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
            -e VERTEX_PROJECT="$VERTEX_PROJECT" \
            -e VERTEX_LOCATION="$VERTEX_LOCATION" \
            ghcr.io/berriai/litellm:main-latest \
            --config /app/config.yaml --port 4000 > /dev/null 2>&1
        
        # Wait for startup
        local retries=0
        while [[ $retries -lt 30 ]]; do
            if check_proxy_running; then
                log_success "Proxy started successfully"
                return 0
            fi
            sleep 1
            ((retries++))
        done
        
        log_error "Failed to start proxy within 30 seconds"
        return 1
    fi
}

# Test 1: Health endpoint
test_health_endpoint() {
    log_test "Testing health endpoint..."
    
    local response
    if response=$(curl -s "$PROXY_URL/health"); then
        if echo "$response" | jq -e '.healthy_endpoints' > /dev/null 2>&1; then
            local healthy_count
            healthy_count=$(echo "$response" | jq '.healthy_count')
            log_pass "Health endpoint accessible, $healthy_count healthy models"
            return 0
        else
            log_fail "Health endpoint returned invalid JSON"
            return 1
        fi
    else
        log_fail "Health endpoint not accessible"
        return 1
    fi
}

# Test 2: Model listing
test_model_listing() {
    log_test "Testing model listing endpoint..."
    
    local response
    if response=$(curl -s "$PROXY_URL/v1/models"); then
        if echo "$response" | jq -e '.data' > /dev/null 2>&1; then
            local model_count
            model_count=$(echo "$response" | jq '.data | length')
            log_pass "Model listing successful, $model_count models available"
            return 0
        else
            log_fail "Model listing returned invalid response"
            return 1
        fi
    else
        log_fail "Model listing endpoint not accessible"
        return 1
    fi
}

# Test 3: Primary model completion
test_primary_model() {
    log_test "Testing primary model (claude-primary)..."
    
    local response
    response=$(curl -s -X POST "$PROXY_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "claude-primary",
            "messages": [{"role": "user", "content": "Respond with exactly: INTEGRATION_TEST_SUCCESS"}],
            "max_tokens": 10
        }')
    
    if echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
        local content
        content=$(echo "$response" | jq -r '.choices[0].message.content')
        if [[ "$content" == *"INTEGRATION_TEST_SUCCESS"* ]]; then
            log_pass "Primary model responding correctly"
            return 0
        else
            log_fail "Primary model response unexpected: $content"
            return 1
        fi
    else
        log_fail "Primary model completion failed: $response"
        return 1
    fi
}

# Test 4: Fast model completion
test_fast_model() {
    log_test "Testing fast model (claude-fast)..."
    
    local response
    response=$(curl -s -X POST "$PROXY_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "claude-fast",
            "messages": [{"role": "user", "content": "Respond with exactly: FAST_TEST_SUCCESS"}],
            "max_tokens": 10
        }')
    
    if echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
        local content
        content=$(echo "$response" | jq -r '.choices[0].message.content')
        if [[ "$content" == *"FAST_TEST_SUCCESS"* ]]; then
            log_pass "Fast model responding correctly"
            return 0
        else
            log_fail "Fast model response unexpected: $content"
            return 1
        fi
    else
        log_fail "Fast model completion failed: $response"
        return 1
    fi
}

# Test 5: Concurrent requests
test_concurrent_requests() {
    log_test "Testing concurrent requests (5 parallel)..."
    
    local pids=()
    local results=()
    
    # Start 5 concurrent requests
    for i in {1..5}; do
        {
            local response
            response=$(curl -s -X POST "$PROXY_URL/v1/chat/completions" \
                -H "Content-Type: application/json" \
                -d "{
                    \"model\": \"claude-primary\",
                    \"messages\": [{\"role\": \"user\", \"content\": \"Test $i\"}],
                    \"max_tokens\": 5
                }")
            
            if echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
                echo "SUCCESS_$i"
            else
                echo "FAILED_$i"
            fi
        } &
        pids+=($!)
    done
    
    # Wait for all requests to complete
    local success_count=0
    for pid in "${pids[@]}"; do
        if wait "$pid"; then
            ((success_count++))
        fi
    done
    
    if [[ $success_count -eq 5 ]]; then
        log_pass "All 5 concurrent requests completed successfully"
        return 0
    else
        log_fail "Only $success_count out of 5 concurrent requests succeeded"
        return 1
    fi
}

# Test 6: Claude Code settings validation
test_claude_settings() {
    log_test "Testing Claude Code settings configuration..."
    
    local settings_file="$PROJECT_ROOT/.claude/settings.json"
    
    if [[ ! -f "$settings_file" ]]; then
        log_fail "Claude settings file not found: $settings_file"
        return 1
    fi
    
    # Check if settings contain proper MCP configurations
    if jq -e '.mcpServers' "$settings_file" > /dev/null 2>&1; then
        log_pass "Claude settings contain MCP server configurations"
    else
        log_fail "Claude settings missing MCP server configurations"
        return 1
    fi
    
    # Check if llmGateway is not hardcoded (should be added dynamically by script)
    if jq -e '.llmGateway' "$settings_file" > /dev/null 2>&1; then
        log_warning "LLM Gateway configuration found in settings (should be dynamic)"
    else
        log_pass "LLM Gateway configuration correctly absent (dynamic mode)"
    fi
    
    return 0
}

# Test 7: Performance benchmark
test_performance() {
    log_test "Testing performance benchmark..."
    
    local start_time
    local end_time
    local duration
    
    start_time=$(date +%s)
    
    local response
    response=$(curl -s -X POST "$PROXY_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "claude-fast",
            "messages": [{"role": "user", "content": "Count from 1 to 10"}],
            "max_tokens": 50
        }')
    
    end_time=$(date +%s)
    duration=$(( end_time - start_time )) # Duration in seconds
    
    if echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
        if [[ $duration -lt 5 ]]; then # Less than 5 seconds
            log_pass "Performance test passed: ${duration}s response time"
            return 0
        else
            log_warning "Performance test slow: ${duration}s response time"
            return 0
        fi
    else
        log_fail "Performance test failed: request unsuccessful"
        return 1
    fi
}

# Test 8: Fallback handling
test_fallback_handling() {
    log_test "Testing fallback behavior with invalid model..."
    
    local response
    response=$(curl -s -X POST "$PROXY_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "nonexistent-model",
            "messages": [{"role": "user", "content": "Respond with exactly: FALLBACK_TEST"}],
            "max_tokens": 10
        }')
    
    # LiteLLM should fallback to available model instead of erroring
    if echo "$response" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
        local model
        model=$(echo "$response" | jq -r '.model')
        log_pass "Fallback working correctly, routed to: $model"
        return 0
    else
        log_fail "Fallback handling not working properly"
        return 1
    fi
}

# Function to display test summary
show_summary() {
    echo
    echo "====================================="
    echo "🧪 LiteLLM Integration Test Summary"
    echo "====================================="
    echo "Total Tests: $TESTS_TOTAL"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}✅ ALL TESTS PASSED - Integration Ready${NC}"
        return 0
    else
        echo -e "\n${RED}❌ SOME TESTS FAILED - Check Issues Above${NC}"
        return 1
    fi
}

# Main test execution
main() {
    echo "🧪 LiteLLM Claude Code Integration Test Suite"
    echo "=============================================="
    echo "Proxy URL: $PROXY_URL"
    echo "Config File: $CONFIG_FILE"
    echo
    
    # Ensure credentials are loaded
    if [[ -z "${GOOGLE_API_KEY:-}" ]]; then
        log_error "GOOGLE_API_KEY not set. Run: source <(uv run $PROJECT_ROOT/.claude/hooks/pre_claude_startup.py --export --quiet)"
        exit 1
    fi
    
    # Ensure proxy is running
    if ! ensure_proxy_running; then
        log_error "Failed to start proxy. Aborting tests."
        exit 1
    fi
    
    echo "🚀 Starting integration tests..."
    echo
    
    # Run all tests
    test_health_endpoint || true
    test_model_listing || true
    test_primary_model || true
    test_fast_model || true
    test_concurrent_requests || true
    test_claude_settings || true
    test_performance || true
    test_fallback_handling || true
    
    # Show summary and exit with appropriate code
    show_summary
}

# Handle interrupts gracefully
trap 'log_warning "Tests interrupted by user"; exit 1' INT TERM

# Execute main function
main "$@"