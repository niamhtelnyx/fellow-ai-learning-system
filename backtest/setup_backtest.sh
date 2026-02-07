#!/bin/bash

echo "🎯 Setting up Weekend Backtest Environment"
echo "=========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi
echo "✅ Python 3 found"

# Check Salesforce CLI
if ! command -v sf &> /dev/null; then
    echo "❌ Salesforce CLI not found"
    echo "   Install with: npm install -g @salesforce/cli"
    exit 1
fi
echo "✅ Salesforce CLI found"

# Check if we're in the right directory
if [ ! -f "backtest_database.py" ]; then
    echo "❌ Run this script from the backtest/ directory"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install requests sqlite3

# Check if API is running
echo "🔍 Checking if qualification API is running..."
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ API is running"
else
    echo "⚠️ API not running - you'll need to start it:"
    echo "   cd ../api && python3 qualification_api.py &"
fi

# Test database setup
echo "🗄️ Testing database setup..."
python3 -c "from backtest_database import BacktestDatabase; db = BacktestDatabase(); print('✅ Database initialized')"

# Test Salesforce connectivity
echo "🔍 Testing Salesforce connectivity..."
sf org list > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Salesforce CLI authenticated"
else
    echo "❌ Salesforce CLI not authenticated"
    echo "   Run: sf org login web"
    exit 1
fi

echo ""
echo "🚀 Setup complete! Ready to run weekend backtest."
echo ""
echo "Quick start options:"
echo "  🧪 Test run:        python3 weekend_backtest.py --test"
echo "  📊 Full backtest:   python3 weekend_backtest.py --days 30"
echo "  📈 Job 1 only:      python3 job1_historical_scoring.py --test"
echo "  🔍 Job 2 only:      python3 job2_deal_analysis.py --once"
echo ""
echo "Logs will be saved to:"
echo "  📋 weekend_backtest.log"
echo "  📋 job1_historical_scoring.log" 
echo "  📋 job2_deal_analysis.log"
echo "  🗄️ backtest_results.db"