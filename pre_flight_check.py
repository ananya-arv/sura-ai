"""
Pre-Flight Check - Run this BEFORE spending Lava credits!
Verifies all components are configured correctly
"""

import os
import sys
from pathlib import Path
import importlib.util

def check_env_vars():
    """Check required environment variables"""
    print("\n1️⃣  Checking Environment Variables...")
    print("="*60)
    
    checks = {
        "LAVA_FORWARD_TOKEN": os.getenv("LAVA_FORWARD_TOKEN"),
        "CANARY_SEED_PHRASE": os.getenv("CANARY_SEED_PHRASE"),
        "MONITORING_SEED_PHRASE": os.getenv("MONITORING_SEED_PHRASE"),  
        "RESPONSE_SEED_PHRASE": os.getenv("RESPONSE_SEED_PHRASE"),
        "COMMUNICATION_SEED_PHRASE": os.getenv("COMMUNICATION_SEED_PHRASE")
    }
    
    all_good = True
    for key, value in checks.items():
        if value:
            masked = f"{value[:10]}..." if len(value) > 10 else value
            print(f"✅ {key}: {masked}")
        else:
            print(f"⚠️  {key}: NOT SET (using defaults)")
            if key == "LAVA_FORWARD_TOKEN":
                print("   → AI features will be DISABLED")
                print("   → System will use rule-based decisions")
            all_good = False
    
    return all_good

def check_files():
    """Check required files exist"""
    print("\n2️⃣  Checking Required Files...")
    print("="*60)
    
    # Must have files
    critical_files = [
        "agents/base_agent.py",
        "agents/registry.py",
        "agents/canary/canary_agent.py",
        "agents/monitoring/monitoring_agent.py",
        "agents/communication/communication_agent.py",
        "services/lava_service.py",
        "services/mock_infrastructure.py",
        "e2e_test_pipeline.py"
    ]
    
    # Need at least one response agent
    response_agents = [
        "agents/response/response_agent.py",
        "agents/response/intelligent_response_agent.py"
    ]
    
    all_critical_exist = True
    for file in critical_files:
        path = Path(file)
        if path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING!")
            all_critical_exist = False
    
    # Check response agents
    response_agent_exists = False
    for file in response_agents:
        path = Path(file)
        if path.exists():
            print(f"✅ {file}")
            response_agent_exists = True
        else:
            print(f"⚠️  {file} - optional")
    
    if not response_agent_exists:
        print(f"❌ No response agent found! Need at least one:")
        print(f"   - response_agent.py (basic)")
        print(f"   - intelligent_response_agent.py (AI-enhanced)")
        return False
    
    return all_critical_exist

def check_imports():
    """Check Python imports work"""
    print("\n3️⃣  Checking Python Imports...")
    print("="*60)
    
    imports_to_check = [
        ("uagents", "Fetch.ai uAgents"),
        ("aiohttp", "HTTP client"),
        ("loguru", "Logging"),
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic")
    ]
    
    all_imports_ok = True
    for module, description in imports_to_check:
        try:
            __import__(module)
            print(f"✅ {module} ({description})")
        except ImportError:
            print(f"❌ {module} - NOT INSTALLED!")
            print(f"   Install with: pip install {module}")
            all_imports_ok = False
    
    return all_imports_ok

def check_agent_communication():
    """Check agents use send_to_peer"""
    print("\n4️⃣  Checking Agent Communication Methods...")
    print("="*60)
    
    files_to_check = {
        "agents/canary/canary_agent.py": "send_to_peer",
        "agents/monitoring/monitoring_agent.py": "send_to_peer",
    }
    
    # Check whichever response agent exists
    response_files = [
        "agents/response/response_agent.py",
        "agents/response/intelligent_response_agent.py"
    ]
    
    for resp_file in response_files:
        if Path(resp_file).exists():
            files_to_check[resp_file] = "send_to_peer"
            break
    
    all_correct = True
    for file, method in files_to_check.items():
        path = Path(file)
        if path.exists():
            content = path.read_text()
            if method in content:
                print(f"✅ {file} uses {method}")
            else:
                print(f"❌ {file} missing {method}!")
                print(f"   Still using hardcoded addresses!")
                all_correct = False
        else:
            print(f"⚠️  {file} not found (skipping)")
    
    return all_correct

def check_lava_service():
    """Check Lava service configuration"""
    print("\n5️⃣  Checking Lava Service...")
    print("="*60)
    
    try:
        # Import without running
        spec = importlib.util.spec_from_file_location("lava_service", "services/lava_service.py")
        lava_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lava_module)
        
        service = lava_module.lava_service
        
        print(f"✅ Lava service loaded")
        print(f"   Available: {service.available}")
        print(f"   Model: {service.model}")
        
        if not service.available:
            print("\n⚠️  Lava AI is DISABLED")
            print("   Reason: LAVA_FORWARD_TOKEN not set")
            print("   Impact: System will use rule-based decisions (still works!)")
            print("\n   To enable AI:")
            print("   1. Get token: https://lavapayments.com/dashboard/build/secret-keys")
            print("   2. Add to .env: LAVA_FORWARD_TOKEN=lsk_...")
            print("   3. Restart agents")
            return "warning"
        
        return True
        
    except Exception as e:
        print(f"❌ Lava service error: {e}")
        return False

def check_logs_directory():
    """Ensure logs directory exists"""
    print("\n6️⃣  Checking Logs Directory...")
    print("="*60)
    
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Created logs/ directory")
    else:
        print("✅ logs/ directory exists")
    
    return True

def generate_summary(checks):
    """Generate final summary"""
    print("\n" + "="*60)
    print("📊 PRE-FLIGHT CHECK SUMMARY")
    print("="*60)
    
    passed = sum(1 for c in checks.values() if c is True)
    warnings = sum(1 for c in checks.values() if c == "warning")
    failed = sum(1 for c in checks.values() if c is False)
    
    print(f"\n✅ Passed: {passed}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"❌ Failed: {failed}")
    
    if failed > 0:
        print("\n❌ CANNOT RUN TESTS")
        print("   Fix the failed checks above before proceeding")
        return False
    
    if warnings > 0:
        print("\n⚠️  CAN RUN TESTS (with limitations)")
        print("   AI features disabled, but rule-based system works")
        print("\n   Options:")
        print("   1. Run tests now with rule-based decisions (FREE)")
        print("   2. Set up Lava token first for AI features ($)")
        return "warning"
    
    print("\n✅ ALL CHECKS PASSED")
    print("   Ready to run full tests with Lava AI!")
    return True

def main():
    print("\n🔍 SURAAI PRE-FLIGHT CHECK")
    print("="*60)
    print("This checks everything BEFORE spending Lava credits")
    print("="*60)
    
    checks = {
        "env_vars": check_env_vars(),
        "files": check_files(),
        "imports": check_imports(),
        "communication": check_agent_communication(),
        "lava": check_lava_service(),
        "logs": check_logs_directory()
    }
    
    result = generate_summary(checks)
    
    if result is False:
        print("\n🛑 Do NOT run tests yet - fix issues first")
        sys.exit(1)
    elif result == "warning":
        print("\n💡 RECOMMENDATION:")
        print("   Run tests in rule-based mode first (no cost)")
        print("   Then add Lava token later for AI features")
        print("\n   Command: python e2e_test_pipeline.py")
        sys.exit(0)
    else:
        print("\n🚀 READY TO RUN TESTS!")
        print("\n   Next steps:")
        print("   1. Start mock: python services/mock_infrastructure.py")
        print("   2. Start agents: ./setup_e2e_test.sh")
        print("   OR")
        print("   1. Test Lava first: python test_lava.py")
        print("   2. Then full test: ./setup_e2e_test.sh")
        sys.exit(0)

if __name__ == "__main__":
    main()