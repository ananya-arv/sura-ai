#!/usr/bin/env python3
"""
Verify Lava is Actually Being Used
Check response agent logs and configuration
"""

from pathlib import Path
import json
import re

def check_response_agent_logs():
    """Check what's happening in response agent logs"""
    
    print("="*70)
    print("🔍 CHECKING RESPONSE AGENT LOGS")
    print("="*70)
    
    log_file = Path("logs/response_agent.log")
    
    if not log_file.exists():
        print("❌ No response agent log found!")
        return False
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Critical checks
    checks = {
        "Agent Started": "Response Agent started at" in content,
        "Lava Enabled": "Lava Gateway: ENABLED" in content or "LAVA IS ENABLED" in content,
        "Lava Token Present": "LAVA_FORWARD_TOKEN" not in content or "lsk_" in content,
        "Received Anomalies": "Received anomaly alert" in content,
        "Lava Analysis": "Lava AI" in content or "Consulting Lava" in content,
        "AI Decision": "AI Decision" in content or "AI analysis" in content,
        "Actions Taken": "Executing" in content or "runbook" in content,
    }
    
    print("\n📋 Status Checks:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    # Count key events
    print("\n📊 Event Counts:")
    anomaly_count = content.count("Received anomaly alert")
    lava_request_count = content.count("Lava Request ID:")
    action_count = content.count("runbook")
    ai_analysis_count = content.count("AI analysis") + content.count("AI Analysis")
    fallback_count = content.count("fallback") + content.count("Fallback")
    
    print(f"   Anomalies Received: {anomaly_count}")
    print(f"   Lava Requests Made: {lava_request_count}")
    print(f"   AI Analyses: {ai_analysis_count}")
    print(f"   Actions/Runbooks: {action_count}")
    print(f"   Fallbacks (AI failed): {fallback_count}")
    
    # Show recent errors
    print("\n🔍 Recent Log Entries (last 20 lines):")
    lines = content.split('\n')
    for line in lines[-20:]:
        if line.strip():
            # Highlight important lines
            if 'ERROR' in line or 'Failed' in line:
                print(f"   ❌ {line[:100]}")
            elif 'Lava' in line or 'AI' in line:
                print(f"   🤖 {line[:100]}")
            elif 'anomaly' in line.lower():
                print(f"   ⚠️  {line[:100]}")
            else:
                print(f"   {line[:100]}")
    
    # Diagnosis
    print("\n" + "="*70)
    print("📊 DIAGNOSIS")
    print("="*70)
    
    if lava_request_count == 0:
        print("\n❌ LAVA IS NOT BEING USED!")
        print("\nPossible reasons:")
        print("1. LAVA_FORWARD_TOKEN not set")
        print("2. Response agent not receiving anomalies")
        print("3. Lava service availability check failing")
        print("4. Agent using fallback mode")
        
        if fallback_count > 0:
            print(f"\n⚠️  Found {fallback_count} fallback instances")
            print("   This means Lava was attempted but failed")
        
        if anomaly_count == 0:
            print("\n⚠️  Agent received 0 anomalies")
            print("   Check monitoring agent → response agent communication")
        
        return False
    
    elif lava_request_count < anomaly_count:
        print(f"\n⚠️  PARTIAL LAVA USAGE")
        print(f"   Received {anomaly_count} anomalies")
        print(f"   Made {lava_request_count} Lava requests")
        print(f"   Missing: {anomaly_count - lava_request_count} requests")
        print("\n   Some anomalies were not processed with AI")
        return False
    
    else:
        print(f"\n✅ LAVA IS WORKING!")
        print(f"   Made {lava_request_count} Lava AI requests")
        print(f"   Processed {anomaly_count} anomalies with AI")
        return True

def check_lava_service_config():
    """Check lava_service.py configuration"""
    
    print("\n" + "="*70)
    print("🔧 CHECKING LAVA SERVICE CONFIGURATION")
    print("="*70)
    
    service_file = Path("services/lava_service.py")
    
    if not service_file.exists():
        print("❌ lava_service.py not found!")
        return False
    
    with open(service_file, 'r') as f:
        content = f.read()
    
    # Check initialization
    checks = {
        "Reads LAVA_FORWARD_TOKEN": 'os.getenv("LAVA_FORWARD_TOKEN")' in content,
        "Sets self.available": "self.available = " in content,
        "Has analyze_incident": "async def analyze_incident" in content,
        "Makes HTTP request": "aiohttp" in content or "requests" in content,
        "Returns lava_request_id": "lava_request_id" in content,
    }
    
    print("\n📋 Configuration Checks:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("\n✅ Lava service looks properly configured")
    else:
        print("\n❌ Lava service has configuration issues")
    
    return all_passed

def check_response_agent_imports():
    """Check if response agent imports lava_service"""
    
    print("\n" + "="*70)
    print("📦 CHECKING RESPONSE AGENT IMPORTS")
    print("="*70)
    
    response_file = Path("agents/response/intelligent_response_agent.py")
    
    if not response_file.exists():
        print("❌ intelligent_response_agent.py not found!")
        # Try old name
        response_file = Path("agents/response/response_agent.py")
        if not response_file.exists():
            print("❌ response_agent.py also not found!")
            return False
    
    with open(response_file, 'r') as f:
        content = f.read()
    
    checks = {
        "Imports lava_service": "from services.lava_service import lava_service" in content,
        "Checks lava_service.available": "lava_service.available" in content,
        "Calls analyze_incident": "lava_service.analyze_incident" in content,
        "Updates lava_requests counter": 'set("lava_requests"' in content or "lava_requests" in content,
        "Has error handling": "try:" in content and "except" in content,
    }
    
    print("\n📋 Import Checks:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    # Check initialization
    if 'if not lava_service.available' in content:
        print("\n⚠️  Agent checks Lava availability on init")
        print("   If token missing, agent won't start!")
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("\n✅ Response agent properly imports and uses Lava")
    else:
        print("\n❌ Response agent has import/usage issues")
    
    return all_passed

def check_environment():
    """Check .env file for LAVA_FORWARD_TOKEN"""
    
    print("\n" + "="*70)
    print("🔐 CHECKING ENVIRONMENT VARIABLES")
    print("="*70)
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    token = os.getenv("LAVA_FORWARD_TOKEN")
    
    if not token:
        print("\n❌ LAVA_FORWARD_TOKEN is NOT SET")
        print("\nThis is why Lava isn't being used!")
        print("\nFix:")
        print("1. Get token from: https://lavapayments.com/dashboard/build/secret-keys")
        print("2. Add to .env:")
        print("   LAVA_FORWARD_TOKEN=lsk_live_your_token_here")
        print("3. Restart agents")
        return False
    
    else:
        print(f"\n✅ LAVA_FORWARD_TOKEN is set")
        print(f"   Length: {len(token)} chars")
        print(f"   Starts with: {token[:10]}...")
        
        if not token.startswith("lsk_"):
            print("\n⚠️  Token doesn't start with 'lsk_'")
            print("   This might not be a valid Lava token")
            return False
        
        print("\n✅ Token format looks valid")
        return True

def main():
    print("\n🔍 LAVA USAGE VERIFICATION")
    print("="*70)
    print("This will check if Lava AI is actually being used\n")
    
    results = {
        "Environment": check_environment(),
        "Lava Service Config": check_lava_service_config(),
        "Response Agent Imports": check_response_agent_imports(),
        "Response Agent Logs": check_response_agent_logs(),
    }
    
    print("\n\n" + "="*70)
    print("📊 FINAL VERDICT")
    print("="*70)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check}")
    
    print("\n" + "="*70)
    
    if all(results.values()):
        print("🎉 LAVA IS WORKING!")
        print("\nAll checks passed. Lava AI is being used properly.")
    
    elif results["Environment"]:
        print("⚠️  LAVA CONFIGURED BUT NOT WORKING")
        print("\nToken is set but something else is broken.")
        print("Check the specific failures above.")
        
        if not results["Response Agent Logs"]:
            print("\n💡 Most likely issue:")
            print("   Response agent not receiving anomaly alerts")
            print("   OR")
            print("   Lava requests failing silently")
            print("\n   Check logs/response_agent.log for errors")
    
    else:
        print("❌ LAVA IS NOT CONFIGURED")
        print("\nLAVA_FORWARD_TOKEN is missing!")
        print("\nThis is a DEMO/SIMULATION mode:")
        print("  ✅ System works without AI")
        print("  ✅ Uses rule-based decisions")
        print("  ❌ No actual AI analysis")
        print("  ❌ No cost tracking")
        print("\nTo enable Lava AI:")
        print("  1. Get token: https://lavapayments.com/dashboard/build/secret-keys")
        print("  2. Add to .env: LAVA_FORWARD_TOKEN=lsk_...")
        print("  3. Restart agents")
        print("  4. Run this script again to verify")
    
    print("="*70)

if __name__ == "__main__":
    main()