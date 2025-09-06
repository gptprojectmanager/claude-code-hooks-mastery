#!/bin/bash
"""
OpenEvolve Command Line Interface
Simplified CLI wrapper for OpenEvolve optimization workflow
"""

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORKTREE_MANAGER="$SCRIPT_DIR/openevolve_worktree_manager.py"
DEMO_SCRIPT="$SCRIPT_DIR/openevolve_test_demo.py"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_usage() {
    echo "OpenEvolve CLI - Evolutionary Code Optimization"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  optimize <file> <language>  - Start optimization for a code file"
    echo "  status <session-id>         - Check status of optimization session"
    echo "  list                        - List active optimization sessions"  
    echo "  cleanup <session-id>        - Cleanup optimization session"
    echo "  cleanup-stale               - Cleanup old sessions (>24h)"
    echo "  demo                        - Run optimization demo"
    echo "  health                      - Check OpenEvolve service health"
    echo ""
    echo "Examples:"
    echo "  $0 optimize my_code.py python"
    echo "  $0 status python_abc123_1234567890"
    echo "  $0 cleanup python_abc123_1234567890"
    echo "  $0 demo"
}

check_service() {
    echo -e "${BLUE}🔍 Checking OpenEvolve service...${NC}"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OpenEvolve service is running${NC}"
        return 0
    else
        echo -e "${RED}❌ OpenEvolve service not available at http://localhost:8000${NC}"
        echo -e "${YELLOW}💡 Start the service with: cd /Users/sam/openevolve/apps/openevolve-service && ./start.sh${NC}"
        return 1
    fi
}

optimize_code() {
    local file="$1"
    local language="$2"
    
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}❌ File not found: $file${NC}"
        exit 1
    fi
    
    if [[ -z "$language" ]]; then
        echo -e "${RED}❌ Language parameter required${NC}"
        exit 1
    fi
    
    check_service || exit 1
    
    echo -e "${BLUE}🚀 Starting optimization for $file ($language)${NC}"
    python3 "$WORKTREE_MANAGER" create --code-file "$file" --language "$language"
}

show_status() {
    local session_id="$1"
    
    if [[ -z "$session_id" ]]; then
        echo -e "${RED}❌ Session ID required${NC}"
        exit 1
    fi
    
    python3 "$WORKTREE_MANAGER" status --session-id "$session_id"
}

list_sessions() {
    echo -e "${BLUE}📋 Active optimization sessions:${NC}"
    python3 "$WORKTREE_MANAGER" list
}

cleanup_session() {
    local session_id="$1"
    
    if [[ -z "$session_id" ]]; then
        echo -e "${RED}❌ Session ID required${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}🧹 Cleaning up session $session_id${NC}"
    python3 "$WORKTREE_MANAGER" cleanup --session-id "$session_id"
}

cleanup_stale() {
    echo -e "${YELLOW}🧹 Cleaning up stale sessions...${NC}"
    python3 "$WORKTREE_MANAGER" cleanup-stale
}

run_demo() {
    echo -e "${BLUE}🎬 Running OpenEvolve optimization demo...${NC}"
    python3 "$DEMO_SCRIPT"
}

health_check() {
    check_service
    
    echo -e "${BLUE}📊 Service statistics:${NC}"
    curl -s http://localhost:8000/stats | python3 -m json.tool 2>/dev/null || echo "Stats not available"
    
    echo -e "${BLUE}📈 Recent jobs:${NC}" 
    curl -s "http://localhost:8000/jobs?limit=5" | python3 -m json.tool 2>/dev/null || echo "Jobs not available"
}

# Main command handling
case "${1:-}" in
    "optimize")
        optimize_code "$2" "$3"
        ;;
    "status")
        show_status "$2"
        ;;
    "list")
        list_sessions
        ;;
    "cleanup")
        cleanup_session "$2"
        ;;
    "cleanup-stale")
        cleanup_stale
        ;;
    "demo")
        run_demo
        ;;
    "health")
        health_check
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: ${1:-}${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac