#!/bin/bash

###############################################################################
# ARGO Platform - Full System Startup
###############################################################################

echo "=========================================="
echo "🚀 ARGO Enterprise Platform"
echo "=========================================="
echo ""

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.sh

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "📡 Starting Backend..."
"$SCRIPT_DIR/start-backend.sh" &

sleep 3

# Start frontend
echo "🎨 Starting Frontend..."
"$SCRIPT_DIR/start-frontend.sh" &

echo ""
echo "=========================================="
echo "✅ ARGO is running!"
echo "=========================================="
echo ""
echo "📍 Frontend: http://localhost:5000"
echo "📍 Backend: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

wait
