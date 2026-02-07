#!/bin/bash

echo "🚀 Starting Business Context Qualification API"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Check if model files exist
if [ ! -f "../ml-model/models/business_context_v1/fellow_business_context_v1.joblib" ]; then
    echo "❌ Model files not found! Make sure you're in the correct directory."
    echo "   Expected: ../ml-model/models/business_context_v1/fellow_business_context_v1.joblib"
    exit 1
fi

echo "✅ Model files found"

# Start the API
echo "🚀 Starting API server on http://localhost:8080"
echo "   Health check: http://localhost:8080/health"
echo "   Model info: http://localhost:8080/model/info"
echo "   Docs: See README.md for endpoint details"
echo ""
echo "Press Ctrl+C to stop"

python qualification_api.py