#!/bin/bash

# LiteLLM Proxy Production Monitoring Script
# ==========================================
# 
# This script provides continuous monitoring for the liteLLM proxy,
# including health checks, performance metrics, and automatic restart
# capabilities for production deployment.

set -euo pipefail

# Configuration
PROXY_URL="http://localhost:4001"
CHECK_INTERVAL=30  # seconds
LOG_FILE="/tmp/litellm-monitor.log"
ALERT_THRESHOLD=3  # consecutive failures before alert
MAX_RESPONSE_TIME=5  # seconds

# State tracking
consecutive_failures=0
last_check_time=$(date +%s)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_with_timestamp() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    log_with_timestamp "INFO" "$1"
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log_with_timestamp "SUCCESS" "$1"
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log_with_timestamp "WARNING" "$1"
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log_with_timestamp "ERROR" "$1"
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check proxy health
check_proxy_health() {
    local start_time=$(date +%s)
    local response
    local http_code
    
    # Try to get health endpoint
    if response=$(curl -s -w "%{http_code}" "$PROXY_URL/health" --max-time 10 2>/dev/null); then
        http_code="${response: -3}"
        response="${response%???}"
        
        local end_time=$(date +%s)
        local response_time=$((end_time - start_time))
        
        if [[ "$http_code" == "200" ]]; then
            # Parse healthy endpoint count
            local healthy_count unhealthy_count
            if healthy_count=$(echo "$response" | jq -r '.healthy_count' 2>/dev/null) && \
               unhealthy_count=$(echo "$response" | jq -r '.unhealthy_count' 2>/dev/null); then
                if [[ "$healthy_count" -gt 0 ]]; then
                    log_success "Proxy healthy: $healthy_count models, ${response_time}s response time"
                    
                    # Extract model information for observability
                    local model_info="healthy:$healthy_count,unhealthy:$unhealthy_count"
                    send_observability_event "health_check" "healthy" "$model_info" "${response_time}000" "Proxy operational with $healthy_count healthy models"
                    
                    consecutive_failures=0
                    return 0
                else
                    log_error "No healthy models available"
                    send_observability_event "health_check" "unhealthy" "healthy:0,unhealthy:$unhealthy_count" "${response_time}000" "No healthy models available"
                    ((consecutive_failures++))
                    return 1
                fi
            else
                log_error "Invalid health response format"
                send_observability_event "health_check" "error" "unknown" "${response_time}000" "Invalid health response format"
                ((consecutive_failures++))
                return 1
            fi
        else
            log_error "Health endpoint returned HTTP $http_code"
            send_observability_event "health_check" "error" "unknown" "${response_time}000" "HTTP $http_code from health endpoint"
            ((consecutive_failures++))
            return 1
        fi
    else
        log_error "Health endpoint unreachable"
        send_observability_event "health_check" "unreachable" "unknown" "0" "Health endpoint unreachable"
        ((consecutive_failures++))
        return 1
    fi
}

# Function to test completion endpoint
test_completion() {
    local start_time=$(date +%s)
    local response
    
    response=$(curl -s -X POST "$PROXY_URL/v1/chat/completions" \
        --max-time 10 \
        -H "Content-Type: application/json" \
        -d '{
            "model": "claude-primary",
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5
        }' 2>/dev/null || echo "")
    
    local end_time=$(date +%s)
    local response_time=$((end_time - start_time))
    
    if [[ -n "$response" ]] && echo "$response" | jq -e '.choices[0]' > /dev/null 2>&1; then
        # Extract model information for observability
        local model=$(echo "$response" | jq -r '.model // "unknown"')
        local model_provider="gemini"
        local model_version="unknown"
        
        # Determine model version
        if [[ "$model" == *"2.5-pro"* ]]; then
            model_version="2.5-pro"
        elif [[ "$model" == *"2.5-flash"* ]]; then
            model_version="2.5-flash"
        elif [[ "$model" == *"gemini"* ]]; then
            model_provider="gemini"
        fi
        
        local model_info="provider:$model_provider,version:$model_version,model:$model"
        
        if [[ $response_time -gt $MAX_RESPONSE_TIME ]]; then
            log_warning "Completion working but slow: ${response_time}s"
            send_observability_event "completion_test" "slow" "$model_info" "${response_time}000" "Completion slow but working"
        else
            log_success "Completion test passed: ${response_time}s"
            send_observability_event "completion_test" "success" "$model_info" "${response_time}000" "Completion test successful"
        fi
        return 0
    else
        log_error "Completion test failed"
        send_observability_event "completion_test" "failed" "unknown" "${response_time}000" "Completion test failed"
        return 1
    fi
}

# Function to restart proxy if needed
restart_proxy() {
    log_warning "Attempting to restart liteLLM proxy..."
    
    # Stop existing container
    if docker stop claude-litellm-proxy 2>/dev/null; then
        log_info "Stopped existing proxy container"
    fi
    
    # Remove container
    docker container rm claude-litellm-proxy 2>/dev/null || true
    
    # Start new container
    local config_file="/Users/sam/claude-code-hooks-mastery/litellm-claude-integration.yaml"
    
    if docker run -d --name claude-litellm-proxy \
        -p 4001:4000 \
        -v "$config_file:/app/config.yaml" \
        -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
        -e VERTEX_PROJECT="$VERTEX_PROJECT" \
        -e VERTEX_LOCATION="$VERTEX_LOCATION" \
        ghcr.io/berriai/litellm:main-latest \
        --config /app/config.yaml --port 4000 > /dev/null 2>&1; then
        
        log_info "Started new proxy container, waiting for startup..."
        
        # Wait for health check
        local retries=0
        while [[ $retries -lt 20 ]]; do
            if check_proxy_health > /dev/null 2>&1; then
                log_success "Proxy restart successful"
                consecutive_failures=0
                return 0
            fi
            sleep 3
            ((retries++))
        done
        
        log_error "Proxy restart failed - health check timeout"
        return 1
    else
        log_error "Failed to start proxy container"
        return 1
    fi
}

# Function to send event to observability system
send_observability_event() {
    local event_type="$1"
    local status="$2"
    local model_info="$3"
    local response_time="$4"
    local details="$5"
    
    # Send event to observability server
    local event_data=$(cat << EOF
{
    "source_app": "litellm-monitor",
    "session_id": "proxy-monitor-$$",
    "hook_event_type": "ProxyHealth",
    "payload": {
        "event_type": "$event_type",
        "status": "$status",
        "proxy_type": "litellm",
        "model_info": "$model_info",
        "response_time_ms": $response_time,
        "details": "$details",
        "timestamp": $(date +%s)000,
        "health_check": {
            "consecutive_failures": $consecutive_failures,
            "alert_threshold": $ALERT_THRESHOLD
        }
    }
}
EOF
    )
    
    # Send to observability server
    if curl -s -X POST http://localhost:4000/events \
        -H "Content-Type: application/json" \
        -d "$event_data" > /dev/null 2>&1; then
        log_info "Event sent to observability system"
    else
        log_warning "Failed to send event to observability system"
    fi
}

# Function to send alerts (can be extended with email, Slack, etc.)
send_alert() {
    local message="$1"
    log_error "ALERT: $message"
    
    # Send alert to observability system
    send_observability_event "alert" "critical" "system" "0" "$message"
    
    # Also log to syslog
    logger -t "litellm-monitor" "ALERT: $message"
}

# Function to check system resources
check_system_resources() {
    # Check Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker daemon is not running"
        return 1
    fi
    
    # Check disk space
    local disk_usage
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        log_warning "Disk usage high: ${disk_usage}%"
    fi
    
    # Check memory usage
    local mem_usage
    mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [[ $mem_usage -gt 90 ]]; then
        log_warning "Memory usage high: ${mem_usage}%"
    fi
    
    return 0
}

# Function to display status
show_status() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 LiteLLM Proxy Monitor - $(date)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Proxy URL: $PROXY_URL"
    echo "Check Interval: ${CHECK_INTERVAL}s"
    echo "Consecutive Failures: $consecutive_failures"
    echo "Log File: $LOG_FILE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Function to cleanup on exit
cleanup() {
    log_info "Monitor stopped by user"
    exit 0
}

# Main monitoring loop
main() {
    echo "🔍 Starting LiteLLM Proxy Production Monitor"
    
    # Ensure credentials are loaded
    if [[ -z "${GOOGLE_API_KEY:-}" ]]; then
        log_error "GOOGLE_API_KEY not set. Load credentials first."
        exit 1
    fi
    
    # Create log file
    touch "$LOG_FILE"
    log_info "Monitor started (PID: $$)"
    
    # Initial status
    show_status
    
    # Main monitoring loop
    while true; do
        # Check system resources
        check_system_resources
        
        # Check proxy health
        if check_proxy_health; then
            # If health is good, also test completion
            if ! test_completion; then
                log_warning "Health OK but completion test failed"
            fi
        else
            log_error "Health check failed (failure #$consecutive_failures)"
            
            # If too many consecutive failures, try restart
            if [[ $consecutive_failures -ge $ALERT_THRESHOLD ]]; then
                send_alert "Proxy failed $consecutive_failures consecutive health checks"
                
                # Try to restart
                if restart_proxy; then
                    log_success "Automatic restart successful"
                else
                    send_alert "Automatic restart failed - manual intervention required"
                    # Reset counter to avoid spam
                    consecutive_failures=0
                fi
            fi
        fi
        
        # Wait for next check
        sleep $CHECK_INTERVAL
    done
}

# Handle interrupts gracefully
trap cleanup INT TERM

# Check if running with correct arguments
if [[ "${1:-}" == "--status" ]]; then
    show_status
    check_proxy_health
    test_completion
    exit 0
elif [[ "${1:-}" == "--restart" ]]; then
    restart_proxy
    exit $?
elif [[ "${1:-}" == "--help" ]]; then
    cat << EOF
LiteLLM Proxy Production Monitor

USAGE:
    $0                  # Start continuous monitoring
    $0 --status        # Show current status and exit
    $0 --restart       # Restart proxy and exit
    $0 --help          # Show this help

FEATURES:
    ✅ Continuous health monitoring
    ✅ Performance tracking
    ✅ Automatic restart on failures
    ✅ System resource monitoring
    ✅ Alert capabilities
    ✅ Detailed logging

ENVIRONMENT VARIABLES:
    GOOGLE_API_KEY     # Required for proxy authentication
    VERTEX_PROJECT     # Required for Vertex AI fallback
    VERTEX_LOCATION    # Required for Vertex AI fallback

LOG FILE: $LOG_FILE
EOF
    exit 0
fi

# Execute main monitoring function
main "$@"