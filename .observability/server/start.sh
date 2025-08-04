#!/bin/bash

# Multi-Agent Observability Server Startup Script

echo "🚀 Starting Multi-Agent Observability Server..."

# Check if Bun is installed
if ! command -v bun &> /dev/null; then
    echo "❌ Bun is not installed. Please install Bun first:"
    echo "curl -fsSL https://bun.sh/install | bash"
    exit 1
fi

# Check if .env file exists, create from example if not
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp .env.example .env
fi

# Install dependencies
echo "📦 Installing dependencies..."
bun install

# Create static directory if it doesn't exist
mkdir -p static

# Check if database directory exists
mkdir -p logs

# Start the server
echo "🔥 Starting server on port 4000..."
echo "📊 Dashboard: http://localhost:4000"
echo "📡 WebSocket: ws://localhost:4000/stream"
echo "📮 Events API: http://localhost:4000/api/events"
echo ""
echo "Press Ctrl+C to stop the server"

bun run src/index.ts