#!/bin/bash
# Claude Monitoring Bridge - System Check
# Verifica stato di tutti i componenti del sistema

set -e

echo "🔍 Claude Monitoring Bridge - System Status Check"
echo "=================================================="
echo ""

# Check Bun Server (Hooks System)
echo "1️⃣ Checking Bun Server (Hooks System)..."
if curl -s "http://localhost:4000/health" > /dev/null 2>&1; then
    echo "✅ Bun server is running on localhost:4000"
    # Get additional info if available
    if response=$(curl -s "http://localhost:4000/health" 2>/dev/null); then
        echo "   Response: $response"
    fi
else
    echo "❌ Bun server not responding on localhost:4000"
    echo "   To start: cd ../apps/server && bun run dev"
fi
echo ""

# Check WebSocket endpoint
echo "2️⃣ Checking WebSocket endpoint..."
if timeout 3 wscat -c ws://localhost:4000/stream < /dev/null > /dev/null 2>&1; then
    echo "✅ WebSocket endpoint accessible"
elif command -v wscat &> /dev/null; then
    echo "❌ WebSocket endpoint not accessible"
else
    echo "⚠️  wscat not available for WebSocket testing"
    echo "   Install: npm install -g wscat"
fi
echo ""

# Check Bridge API
echo "3️⃣ Checking Bridge API..."
if curl -s "http://localhost:8080/health" > /dev/null 2>&1; then
    echo "✅ Bridge API is running on localhost:8080"
    # Get health status
    if health=$(curl -s "http://localhost:8080/health" 2>/dev/null); then
        echo "   Health: $health"
    fi
else
    echo "❌ Bridge API not responding on localhost:8080"
    echo "   To start: ./start.sh"
fi
echo ""

# Check Usage Monitor (claude-monitor CLI)
echo "4️⃣ Checking Usage Monitor CLI..."
if command -v claude-monitor &> /dev/null; then
    echo "✅ claude-monitor CLI available"
    echo "   Location: $(which claude-monitor)"
    echo "   Version: $(claude-monitor --version 2>/dev/null || echo "available")"
elif command -v uv &> /dev/null; then
    echo "⚠️  claude-monitor not found, attempting installation with uv..."
    uv tool install claude-monitor
    if command -v claude-monitor &> /dev/null; then
        echo "✅ claude-monitor installed successfully"
    else
        echo "❌ Failed to install claude-monitor"
    fi
else
    echo "⚠️  Neither claude-monitor nor uv found"
    echo "   Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   Then: uv tool install claude-monitor"
fi
echo ""

# Summary
echo "📋 SUMMARY"
echo "=========="
bun_status="❌"
websocket_status="❌"
bridge_status="❌"
monitor_status="⚠️"

if curl -s "http://localhost:4000/health" > /dev/null 2>&1; then
    bun_status="✅"
fi

if curl -s "http://localhost:8080/health" > /dev/null 2>&1; then
    bridge_status="✅"
fi

echo "Bun Server:    $bun_status"
echo "Bridge API:    $bridge_status"
echo "Usage Monitor: $monitor_status"
echo ""

if [[ "$bun_status" == "✅" && "$bridge_status" == "✅" ]]; then
    echo "🎉 Sistema completamente operativo!"
    echo ""
    echo "🔗 Quick Links:"
    echo "   • Bridge Health:  http://localhost:8080/health"
    echo "   • Bridge Metrics: http://localhost:8080/metrics"
    echo "   • Hooks System:   http://localhost:4000/health"
else
    echo "⚠️  Alcuni componenti non sono attivi."
    echo ""
    echo "🛠️ Per avviare tutto:"
    echo "   1. cd ../apps/server && bun run dev    # Hooks system"
    echo "   2. ./start.sh                          # Bridge service"
fi