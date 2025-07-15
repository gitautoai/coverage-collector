#!/bin/bash

# Coverage Collector Run Script

set -e

echo "🚀 Coverage Collector Setup & Run"
echo "================================"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo "📥 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Using default values."
    echo "   Copy .env.example to .env and add your GitHub token for better API access."
fi

# Run the coverage collector
echo "🏃 Running coverage collector..."
python main.py "$@"

echo "✅ Done!"