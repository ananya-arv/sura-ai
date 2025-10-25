"""
Diagnose why agents aren't registering
Run this to see what's going wrong
"""

import subprocess
import time
import os
import json
from pathlib import Path

def check_agent_file(agent_file):
    """Check if agent file can be imported"""
    print(f"\n🔍 Checking {agent_file}...")
    
    try:
        result = subprocess.run(
            ['python', '-c', f'import {agent_file.replace("/", ".").replace(".py", "")}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"   ✅ Imports successfully")
            return True
        else:
            print(f"   ❌ Import failed!")
            print(f"   Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Import timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_agent_startup(agent_file, timeout=10):
    """Try to start an agent and see what happens"""
    print(f"\n🚀 Testing {agent_file} startup...")
    
    try:
        # Start agent
        process = subprocess.Popen(
            ['python', agent_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"   PID: {process.pid}")
        print(f"   Waiting {timeout} seconds...")
        
        # Wait and capture output
        time.sleep(timeout)
        
        # Check if still running
        poll = process.poll()
        
        if poll is None:
            print(f"   ✅ Agent is RUNNING")
            
            # Check registry
            if Path("agent_registry.json").exists():
                with open("agent_registry.json", "r") as f:
                    registry = json.load(f)
                    agent_name = agent_file.split("/")[-1].replace("_agent.py", "_agent")
                    if agent_name in registry:
                        print(f"   ✅ Agent REGISTERED in registry!")
                    else:
                        print(f"   ⚠️  Agent running but NOT in registry")
                        print(f"      Looking for: {agent_name}")
                        print(f"      Registry has: {list(registry.keys())}")
            else:
                print(f"   ⚠️  No registry file created")
            
            # Kill it
            process.terminate()
            process.wait(timeout=5)
            return True
            
        else:
            print(f"   ❌ Agent EXITED with code {poll}")
            
            # Show output
            stdout, stderr = process.communicate()
            
            if stderr:
                print(f"\n   📛 STDERR:")
                print(f"   {stderr[:500]}")
            
            if stdout:
                print(f"\n   📋 STDOUT:")
                print(f"   {stdout[:500]}")
            
            return False
            
    except Exception as e:
        print(f"   ❌ Failed to start: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("\n🔧 Checking Environment...")
    
    # Check .env
    if Path(".env").exists():
        print("   ✅ .env file exists")
        
        # Check for required vars
        from dotenv import load_dotenv
        load_dotenv()
        
        required = [
            "CANARY_SEED_PHRASE",
            "MONITORING_SEED_PHRASE",
            "RESPONSE_SEED_PHRASE",
            "COMMUNICATION_SEED_PHRASE"
        ]
        
        all_set = True
        for var in required:
            val = os.getenv(var)
            if val:
                print(f"   ✅ {var}: {val[:10]}...")
            else:
                print(f"   ❌ {var}: NOT SET")
                all_set = False
        
        return all_set
    else:
        print("   ❌ .env file NOT FOUND")
        return False

def check_mock_infrastructure():
    """Check if mock infrastructure is needed and running"""
    print("\n🏗️  Checking Mock Infrastructure...")
    
    try:
        import requests
        resp = requests.get("http://localhost:8000/health", timeout=2)
        if resp.status_code == 200:
            print("   ✅ Mock infrastructure is running")
            return True
        else:
            print(f"   ⚠️  Mock returned {resp.status_code}")
            return False
    except:
        print("   ❌ Mock infrastructure NOT running")
        print("   Start it with: python services/mock_infrastructure.py")
        return False

def main():
    print("="*70)
    print("🔍 AGENT REGISTRATION DIAGNOSTICS")
    print("="*70)
    
    # Step 1: Environment
    env_ok = check_environment()
    
    # Step 2: Mock infrastructure
    mock_ok = check_mock_infrastructure()
    
    # Step 3: Clean slate
    print("\n🧹 Cleaning up...")
    if Path("agent_registry.json").exists():
        os.remove("agent_registry.json")
        print("   Removed old registry")
    
    # Step 4: Test each agent
    agents = [
        "agents/canary/canary_agent.py",
        "agents/monitoring/monitoring_agent.py",
        "agents/response/intelligent_response_agent.py",
        "agents/communication/communication_agent.py"
    ]
    
    results = {}
    for agent in agents:
        if not Path(agent).exists():
            print(f"\n❌ {agent} NOT FOUND")
            results[agent] = False
            continue
        
        # Try to start it
        success = test_agent_startup(agent, timeout=8)
        results[agent] = success
        
        # Clean up registry between tests
        if Path("agent_registry.json").exists():
            os.remove("agent_registry.json")
        
        time.sleep(2)
    
    # Summary
    print("\n" + "="*70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*70)
    
    print(f"\nEnvironment: {'✅ OK' if env_ok else '❌ ISSUES'}")
    print(f"Mock Infrastructure: {'✅ OK' if mock_ok else '❌ NOT RUNNING'}")
    
    print("\nAgent Status:")
    for agent, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"  {agent.split('/')[-1]}: {status}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if not env_ok:
        print("\n1. FIX ENVIRONMENT VARIABLES:")
        print("   Run: python fix_env.py")
        print("   Make sure all seed phrases are set")
    
    if not mock_ok:
        print("\n2. START MOCK INFRASTRUCTURE:")
        print("   In a separate terminal:")
        print("   python services/mock_infrastructure.py")
    
    if not all(results.values()):
        print("\n3. CHECK FAILING AGENTS:")
        for agent, success in results.items():
            if not success:
                print(f"\n   {agent}:")
                print(f"   - Check logs/  directory")
                print(f"   - Run directly: python {agent}")
                print(f"   - Look for error messages")
    
    if all(results.values()) and env_ok and mock_ok:
        print("\n✅ ALL CHECKS PASSED!")
        print("\n   Agents should work now. Try:")
        print("   ./setup_e2e_test.sh")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()