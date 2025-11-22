#!/bin/bash

###############################################################################
# ARGO - Backend Startup
###############################################################################

echo "📡 Initializing Backend..."

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

cd "$BACKEND_DIR"

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env and add your OpenAI API key"
    echo ""
fi

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔧 Activating environment..."
source venv/bin/activate

echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create directories
mkdir -p data logs temp

echo "✅ Backend ready"
echo "🌐 Starting server on port 8000..."
echo ""

# Start backend
python main.py
