#!/bin/bash

# SuraAI E2E Test Pipeline Setup - FIXED VERSION
# Includes PYTHONPATH fix for imports

echo "🚀 SuraAI End-to-End Test Pipeline Setup"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# CRITICAL FIX: Set PYTHONPATH so agents can find each other
export PYTHONPATH=$(pwd):${PYTHONPATH}
echo -e "\n${GREEN}🔧 PYTHONPATH set to: $(pwd)${NC}"

# Cleanup old registry
echo -e "\n${YELLOW}Cleaning up old registry...${NC}"
rm -f agent_registry.json
rm -f logs/*.log
mkdir -p logs

# Start mock infrastructure
echo -e "\n${GREEN}1️⃣  Starting Mock Infrastructure...${NC}"
PYTHONPATH=$(pwd) python services/mock_infrastructure.py > logs/mock_infra.log 2>&1 &
MOCK_PID=$!
echo "   PID: $MOCK_PID"
sleep 3

# Check if mock is running
curl -s http://localhost:8000/health > /dev/null
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ Mock infrastructure running${NC}"
else
    echo -e "   ${RED}❌ Mock infrastructure failed to start${NC}"
    echo "   Check logs/mock_infra.log for errors"
    exit 1
fi

# Start agents (they will auto-register)
echo -e "\n${GREEN}2️⃣  Starting Agents (will auto-register)...${NC}"

echo "   Starting Canary Agent..."
PYTHONPATH=$(pwd) python agents/canary/canary_agent.py > logs/canary_startup.log 2>&1 &
CANARY_PID=$!
sleep 3

echo "   Starting Monitoring Agent..."
PYTHONPATH=$(pwd) python agents/monitoring/monitoring_agent.py > logs/monitoring_startup.log 2>&1 &
MONITORING_PID=$!
sleep 3

echo "   Starting Response Agent..."
PYTHONPATH=$(pwd) python agents/response/intelligent_response_agent.py > logs/response_startup.log 2>&1 &
RESPONSE_PID=$!
sleep 3

echo "   Starting Communication Agent..."
PYTHONPATH=$(pwd) python agents/communication/communication_agent.py > logs/communication_startup.log 2>&1 &
COMMUNICATION_PID=$!
sleep 3

echo -e "\n   ${GREEN}✅ All agents started${NC}"
echo "   Canary PID: $CANARY_PID"
echo "   Monitoring PID: $MONITORING_PID"
echo "   Response PID: $RESPONSE_PID"
echo "   Communication PID: $COMMUNICATION_PID"

# Wait for agents to register
echo -e "\n${YELLOW}3️⃣  Waiting for agent registration...${NC}"
sleep 10

# Check if agents are still running
echo -e "\n${YELLOW}Checking if agents are alive...${NC}"
for pid in $CANARY_PID $MONITORING_PID $RESPONSE_PID $COMMUNICATION_PID; do
    if ps -p $pid > /dev/null; then
        echo -e "   ${GREEN}✅ PID $pid is running${NC}"
    else
        echo -e "   ${RED}❌ PID $pid has died${NC}"
    fi
done

# Check registry
if [ -f "agent_registry.json" ]; then
    AGENT_COUNT=$(python -c "import json; data=json.load(open('agent_registry.json')); print(len(data))" 2>/dev/null)
    echo -e "\n   ${GREEN}✅ $AGENT_COUNT agents registered${NC}"
    
    # Show registered agents
    echo -e "\n   Registered agents:"
    python -c "
import json
try:
    data = json.load(open('agent_registry.json'))
    for name in data:
        print(f'   - {name}')
except Exception as e:
    print(f'   Error reading registry: {e}')
"
else
    echo -e "\n   ${RED}❌ No registry file created!${NC}"
    echo -e "   Agents may have crashed. Check logs:"
    echo "   - logs/canary_startup.log"
    echo "   - logs/monitoring_startup.log"
    echo "   - logs/response_startup.log"
    echo "   - logs/communication_startup.log"
    
    # Show last few lines of each log
    echo -e "\n   ${YELLOW}Last errors from logs:${NC}"
    for log in logs/*_startup.log; do
        if [ -f "$log" ]; then
            echo -e "\n   ${log}:"
            tail -5 "$log"
        fi
    done
    
    # Cleanup and exit
    echo -e "\n${RED}Agents failed to register. Cleaning up...${NC}"
    kill $MOCK_PID $CANARY_PID $MONITORING_PID $RESPONSE_PID $COMMUNICATION_PID 2>/dev/null
    exit 1
fi

# Run E2E tests
echo -e "\n${GREEN}4️⃣  Running End-to-End Tests...${NC}"
echo "   This will take ~2-3 minutes to complete all scenarios"
echo ""
PYTHONPATH=$(pwd) python e2e_test_pipeline.py

# Capture test PID for cleanup
TEST_PID=$!

# Cleanup function
cleanup() {
    echo -e "\n\n${YELLOW}🛑 Shutting down all services...${NC}"
    
    kill $MOCK_PID 2>/dev/null
    kill $CANARY_PID 2>/dev/null
    kill $MONITORING_PID 2>/dev/null
    kill $RESPONSE_PID 2>/dev/null
    kill $COMMUNICATION_PID 2>/dev/null
    kill $TEST_PID 2>/dev/null
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    echo ""
    echo "📂 Check logs/ directory for detailed execution logs"
    echo "📋 Check agent_registry.json for agent addresses"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Wait for test to complete
wait $TEST_PID

# Auto cleanup after tests
cleanup