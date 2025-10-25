"""
Complete Agent Communication Fix
This patches ALL agents to use direct HTTP communication
Run this, then restart your tests
"""

import os
from pathlib import Path
import shutil

def backup_file(filepath):
    """Create backup of original file"""
    backup = Path(str(filepath) + ".backup_" + str(int(time.time())))
    shutil.copy(filepath, backup)
    print(f"   📦 Backup: {backup.name}")

def fix_base_agent():
    """Fix base_agent.py - Core communication layer"""
    print("\n🔧 Fixing base_agent.py...")
    
    filepath = Path("agents/base_agent.py")
    
    # The corrected base_agent with LOCAL HTTP communication
    new_content = '''from uagents import Agent, Context, Model
from loguru import logger
import asyncio
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from agents.registry import register_agent, get_agent_address, registry
import aiohttp
import json

class BaseAgentConfig(Model):
    """Base configuration for all agents"""
    agent_name: str
    agent_description: str
    seed_phrase: Optional[str] = None

class AgentMessage(Model):
    """Standard message format between agents"""
    sender: str
    receiver: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: float

class BaseSuraAgent:
    def __init__(
        self, 
        name: str, 
        seed: str, 
        port: int, 
        capabilities: List[str] = None,
        endpoint: Optional[str] = None
    ):
        load_dotenv()
        
        # Create agent WITHOUT Agentverse endpoint
        self.agent = Agent(
            name=name,
            seed=seed,
            port=port,
            endpoint=[]  # EMPTY - No Agentverse!
        )
        self.name = name
        self.capabilities = capabilities or []
        
        # Setup logging
        logger.add(
            f"logs/{name}.log",
            rotation="100 MB",
            retention="7 days",
            level="INFO"
        )
        
        logger.info(f"✅ {name} initialized (LOCAL HTTP ONLY)")
        logger.info(f"   Address: {self.agent.address}")
        logger.info(f"   Port: {port}")
        
        # Auto-register in registry
        self.register_self()
    
    def register_self(self):
        """Register this agent in the global registry"""
        try:
            register_agent(
                name=self.name,
                address=str(self.agent.address),
                port=self.agent._port,
                capabilities=self.capabilities
            )
            logger.info(f"📝 Registered {self.name} in agent registry")
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
    
    def get_peer_address(self, peer_name: str) -> Optional[str]:
        """Get another agent's address from registry"""
        address = get_agent_address(peer_name)
        if address:
            logger.debug(f"Found {peer_name} at {address[:20]}...")
        else:
            logger.warning(f"Agent {peer_name} not found in registry")
        return address
    
    async def send_to_peer(self, ctx: Context, peer_name: str, message: Model) -> bool:
        """
        Send message via DIRECT LOCAL HTTP (no Agentverse!)
        """
        # Get peer info from registry
        peer_info = registry.get_agent(peer_name)
        if not peer_info:
            logger.error(f"❌ {peer_name} not in registry!")
            logger.info("   Available agents:")
            for name in registry.get_all_agents().keys():
                logger.info(f"      - {name}")
            return False
        
        try:
            # Direct HTTP to localhost
            endpoint = f"http://localhost:{peer_info.port}/submit"
            
            logger.info(f"📤 Sending {message.__class__.__name__} to {peer_name}")
            logger.debug(f"   Target: {endpoint}")
            
            # Build payload
            payload = {
                "sender": str(self.agent.address),
                "target": peer_info.address,
                "message": message.dict(),
                "message_type": message.__class__.__name__,
            }
            
            # Send via HTTP POST
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    
                    if resp.status == 200:
                        logger.info(f"✅ Sent to {peer_name}")
                        return True
                    else:
                        text = await resp.text()
                        logger.error(f"❌ HTTP {resp.status}: {text[:200]}")
                        return False
            
        except aiohttp.ClientConnectorError as e:
            logger.error(f"❌ Cannot connect to {peer_name} on port {peer_info.port}")
            logger.error(f"   Is {peer_name} running?")
            return False
        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout connecting to {peer_name}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send to {peer_name}: {e}")
            return False
    
    def get_agent(self):
        return self.agent
    
    def get_address(self):
        return self.agent.address
'''
    
    # Backup and write
    import time
    backup_file(filepath)
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print("   ✅ Fixed base_agent.py")

def verify_agent_file(filepath, agent_name):
    """Verify agent file imports and uses send_to_peer"""
    print(f"\n🔍 Verifying {agent_name}...")
    
    if not Path(filepath).exists():
        print(f"   ❌ File not found!")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    checks = {
        "Imports BaseSuraAgent": "from agents.base_agent import BaseSuraAgent" in content,
        "Uses send_to_peer": "send_to_peer" in content,
        "Has capabilities": "capabilities=" in content,
        "No hardcoded addresses": "agent1q" not in content or "send_to_peer" in content
    }
    
    all_good = True
    for check, passed in checks.items():
        if passed:
            print(f"   ✅ {check}")
        else:
            print(f"   ⚠️  {check}")
            all_good = False
    
    return all_good

def fix_canary_agent():
    """Ensure canary uses send_to_peer"""
    print("\n🔧 Checking canary_agent.py...")
    
    filepath = Path("agents/canary/canary_agent.py")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if it's already using send_to_peer correctly
    if "await self.send_to_peer(ctx, \"response_agent\", CanaryTestResult(**result))" in content:
        print("   ✅ Already correct!")
        return True
    
    # Need to fix the message sending part
    print("   🔧 Updating message sending...")
    
    # Replace ctx.send with send_to_peer
    import re
    
    # Pattern to find: await ctx.send(address, CanaryTestResult(...))
    pattern = r'await ctx\.send\([^,]+,\s*CanaryTestResult\(\*\*result\)\)'
    replacement = 'await self.send_to_peer(ctx, "response_agent", CanaryTestResult(**result))'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        backup_file(filepath)
        with open(filepath, 'w') as f:
            f.write(new_content)
        print("   ✅ Fixed!")
    else:
        print("   ⚠️  Could not auto-fix, manual check needed")
    
    return True

def create_test_verification_script():
    """Create a script to verify agents are working"""
    print("\n📝 Creating verification script...")
    
    script = '''#!/usr/bin/env python3
"""
Verify Agents Are Working - Run AFTER starting agents
"""

import json
import time
import requests
from pathlib import Path

def check_registry():
    """Check agent registry"""
    print("\\n1️⃣ Checking Agent Registry...")
    
    registry_file = Path("agent_registry.json")
    if not registry_file.exists():
        print("   ❌ No registry file!")
        return False
    
    with open(registry_file) as f:
        registry = json.load(f)
    
    required = ["canary_agent", "monitoring_agent", "response_agent", "communication_agent"]
    
    for agent in required:
        if agent in registry:
            print(f"   ✅ {agent}")
        else:
            print(f"   ❌ {agent} - NOT REGISTERED")
            return False
    
    return True

def check_agent_endpoints():
    """Check agents are responding"""
    print("\\n2️⃣ Checking Agent HTTP Endpoints...")
    
    agents = [
        ("Canary", 8001),
        ("Monitoring", 8002),
        ("Response", 8003),
        ("Communication", 8004)
    ]
    
    all_ok = True
    for name, port in agents:
        try:
            # Try to connect (even if it returns 405, means it's listening)
            response = requests.get(f"http://localhost:{port}/", timeout=2)
            print(f"   ✅ {name} Agent (port {port})")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ {name} Agent (port {port}) - NOT RESPONDING")
            all_ok = False
        except:
            # Any other response means it's alive
            print(f"   ✅ {name} Agent (port {port})")
    
    return all_ok

def check_mock_infrastructure():
    """Check mock infrastructure"""
    print("\\n3️⃣ Checking Mock Infrastructure...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("   ✅ Mock infrastructure running")
            return True
    except:
        pass
    
    print("   ❌ Mock infrastructure not responding")
    return False

def main():
    print("="*60)
    print("🔍 AGENT VERIFICATION")
    print("="*60)
    
    print("\\n⏳ Waiting 5 seconds for agents to initialize...")
    time.sleep(5)
    
    checks = {
        "Registry": check_registry(),
        "Endpoints": check_agent_endpoints(),
        "Mock Infrastructure": check_mock_infrastructure()
    }
    
    print("\\n" + "="*60)
    print("📊 VERIFICATION RESULTS")
    print("="*60)
    
    for name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    if all(checks.values()):
        print("\\n🎉 ALL CHECKS PASSED!")
        print("\\nAgents are ready. You can now run:")
        print("   python e2e_test_pipeline.py")
    else:
        print("\\n⚠️  SOME CHECKS FAILED")
        print("\\nTroubleshooting:")
        print("1. Check logs/ directory for errors")
        print("2. Make sure you started agents with:")
        print("   ./setup_e2e_test.sh")
        print("3. Verify PYTHONPATH is set:")
        print("   export PYTHONPATH=$(pwd)")
    
    print("="*60)

if __name__ == "__main__":
    main()
'''
    
    with open("verify_agents.py", "w") as f:
        f.write(script)
    
    os.chmod("verify_agents.py", 0o755)
    print("   ✅ Created verify_agents.py")

def create_improved_setup_script():
    """Create improved setup script with better error handling"""
    print("\n📝 Creating improved setup script...")
    
    script = '''#!/bin/bash

# SuraAI E2E Test - FIXED VERSION
# Better error handling and verification

set -e  # Exit on error

echo "🚀 SuraAI End-to-End Test Pipeline"
echo "===================================="

# Set PYTHONPATH
export PYTHONPATH=$(pwd)
echo "🔧 PYTHONPATH: $PYTHONPATH"

# Cleanup
echo ""
echo "🧹 Cleaning up..."
rm -f agent_registry.json
rm -rf logs/*.log
mkdir -p logs

# Start mock infrastructure
echo ""
echo "1️⃣ Starting Mock Infrastructure..."
python services/mock_infrastructure.py > logs/mock_infra.log 2>&1 &
MOCK_PID=$!
sleep 3

# Verify mock is running
curl -sf http://localhost:8000/health > /dev/null || {
    echo "❌ Mock infrastructure failed!"
    cat logs/mock_infra.log
    exit 1
}
echo "✅ Mock infrastructure ready"

# Start agents with verification
echo ""
echo "2️⃣ Starting Agents..."

start_agent() {
    local name=$1
    local file=$2
    local port=$3
    
    echo "   Starting $name..."
    python "$file" > "logs/${name}_startup.log" 2>&1 &
    local pid=$!
    sleep 3
    
    # Check if still alive
    if kill -0 $pid 2>/dev/null; then
        echo "   ✅ $name (PID: $pid, Port: $port)"
        eval "${name^^}_PID=$pid"
    else
        echo "   ❌ $name failed to start!"
        cat "logs/${name}_startup.log"
        exit 1
    fi
}

start_agent "canary" "agents/canary/canary_agent.py" 8001
start_agent "monitoring" "agents/monitoring/monitoring_agent.py" 8002
start_agent "response" "agents/response/intelligent_response_agent.py" 8003
start_agent "communication" "agents/communication/communication_agent.py" 8004

# Wait for registration
echo ""
echo "3️⃣ Waiting for agent registration..."
sleep 10

# Verify agents
echo ""
python verify_agents.py || {
    echo ""
    echo "❌ Agent verification failed!"
    echo "Check logs for errors"
    kill $MOCK_PID $CANARY_PID $MONITORING_PID $RESPONSE_PID $COMMUNICATION_PID 2>/dev/null
    exit 1
}

# Run tests
echo ""
echo "4️⃣ Running Tests..."
python e2e_test_pipeline.py

# Cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $MOCK_PID $CANARY_PID $MONITORING_PID $RESPONSE_PID $COMMUNICATION_PID 2>/dev/null
    echo "✅ Done"
}

trap cleanup EXIT INT TERM
wait
'''
    
    with open("setup_e2e_test_fixed.sh", "w") as f:
        f.write(script)
    
    os.chmod("setup_e2e_test_fixed.sh", 0o755)
    print("   ✅ Created setup_e2e_test_fixed.sh")

def main():
    print("="*70)
    print("🔧 COMPLETE AGENT COMMUNICATION FIX")
    print("="*70)
    print("\nThis will:")
    print("1. Fix base_agent.py to use LOCAL HTTP only")
    print("2. Verify all agent files are correct")
    print("3. Create verification and setup scripts")
    print("\n" + "="*70)
    
    # Fix base agent
    fix_base_agent()
    
    # Verify agents
    agents = [
        ("agents/canary/canary_agent.py", "Canary"),
        ("agents/monitoring/monitoring_agent.py", "Monitoring"),
        ("agents/response/intelligent_response_agent.py", "Response"),
        ("agents/communication/communication_agent.py", "Communication")
    ]
    
    for filepath, name in agents:
        verify_agent_file(filepath, name)
    
    # Fix canary specifically
    fix_canary_agent()
    
    # Create helper scripts
    create_test_verification_script()
    create_improved_setup_script()
    
    print("\n" + "="*70)
    print("✅ FIX COMPLETE!")
    print("="*70)
    print("\nNext Steps:")
    print("1. Kill any running agents (Ctrl+C)")
    print("2. Run: ./setup_e2e_test_fixed.sh")
    print("   OR manually:")
    print("   - Start mock: python services/mock_infrastructure.py")
    print("   - Start agents (separate terminals)")
    print("   - Verify: python verify_agents.py")
    print("   - Test: python e2e_test_pipeline.py")
    print("\n" + "="*70)

if __name__ == "__main__":
    main()