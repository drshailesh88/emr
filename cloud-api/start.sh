#!/bin/bash

# DocAssist Cloud API Startup Script

set -e

echo "=== DocAssist Cloud API ==="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Check if JWT secret is configured
JWT_SECRET=$(grep "^JWT_SECRET_KEY=" .env | cut -d'=' -f2)
if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "your-secret-key-here-generate-with-openssl-rand-hex-32" ]; then
    echo "ERROR: JWT_SECRET_KEY not configured in .env"
    echo ""
    echo "Generate a secret key with:"
    echo "  openssl rand -hex 32"
    echo ""
    echo "Then add it to .env file"
    exit 1
fi

# Create data directories
mkdir -p data/backups

echo ""
echo "Starting server..."
echo "API Docs: http://localhost:8000/docs"
echo "Health: http://localhost:8000/health"
echo ""

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
