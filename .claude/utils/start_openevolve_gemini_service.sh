#!/bin/bash

# OpenEvolve + Gemini Integration Startup Script
# This script starts the LiteLLM proxy with Gemini configuration and the OpenEvolve service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LITELLM_CONFIG="$SCRIPT_DIR/openevolve_litellm_gemini_config.yaml"
OPENEVOLVE_SERVICE_DIR="/Users/sam/openevolve/apps/openevolve-service"
LITELLM_PORT=4001
OPENEVOLVE_PORT=8000
MAX_WAIT_TIME=30

# Log files
LITELLM_LOG="$SCRIPT_DIR/litellm_gemini.log"
OPENEVOLVE_LOG="$SCRIPT_DIR/openevolve_service.log"

# PID files for cleanup
LITELLM_PID_FILE="$SCRIPT_DIR/litellm.pid"
OPENEVOLVE_PID_FILE="$SCRIPT_DIR/openevolve.pid"

echo -e "${BLUE}🚀 Starting OpenEvolve + Gemini Integration Services${NC}"
echo "============================================================="

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up services...${NC}"
    
    # Kill LiteLLM if running
    if [ -f "$LITELLM_PID_FILE" ]; then
        LITELLM_PID=$(cat "$LITELLM_PID_FILE")
        if kill -0 "$LITELLM_PID" 2>/dev/null; then
            echo "Stopping LiteLLM proxy (PID: $LITELLM_PID)..."
            kill "$LITELLM_PID"
            rm -f "$LITELLM_PID_FILE"
        fi
    fi
    
    # Kill OpenEvolve service if running
    if [ -f "$OPENEVOLVE_PID_FILE" ]; then
        OPENEVOLVE_PID=$(cat "$OPENEVOLVE_PID_FILE")
        if kill -0 "$OPENEVOLVE_PID" 2>/dev/null; then
            echo "Stopping OpenEvolve service (PID: $OPENEVOLVE_PID)..."
            kill "$OPENEVOLVE_PID"
            rm -f "$OPENEVOLVE_PID_FILE"
        fi
    fi
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Set up signal handlers for graceful shutdown
trap cleanup EXIT INT TERM

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local max_attempts=$3
    
    echo "🔍 Waiting for $service_name to start on port $port..."
    
    for i in $(seq 1 $max_attempts); do
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1 || 
           curl -s "http://localhost:$port/models" > /dev/null 2>&1 || 
           nc -z localhost $port 2>/dev/null; then
            echo -e "${GREEN}✅ $service_name is running on port $port${NC}"
            return 0
        fi
        
        echo "  Attempt $i/$max_attempts - waiting..."
        sleep 2
    done
    
    echo -e "${RED}❌ $service_name failed to start after $max_attempts attempts${NC}"
    return 1
}

# Function to check environment variables
check_environment() {
    echo "🔧 Checking environment..."
    
    if [ -z "$GOOGLE_API_KEY" ]; then
        echo -e "${RED}❌ GOOGLE_API_KEY environment variable not set${NC}"
        echo "Please set your Google AI API key:"
        echo "export GOOGLE_API_KEY='your-api-key-here'"
        exit 1
    fi
    
    echo -e "${GREEN}✅ GOOGLE_API_KEY is set${NC}"
    
    # Check if litellm is available
    if ! command -v litellm &> /dev/null; then
        echo -e "${YELLOW}⚠️  LiteLLM not found in PATH, trying pip install...${NC}"
        pip3 install litellm
        
        if ! command -v litellm &> /dev/null; then
            echo -e "${RED}❌ Failed to install LiteLLM${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✅ LiteLLM is available${NC}"
}

# Function to start LiteLLM proxy
start_litellm() {
    echo "🔄 Starting LiteLLM proxy with Gemini configuration..."
    
    if [ ! -f "$LITELLM_CONFIG" ]; then
        echo -e "${RED}❌ LiteLLM config file not found: $LITELLM_CONFIG${NC}"
        exit 1
    fi
    
    # Start LiteLLM proxy in background
    nohup litellm --config "$LITELLM_CONFIG" --port $LITELLM_PORT --host 0.0.0.0 \
        > "$LITELLM_LOG" 2>&1 &
    
    LITELLM_PID=$!
    echo $LITELLM_PID > "$LITELLM_PID_FILE"
    
    echo "📝 LiteLLM proxy started (PID: $LITELLM_PID)"
    echo "📋 Log file: $LITELLM_LOG"
    
    # Wait for LiteLLM to start
    if ! check_service "LiteLLM proxy" $LITELLM_PORT $MAX_WAIT_TIME; then
        echo -e "${RED}❌ LiteLLM proxy failed to start${NC}"
        echo "Check log file: $LITELLM_LOG"
        exit 1
    fi
}

# Function to start OpenEvolve service
start_openevolve() {
    echo "🔄 Starting OpenEvolve service..."
    
    if [ ! -d "$OPENEVOLVE_SERVICE_DIR" ]; then
        echo -e "${RED}❌ OpenEvolve service directory not found: $OPENEVOLVE_SERVICE_DIR${NC}"
        exit 1
    fi
    
    # Set environment variables for OpenEvolve service
    export LITELLM_ENDPOINT="http://localhost:$LITELLM_PORT"
    export DEBUG=false
    export LOG_LEVEL=INFO
    export HOST=0.0.0.0
    export PORT=$OPENEVOLVE_PORT
    
    # Navigate to service directory and start
    cd "$OPENEVOLVE_SERVICE_DIR"
    
    # Start OpenEvolve service in background
    nohup python3 main.py > "$OPENEVOLVE_LOG" 2>&1 &
    
    OPENEVOLVE_PID=$!
    echo $OPENEVOLVE_PID > "$OPENEVOLVE_PID_FILE"
    
    echo "📝 OpenEvolve service started (PID: $OPENEVOLVE_PID)"
    echo "📋 Log file: $OPENEVOLVE_LOG"
    
    # Wait for OpenEvolve to start
    if ! check_service "OpenEvolve service" $OPENEVOLVE_PORT $MAX_WAIT_TIME; then
        echo -e "${RED}❌ OpenEvolve service failed to start${NC}"
        echo "Check log file: $OPENEVOLVE_LOG"
        exit 1
    fi
}

# Function to display service status
show_status() {
    echo ""
    echo "============================================================="
    echo -e "${GREEN}🎉 Services Successfully Started!${NC}"
    echo "============================================================="
    echo ""
    echo "📊 Service Status:"
    echo "  • LiteLLM Proxy:     http://localhost:$LITELLM_PORT"
    echo "  • OpenEvolve API:    http://localhost:$OPENEVOLVE_PORT"
    echo ""
    echo "📋 Available Endpoints:"
    echo "  • Health Check:      http://localhost:$OPENEVOLVE_PORT/health"
    echo "  • API Docs:          http://localhost:$OPENEVOLVE_PORT/docs"
    echo "  • OpenAPI Schema:    http://localhost:$OPENEVOLVE_PORT/openapi.json"
    echo "  • LiteLLM Models:    http://localhost:$LITELLM_PORT/models"
    echo ""
    echo "📝 Log Files:"
    echo "  • LiteLLM:           $LITELLM_LOG"
    echo "  • OpenEvolve:        $OPENEVOLVE_LOG"
    echo ""
    echo "🔑 Configuration:"
    echo "  • LiteLLM Config:    $LITELLM_CONFIG"
    echo "  • Service Directory: $OPENEVOLVE_SERVICE_DIR"
    echo ""
    echo -e "${BLUE}💡 Test the integration:${NC}"
    echo "curl http://localhost:$OPENEVOLVE_PORT/health"
    echo ""
}

# Function to monitor logs
monitor_logs() {
    echo -e "${YELLOW}📺 Monitoring service logs (Ctrl+C to stop)...${NC}"
    echo "============================================================="
    
    # Monitor both logs simultaneously
    tail -f "$LITELLM_LOG" "$OPENEVOLVE_LOG" &
    TAIL_PID=$!
    
    # Wait for interrupt
    wait $TAIL_PID
}

# Main execution
main() {
    # Check environment and dependencies
    check_environment
    
    # Start services
    start_litellm
    start_openevolve
    
    # Show status
    show_status
    
    # If run interactively, monitor logs
    if [ -t 0 ]; then
        echo -e "${YELLOW}Press Ctrl+C to stop services or 'tail -f $LITELLM_LOG' to monitor logs${NC}"
        echo ""
        
        # Keep the script running
        while true; do
            sleep 10
            
            # Check if services are still running
            if [ -f "$LITELLM_PID_FILE" ]; then
                LITELLM_PID=$(cat "$LITELLM_PID_FILE")
                if ! kill -0 "$LITELLM_PID" 2>/dev/null; then
                    echo -e "${RED}⚠️  LiteLLM proxy has stopped unexpectedly${NC}"
                    break
                fi
            fi
            
            if [ -f "$OPENEVOLVE_PID_FILE" ]; then
                OPENEVOLVE_PID=$(cat "$OPENEVOLVE_PID_FILE")
                if ! kill -0 "$OPENEVOLVE_PID" 2>/dev/null; then
                    echo -e "${RED}⚠️  OpenEvolve service has stopped unexpectedly${NC}"
                    break
                fi
            fi
        done
    fi
}

# Handle command line arguments
case "${1:-start}" in
    "start")
        main
        ;;
    "stop")
        cleanup
        ;;
    "status")
        echo "🔍 Checking service status..."
        
        if [ -f "$LITELLM_PID_FILE" ]; then
            LITELLM_PID=$(cat "$LITELLM_PID_FILE")
            if kill -0 "$LITELLM_PID" 2>/dev/null; then
                echo -e "${GREEN}✅ LiteLLM proxy is running (PID: $LITELLM_PID)${NC}"
            else
                echo -e "${RED}❌ LiteLLM proxy is not running${NC}"
            fi
        else
            echo -e "${RED}❌ LiteLLM proxy is not running${NC}"
        fi
        
        if [ -f "$OPENEVOLVE_PID_FILE" ]; then
            OPENEVOLVE_PID=$(cat "$OPENEVOLVE_PID_FILE")
            if kill -0 "$OPENEVOLVE_PID" 2>/dev/null; then
                echo -e "${GREEN}✅ OpenEvolve service is running (PID: $OPENEVOLVE_PID)${NC}"
            else
                echo -e "${RED}❌ OpenEvolve service is not running${NC}"
            fi
        else
            echo -e "${RED}❌ OpenEvolve service is not running${NC}"
        fi
        ;;
    "logs")
        echo "📺 Showing service logs..."
        echo "============================================================="
        
        if [ -f "$LITELLM_LOG" ]; then
            echo -e "${BLUE}📋 LiteLLM Proxy Log:${NC}"
            tail -n 20 "$LITELLM_LOG"
            echo ""
        fi
        
        if [ -f "$OPENEVOLVE_LOG" ]; then
            echo -e "${BLUE}📋 OpenEvolve Service Log:${NC}"
            tail -n 20 "$OPENEVOLVE_LOG"
        fi
        ;;
    "help"|"-h"|"--help")
        echo "OpenEvolve + Gemini Integration Service Manager"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start     Start both services (default)"
        echo "  stop      Stop all services"
        echo "  status    Check service status"
        echo "  logs      Show recent log entries"
        echo "  help      Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  GOOGLE_API_KEY    Required - Your Google AI API key"
        echo ""
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac