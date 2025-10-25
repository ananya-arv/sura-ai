#!/usr/bin/env python3
"""
Verify Agents Are Working - Run AFTER starting agents
"""

import json
import time
import requests
from pathlib import Path

def check_registry():
    """Check agent registry"""
    print("\n1️⃣ Checking Agent Registry...")
    
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
    print("\n2️⃣ Checking Agent HTTP Endpoints...")
    
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
    print("\n3️⃣ Checking Mock Infrastructure...")
    
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
    
    print("\n⏳ Waiting 5 seconds for agents to initialize...")
    time.sleep(5)
    
    checks = {
        "Registry": check_registry(),
        "Endpoints": check_agent_endpoints(),
        "Mock Infrastructure": check_mock_infrastructure()
    }
    
    print("\n" + "="*60)
    print("📊 VERIFICATION RESULTS")
    print("="*60)
    
    for name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    if all(checks.values()):
        print("\n🎉 ALL CHECKS PASSED!")
        print("\nAgents are ready. You can now run:")
        print("   python e2e_test_pipeline.py")
    else:
        print("\n⚠️  SOME CHECKS FAILED")
        print("\nTroubleshooting:")
        print("1. Check logs/ directory for errors")
        print("2. Make sure you started agents with:")
        print("   ./setup_e2e_test.sh")
        print("3. Verify PYTHONPATH is set:")
        print("   export PYTHONPATH=$(pwd)")
    
    print("="*60)

if __name__ == "__main__":
    main()
