"""
Test Lava Integration (CORRECTED - No Anthropic key needed!)
Quick test to verify Lava + Claude Sonnet 3.5 is working
"""

import asyncio
from services.lava_service import lava_service
from loguru import logger
import os

async def test_lava_connection():
    """Test basic Lava connection"""
    print("\n" + "="*60)
    print("🌊 TESTING LAVA AI INTEGRATION")
    print("="*60)
    
    # Check environment variables
    print("\n1️⃣ Checking Environment Variables...")
    lava_token = os.getenv("LAVA_FORWARD_TOKEN")
    
    if not lava_token:
        print("❌ LAVA_FORWARD_TOKEN not set!")
        print("   Get it from: https://lavapayments.com/dashboard/build/secret-keys")
        print("\n   Steps:")
        print("   1. Sign up at lavapayments.com")
        print("   2. Go to Build > Secret Keys")
        print("   3. Copy 'Self Forward Token'")
        print("   4. Add to .env: LAVA_FORWARD_TOKEN=lsk_...")
        return False
    else:
        print(f"✅ LAVA_FORWARD_TOKEN: {lava_token[:15]}...")
        print("💰 This token uses your Lava wallet credits ($10 free!)")
    
    # Test incident analysis
    print("\n2️⃣ Testing Incident Analysis...")
    print("   (This will use ~$0.01-0.02 from your Lava wallet)")
    
    test_incident = {
        "alert_id": "TEST-LAVA-001",
        "severity": "HIGH",
        "system_id": "test-server-1",
        "metric_type": "CPU",
        "current_value": 95.0,
        "expected_value": 40.0,
        "confidence": 0.9
    }
    
    try:
        result = await lava_service.analyze_incident(test_incident)
        
        print("\n✅ Lava + Claude Analysis Complete!")
        print(f"   Recommendation: {result.get('recommendation')}")
        print(f"   Confidence: {result.get('confidence', 0):.2f}")
        print(f"   Reasoning: {result.get('reasoning', 'N/A')}")
        print(f"   Severity: {result.get('severity', 'N/A')}")
        
        print("\n💰 Cost Tracking:")
        print("   ✅ Request charged to Lava wallet")
        print("   ✅ Check dashboard for token usage & cost")
        print("   Dashboard: https://lavapayments.com/dashboard/monetize/explore")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        print("\nTroubleshooting:")
        print("1. Verify Lava token is correct (starts with 'lsk_')")
        print("2. Check Lava wallet has funds:")
        print("   https://lavapayments.com/dashboard/wallet/billing")
        print("3. Add $10-20 to wallet if empty")
        return False

async def test_failure_prediction():
    """Test failure prediction"""
    print("\n3️⃣ Testing Failure Prediction...")
    
    test_metrics = {
        "cpu_usage": 85.0,
        "memory_usage": 92.0,
        "disk_usage": 45.0,
        "network_latency": 120.0,
        "error_count": 15
    }
    
    try:
        result = await lava_service.predict_failure(test_metrics)
        
        print("✅ Prediction Complete!")
        print(f"   Failure Type: {result.get('failure_type')}")
        print(f"   Probability: {result.get('failure_probability', 0):.2%}")
        print(f"   Action: {result.get('preventive_action')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prediction Failed: {e}")
        return False

async def main():
    print("🚀 SuraAI - Lava Integration Test")
    print("   Using Claude Sonnet 3.5 through Lava's API")
    print("   No separate Anthropic key needed!\n")
    
    # Run tests
    test1 = await test_lava_connection()
    
    if test1:
        test2 = await test_failure_prediction()
    else:
        test2 = False
        print("\n⏭️  Skipping test 2 (test 1 failed)")
    
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Incident Analysis: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Failure Prediction: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if test1 and test2:
        print("\n🎉 All tests passed! Lava integration working!")
        print("\n📝 Next Steps:")
        print("1. Update agents/response/intelligent_response_agent.py")
        print("   to import from lava_service instead of groq_service")
        print("2. Run: python e2e_test_pipeline.py")
        print("3. Check Lava dashboard for usage/costs")
        print("\n💰 You're using your $10 Lava credit - no extra API keys!")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        print("\nMost common issue: Need to fund Lava wallet")
        print("Fix: https://lavapayments.com/dashboard/wallet/billing")
    
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())