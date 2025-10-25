#!/usr/bin/env python3
"""
Diagnose Agentverse Connection Issues
Run this to find out exactly what's wrong with agent communication
"""

import json
import subprocess
import time
import requests
from pathlib import Path
import sys

def check_agent_logs():
    """Check agent logs for connection status"""
    print("\n1️⃣ Checking Agent Logs for Agentverse Connection...")
    print("="*70)
    
    agents = [
        "canary_agent.log",
        "monitoring_agent.log", 
        "response_agent.log",
        "communication_agent.log"
    ]
    
    findings = {}
    
    for agent in agents:
        log_file = Path(f"logs/{agent}")
        if not log_file.exists():
            print(f"❌ {agent} - No log file found!")
            findings[agent] = "no_log"
            continue
        
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Check for key indicators
        has_mailbox_started = "Starting mailbox client" in content
        has_almanac_registration = "Registration on Almanac" in content
        has_almanac_complete = "Registering on almanac contract...complete" in content
        has_mailbox_token = "Mailbox access token acquired" in content
        has_errors = "ERROR" in content or "Failed" in content
        
        print(f"\n📋 {agent}:")
        print(f"   Mailbox Started: {'✅' if has_mailbox_started else '❌'}")
        print(f"   Almanac Registration: {'✅' if has_almanac_registration else '❌'}")
        print(f"   Almanac Complete: {'✅' if has_almanac_complete else '❌'}")
        print(f"   Mailbox Token: {'✅' if has_mailbox_token else '❌'}")
        print(f"   Has Errors: {'⚠️ YES' if has_errors else '✅ No'}")
        
        findings[agent] = {
            "mailbox_started": has_mailbox_started,
            "almanac_registration": has_almanac_registration,
            "almanac_complete": has_almanac_complete,
            "mailbox_token": has_mailbox_token,
            "has_errors": has_errors
        }
        
        # Show last few lines
        lines = content.split('\n')
        print(f"\n   Last 5 lines:")
        for line in lines[-5:]:
            if line.strip():
                print(f"   {line[:100]}")
    
    return findings

def check_registry_addresses():
    """Verify registry addresses"""
    print("\n\n2️⃣ Checking Agent Registry Addresses...")
    print("="*70)
    
    registry_file = Path("agent_registry.json")
    if not registry_file.exists():
        print("❌ agent_registry.json NOT FOUND!")
        return None
    
    with open(registry_file, 'r') as f:
        registry = json.load(f)
    
    print("\n📋 Registered Agents:")
    for agent_name, info in registry.items():
        address = info['address']
        port = info['port']
        
        # Validate address format
        is_valid = address.startswith('agent1q') and len(address) > 50
        
        print(f"\n   {agent_name}:")
        print(f"   Address: {address}")
        print(f"   Port: {port}")
        print(f"   Valid Format: {'✅' if is_valid else '❌'}")
        
        if not is_valid:
            print(f"   ⚠️  Address looks incorrect!")
            print(f"   Should start with 'agent1q' and be 63 chars long")
    
    return registry

def check_agent_processes():
    """Check if agents are running"""
    print("\n\n3️⃣ Checking Running Agent Processes...")
    print("="*70)
    
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        
        agent_files = [
            "canary_agent.py",
            "monitoring_agent.py",
            "response_agent.py",
            "communication_agent.py"
        ]
        
        for agent_file in agent_files:
            if agent_file in result.stdout:
                print(f"✅ {agent_file} is running")
            else:
                print(f"❌ {agent_file} is NOT running")
        
    except Exception as e:
        print(f"⚠️  Could not check processes: {e}")

def extract_actual_addresses_from_logs():
    """Extract actual agent addresses from logs"""
    print("\n\n4️⃣ Extracting Actual Addresses from Logs...")
    print("="*70)
    
    agents = {
        "canary_agent": "logs/canary_agent.log",
        "monitoring_agent": "logs/monitoring_agent.log",
        "response_agent": "logs/response_agent.log",
        "communication_agent": "logs/communication_agent.log"
    }
    
    actual_addresses = {}
    
    for agent_name, log_file in agents.items():
        log_path = Path(log_file)
        if not log_path.exists():
            print(f"❌ {agent_name}: No log file")
            continue
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        # Look for "Agent started at agent1q..."
        import re
        match = re.search(r'started at (agent1q[a-z0-9]+)', content)
        
        if match:
            address = match.group(1)
            actual_addresses[agent_name] = address
            print(f"✅ {agent_name}:")
            print(f"   {address}")
        else:
            print(f"❌ {agent_name}: Could not find address in log")
    
    return actual_addresses

def compare_addresses(registry, actual_addresses):
    """Compare registry vs actual addresses"""
    print("\n\n5️⃣ Comparing Registry vs Actual Addresses...")
    print("="*70)
    
    if not registry or not actual_addresses:
        print("❌ Cannot compare - missing data")
        return False
    
    all_match = True
    
    for agent_name, actual_addr in actual_addresses.items():
        if agent_name not in registry:
            print(f"❌ {agent_name}: Not in registry!")
            all_match = False
            continue
        
        registry_addr = registry[agent_name]['address']
        
        if registry_addr == actual_addr:
            print(f"✅ {agent_name}: Addresses MATCH")
        else:
            print(f"❌ {agent_name}: ADDRESS MISMATCH!")
            print(f"   Registry:  {registry_addr}")
            print(f"   Actual:    {actual_addr}")
            all_match = False
    
    return all_match

def check_mock_infrastructure():
    """Check if mock infrastructure is running"""
    print("\n\n6️⃣ Checking Mock Infrastructure...")
    print("="*70)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Mock infrastructure running")
            print(f"   Total systems: {data.get('total_systems', 0)}")
            print(f"   Healthy: {data.get('healthy', 0)}")
            return True
    except Exception as e:
        print(f"❌ Mock infrastructure NOT responding: {e}")
        return False

def generate_recommendations(findings, registry, actual_addresses, addresses_match):
    """Generate actionable recommendations"""
    print("\n\n" + "="*70)
    print("📊 DIAGNOSIS SUMMARY & RECOMMENDATIONS")
    print("="*70)
    
    issues = []
    
    # Check log findings
    for agent, status in findings.items():
        if isinstance(status, dict):
            if not status.get('almanac_complete'):
                issues.append(f"{agent} - Not registered on Almanac")
            if not status.get('mailbox_token'):
                issues.append(f"{agent} - No mailbox token acquired")
    
    # Check address mismatch
    if not addresses_match:
        issues.append("Registry addresses don't match actual agent addresses")
    
    if not issues:
        print("\n✅ All checks passed!")
        print("\n🤔 But agents still not communicating? Try:")
        print("   1. Wait longer (60+ seconds) for Agentverse routing")
        print("   2. Manually verify on https://agentverse.ai/agents")
        print("   3. Check all 4 agents show 'Connected' status")
        print("   4. Restart test pipeline")
    else:
        print("\n⚠️  Found Issues:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n\n🔧 FIXES:")
        
        if not addresses_match:
            print("\n❌ ADDRESS MISMATCH - This is likely the problem!")
            print("\n   Fix:")
            print("   1. Kill all running agents (Ctrl+C)")
            print("   2. Delete agent_registry.json")
            print("   3. Restart agents with: ./setup_e2e_test.sh")
            print("   4. Let them register fresh addresses")
        
        if any("Not registered on Almanac" in issue for issue in issues):
            print("\n❌ ALMANAC REGISTRATION FAILED")
            print("\n   This happens when agents can't reach Almanac")
            print("\n   Fix:")
            print("   1. Check internet connection")
            print("   2. Agents need to reach almanac.fetch.ai")
            print("   3. Wait 30-60 seconds after startup")
            print("   4. Check firewall/network restrictions")
        
        if any("No mailbox token" in issue for issue in issues):
            print("\n❌ MAILBOX TOKEN NOT ACQUIRED")
            print("\n   Fix:")
            print("   1. Verify SEED_PHRASE environment variables are set")
            print("   2. Each agent needs unique seed phrase")
            print("   3. Check .env file has all seed phrases")
            print("   4. Restart agents after setting .env")
        
        print("\n\n💡 QUICK FIX (Try this first):")
        print("="*70)
        print("1. Kill everything:")
        print("   pkill -f 'python.*agent'")
        print("   pkill -f 'mock_infrastructure'")
        print("")
        print("2. Clean slate:")
        print("   rm agent_registry.json")
        print("   rm -rf logs/*.log")
        print("")
        print("3. Restart:")
        print("   ./setup_e2e_test.sh")
        print("")
        print("4. Wait 60 seconds after startup")
        print("")
        print("5. Check Agentverse dashboard:")
        print("   https://agentverse.ai/agents")
        print("   All 4 should show 'Connected'")

def main():
    print("="*70)
    print("🔍 AGENTVERSE CONNECTION DIAGNOSTIC")
    print("="*70)
    print("\nThis will diagnose why agents aren't communicating")
    print("Run this WHILE agents are running")
    print("="*70)
    
    # Run all checks
    findings = check_agent_logs()
    registry = check_registry_addresses()
    check_agent_processes()
    actual_addresses = extract_actual_addresses_from_logs()
    addresses_match = compare_addresses(registry, actual_addresses)
    check_mock_infrastructure()
    
    # Generate recommendations
    generate_recommendations(findings, registry, actual_addresses, addresses_match)
    
    print("\n" + "="*70)
    print("Diagnosis complete!")
    print("="*70)

if __name__ == "__main__":
    main()