# Quick manual test - just try starting each agent one by one
export PYTHONPATH=$(pwd)

# Test 1: Canary
echo "Testing Canary..."
python agents/canary/canary_agent.py &
CANARY_PID=$!
sleep 5
if ps -p $CANARY_PID > /dev/null; then
    echo "✅ Canary works!"
    kill $CANARY_PID
else
    echo "❌ Canary crashed - checking log"
    tail -30 logs/canary_agent.log 2>/dev/null || echo "No log yet"
fi

# Test 2: Monitoring  
echo ""
echo "Testing Monitoring..."
python agents/monitoring/monitoring_agent.py &
MON_PID=$!
sleep 5
if ps -p $MON_PID > /dev/null; then
    echo "✅ Monitoring works!"
    kill $MON_PID
else
    echo "❌ Monitoring crashed"
    tail -30 logs/monitoring_agent.log 2>/dev/null || echo "No log yet"
fi

# Test 3: Response
echo ""
echo "Testing Response..."
python agents/response/intelligent_response_agent.py &
RESP_PID=$!
sleep 5
if ps -p $RESP_PID > /dev/null; then
    echo "✅ Response works!"
    kill $RESP_PID
else
    echo "❌ Response crashed"
    tail -30 logs/response_agent.log 2>/dev/null || echo "No log yet"
fi

# Test 4: Communication
echo ""
echo "Testing Communication..."
python agents/communication/communication_agent.py &
COMM_PID=$!
sleep 5
if ps -p $COMM_PID > /dev/null; then
    echo "✅ Communication works!"
    kill $COMM_PID
else
    echo "❌ Communication crashed"
    tail -30 logs/communication_agent.log 2>/dev/null || echo "No log yet"
fi

# Cleanup
killall python 2>/dev/null || true