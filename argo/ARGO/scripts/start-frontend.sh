#!/bin/bash

###############################################################################
# ARGO - Frontend Startup
###############################################################################

echo "🎨 Initializing Frontend..."

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

cd "$FRONTEND_DIR"

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env from template..."
    cp .env.example .env
fi

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "✅ Frontend ready"
echo "🌐 Starting dev server on port 5000..."
echo ""

# Start frontend
npm run dev:client
