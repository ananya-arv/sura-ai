#!/bin/bash

# SuraAI E2E Test Pipeline Setup - AGENTVERSE MAILBOX MODE (CORRECTED)
# All critical fixes applied

echo "🚀 SuraAI End-to-End Test Pipeline Setup"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Set PYTHONPATH
export PYTHONPATH=$(pwd):${PYTHONPATH}
echo -e "\n${GREEN}🔧 PYTHONPATH set to: $(pwd)${NC}"

# Check if agent_registry.json has Agentverse addresses
echo -e "\n${YELLOW}Checking agent registry...${NC}"
if [ ! -f "agent_registry.json" ]; then
    echo -e "${RED}❌ agent_registry.json not found!${NC}"
    echo ""
    echo "You need to:"
    echo "1. Start each agent individually"
    echo "2. Connect them to Agentverse mailbox"
    echo "3. Update agent_registry.json with their addresses"
    echo ""
    echo "Run: ./reconnect_agents.sh"
    exit 1
fi

# Verify addresses look like Agentverse addresses
SAMPLE_ADDR=$(python3 -c "import json; d=json.load(open('agent_registry.json')); print(list(d.values())[0]['address'])" 2>/dev/null)
if [[ ! $SAMPLE_ADDR == agent1q* ]]; then
    echo -e "${RED}❌ Registry contains invalid addresses!${NC}"
    echo "Addresses should start with 'agent1q...'"
    echo "Found: $SAMPLE_ADDR"
    echo ""
    echo "Run: ./reconnect_agents.sh to get correct addresses"
    exit 1
fi

echo -e "${GREEN}✅ Registry looks good (Agentverse addresses)${NC}"

# Cleanup old logs
echo -e "\n${YELLOW}Cleaning up old logs...${NC}"
rm -f logs/*.log
mkdir -p logs

# Start mock infrastructure
echo -e "\n${GREEN}1️⃣  Starting Mock Infrastructure...${NC}"
python services/mock_infrastructure.py > logs/mock_infra.log 2>&1 &
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

# Start agents in MAILBOX MODE
echo -e "\n${GREEN}2️⃣  Starting Agents (Agentverse Mailbox Mode)...${NC}"
echo -e "${YELLOW}   Note: Agents will connect to Agentverse, not communicate locally${NC}"

echo "   Starting Canary Agent..."
python agents/canary/canary_agent.py > logs/canary_agent.log 2>&1 &
CANARY_PID=$!
sleep 4

echo "   Starting Monitoring Agent..."
python agents/monitoring/monitoring_agent.py > logs/monitoring_agent.log 2>&1 &
MONITORING_PID=$!
sleep 4

echo "   Starting Response Agent..."
python agents/response/intelligent_response_agent.py > logs/response_agent.log 2>&1 &
RESPONSE_PID=$!
sleep 4

echo "   Starting Communication Agent..."
python agents/communication/communication_agent.py > logs/communication_agent.log 2>&1 &
COMMUNICATION_PID=$!
sleep 4

echo -e "\n   ${GREEN}✅ All agents started${NC}"
echo "   Canary PID: $CANARY_PID"
echo "   Monitoring PID: $MONITORING_PID"
echo "   Response PID: $RESPONSE_PID"
echo "   Communication PID: $COMMUNICATION_PID"

# CRITICAL FIX #3: Longer wait time for Almanac registration
echo -e "\n${YELLOW}3️⃣  Waiting for agents to initialize...${NC}"
echo -e "${BLUE}   (Almanac registration can take 10-30 seconds)${NC}"
sleep 15

# Check if agents are still running
echo -e "\n${YELLOW}Verifying agents are alive...${NC}"

AGENTS_OK=true
for pid in $CANARY_PID $MONITORING_PID $RESPONSE_PID $COMMUNICATION_PID; do
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ PID $pid is running${NC}"
    else
        echo -e "   ${RED}❌ PID $pid has died${NC}"
        AGENTS_OK=false
    fi
done

if [ "$AGENTS_OK" = false ]; then
    echo -e "\n${RED}Some agents crashed. Check logs:${NC}"
    echo "   logs/canary_agent.log"
    echo "   logs/monitoring_agent.log"
    echo "   logs/response_agent.log"
    echo "   logs/communication_agent.log"
    
    echo -e "\n${YELLOW}Showing last errors:${NC}"
    for log in logs/*_agent.log; do
        if [ -f "$log" ]; then
            echo -e "\n${YELLOW}=== $(basename $log) ===${NC}"
            tail -10 "$log" | grep -i "error\|exception\|failed" || tail -5 "$log"
        fi
    done
    
    kill $MOCK_PID $CANARY_PID $MONITORING_PID $RESPONSE_PID $COMMUNICATION_PID 2>/dev/null
    exit 1
fi

# Wait additional time for Almanac registration to complete
echo -e "\n${YELLOW}⏳ Waiting additional 15 seconds for Almanac registration...${NC}"
sleep 15

# Verify Agentverse connection (check logs for successful registration)
echo -e "\n${YELLOW}4️⃣  Checking Agentverse connection status...${NC}"

# Look for successful Almanac registration
ALMANAC_SUCCESS=0
for log in logs/*_agent.log; do
    if grep -q "Registering on almanac contract...complete" "$log" 2>/dev/null; then
        ALMANAC_SUCCESS=$((ALMANAC_SUCCESS + 1))
        AGENT_NAME=$(basename "$log" .log)
        echo -e "   ${GREEN}✅ $AGENT_NAME registered on Almanac${NC}"
    fi
done

if [ $ALMANAC_SUCCESS -lt 4 ]; then
    echo -e "\n   ${YELLOW}⚠️  Only $ALMANAC_SUCCESS/4 agents registered on Almanac${NC}"
    echo "   This is OK if you manually connected them to Agentverse mailbox"
fi

# CRITICAL FIX #6: Manual verification step
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}⚠️  IMPORTANT: Manual Verification Required${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "   Before continuing, verify on Agentverse dashboard:"
echo -e "   ${GREEN}https://agentverse.ai/agents${NC}"
echo ""
echo "   All 4 agents should show:"
echo "   ✅ Status: Connected"
echo "   ✅ Green indicator next to agent name"
echo "   ✅ 'Mailbox' in the connection type"
echo ""
echo -e "${YELLOW}   If agents are NOT connected:${NC}"
echo "   1. Find each agent by address on Agentverse"
echo "   2. Click 'Connect to Mailbox' button"
echo "   3. Wait for 'Connected' status"
echo "   4. Come back and continue this script"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

read -p "   Have you verified all agents are connected on Agentverse? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}⏸️  Pausing for manual verification...${NC}"
    echo ""
    echo "   When ready:"
    echo "   1. Connect agents on Agentverse"
    echo "   2. Press ENTER to continue"
    echo "   3. Or press Ctrl+C to abort"
    echo ""
    read -p "   Press ENTER when all agents are connected..."
fi

# Check e2e_test_pipeline.py has correct addresses
echo -e "\n${YELLOW}5️⃣  Verifying test pipeline configuration...${NC}"
PIPELINE_ADDR=$(python3 -c "
import re
try:
    with open('e2e_test_pipeline.py', 'r') as f:
        content = f.read()
        # Check if it loads from registry
        if 'load_agent_addresses()' in content:
            print('LOADS_FROM_REGISTRY')
        else:
            match = re.search(r'\"canary_agent\": \"(agent1q[a-z0-9]+)\"', content)
            if match:
                print(match.group(1))
except:
    print('ERROR')
" 2>/dev/null)

if [ "$PIPELINE_ADDR" = "LOADS_FROM_REGISTRY" ]; then
    echo -e "   ${GREEN}✅ Test pipeline loads addresses from registry${NC}"
elif [ "$PIPELINE_ADDR" = "ERROR" ]; then
    echo -e "   ${RED}❌ Failed to check pipeline configuration${NC}"
else
    REGISTRY_ADDR=$(python3 -c "import json; d=json.load(open('agent_registry.json')); print(d['canary_agent']['address'])" 2>/dev/null)
    
    if [ "$PIPELINE_ADDR" = "$REGISTRY_ADDR" ]; then
        echo -e "   ${GREEN}✅ Test pipeline addresses match registry${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Address mismatch detected:${NC}"
        echo "   Pipeline: $PIPELINE_ADDR"
        echo "   Registry: $REGISTRY_ADDR"
        echo ""
        echo "   Update AGENTVERSE_ADDRESSES in e2e_test_pipeline.py"
        echo ""
        read -p "   Press ENTER to continue anyway (or Ctrl+C to abort)..."
    fi
fi

# Run E2E tests
echo -e "\n${GREEN}6️⃣  Running End-to-End Tests...${NC}"
echo -e "${YELLOW}   This will take ~2-3 minutes to complete all scenarios${NC}"
echo -e "${YELLOW}   Messages will route through Agentverse mailbox${NC}"
echo -e "${BLUE}   Note: First messages may take 30-60 seconds to route${NC}"
echo ""

python e2e_test_pipeline.py &
TEST_PID=$!

# CRITICAL FIX #7: Better cleanup function
cleanup() {
    echo -e "\n\n${YELLOW}🛑 Shutting down all services...${NC}"
    
    # Kill specific PIDs
    kill $MOCK_PID 2>/dev/null
    kill $CANARY_PID 2>/dev/null
    kill $MONITORING_PID 2>/dev/null
    kill $RESPONSE_PID 2>/dev/null
    kill $COMMUNICATION_PID 2>/dev/null
    
    # Kill test orchestrator and any subprocesses
    if [ ! -z "$TEST_PID" ]; then
        # Kill child processes first
        pkill -P $TEST_PID 2>/dev/null
        # Then kill the main process
        kill $TEST_PID 2>/dev/null
        sleep 2
        # Force kill if still alive
        kill -9 $TEST_PID 2>/dev/null
    fi
    
    # Nuclear option: kill any remaining agent processes
    # Uncomment if you still have zombie processes:
    # pkill -f "canary_agent.py" 2>/dev/null
    # pkill -f "monitoring_agent.py" 2>/dev/null
    # pkill -f "response_agent.py" 2>/dev/null
    # pkill -f "communication_agent.py" 2>/dev/null
    # pkill -f "e2e_test_pipeline.py" 2>/dev/null
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    echo ""
    echo "📂 Check logs/ directory for detailed execution logs"
    echo "📋 Check agent_registry.json for agent addresses"
    echo "🌐 Check https://agentverse.ai/agents for agent activity"
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Test pipeline complete!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    exit 0
}

# Trap Ctrl+C and other termination signals
trap cleanup INT TERM EXIT

# Wait for test to complete
wait $TEST_PID

# Cleanup will be called automatically by trap on exit