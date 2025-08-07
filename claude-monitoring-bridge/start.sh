#!/bin/bash
# Claude Monitoring Bridge - Startup Script
# Avvia il servizio di monitoraggio e recovery automatico

set -e

BRIDGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BRIDGE_DIR"

echo "🚀 Starting Claude Monitoring Bridge..."
echo "📁 Working directory: $BRIDGE_DIR"

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.7+"
    exit 1
fi

# Check uv
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Check if claude-monitor is installed
if ! command -v claude-monitor &> /dev/null; then
    echo "📦 Installing claude-monitor with uv..."
    uv tool install claude-monitor
    echo "✅ claude-monitor installed"
fi

# Check dependencies
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

# Check config
if [ ! -f "config.yaml" ]; then
    echo "❌ config.yaml not found"
    exit 1
fi

echo "✅ Prerequisites OK"

# Install/update dependencies if needed
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt > /dev/null 2>&1
echo "✅ Dependencies installed"

# Check if Bun server is running
echo "🔍 Checking Bun server connection..."
if ! curl -s "http://localhost:4000/health" > /dev/null 2>&1; then
    echo "⚠️  Warning: Bun server not responding on localhost:4000"
    echo "   Make sure to start the hooks system first:"
    echo "   cd ../apps/server && bun run dev"
    echo ""
fi

# Check if port 8080 is available
if lsof -i :8080 > /dev/null 2>&1; then
    echo "❌ Port 8080 is already in use. Please free the port or change config."
    exit 1
fi

echo "🎯 Starting Claude Monitoring Bridge on http://localhost:8080"
echo "📊 Metrics: http://localhost:8080/metrics" 
echo "❤️  Health: http://localhost:8080/health"
echo ""
echo "Press Ctrl+C to stop the service"
echo "Logs will be saved to bridge.log"
echo ""

# Start the bridge
python3 bridge.py