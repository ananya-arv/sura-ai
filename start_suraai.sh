#!/bin/bash

echo "🚀 Starting SuraAI - Autonomous Disaster Recovery Network"
echo "============================================================"

# Check Python version
python3 --version

# Activate virtual environment
source venv/bin/activate

# Start mock infrastructure
echo ""
echo "📦 Starting Mock Infrastructure..."
python services/mock_infrastructure.py &
MOCK_PID=$!
sleep 3

# Start all agents
echo ""
echo "🤖 Starting Agents..."
python main.py &
AGENTS_PID=$!
sleep 5

# Open dashboard
echo ""
echo "📊 Opening Dashboard..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open dashboard/dashboard.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open dashboard/dashboard.html
else
    start dashboard/dashboard.html
fi

echo ""
echo "============================================================"
echo "✅ SuraAI is running!"
echo ""
echo "📊 Dashboard: file://$(pwd)/dashboard/dashboard.html"
echo "🔌 API: http://localhost:8000"
echo "📝 Logs: logs/"
echo ""
echo "Press Ctrl+C to stop all services"
echo "============================================================"

# Wait for interrupt
trap "echo ''; echo '🛑 Stopping SuraAI...'; kill $MOCK_PID $AGENTS_PID; exit" INT
wait
