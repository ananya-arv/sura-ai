import asyncio
import requests
from loguru import logger
import time

BASE_URL = "http://localhost:8000"

async def run_demo():
    """Run the complete SuraAI demo scenario"""
    
    logger.info("=" * 70)
    logger.info("🎬 SURAAI DEMO: Preventing the Next CrowdStrike Disaster")
    logger.info("=" * 70)
    
    # Scenario 1: Canary catches bad update
    logger.info("\n📦 SCENARIO 1: Bad Update Deployment")
    logger.info("-" * 70)
    logger.info("Attempting to deploy UPDATE-BAD-001 to 1000 systems...")
    
    await asyncio.sleep(2)
    logger.info("🐦 Canary Agent: Testing on 1 system (0.1% of fleet)...")
    await asyncio.sleep(3)
    logger.info("⚠️  Canary Agent: ERROR DETECTED! System crashed!")
    await asyncio.sleep(1)
    logger.info("🚑 Response Agent: AUTOMATIC ROLLBACK INITIATED")
    await asyncio.sleep(2)
    logger.info("✅ Result: 999 systems SAVED from bad update!")
    logger.info("💰 Estimated savings: $5.3 BILLION (based on CrowdStrike incident)")
    
    # Scenario 2: Anomaly detection
    logger.info("\n\n👁️  SCENARIO 2: Real-time Anomaly Detection")
    logger.info("-" * 70)
    logger.info("Monitoring 100 production systems...")
    
    await asyncio.sleep(2)
    logger.info("📊 Monitoring Agent: CPU spike detected on server-42!")
    logger.info("   Normal: 35% | Current: 95%")
    await asyncio.sleep(1)
    logger.info("🤖 Lava AI Analysis: HIGH confidence (0.92) - Memory leak detected")
    await asyncio.sleep(1)
    logger.info("🚑 Response Agent: Auto-scaling +3 instances")
    await asyncio.sleep(2)
    logger.info("🚑 Response Agent: Isolating problematic service")
    await asyncio.sleep(1)
    logger.info("✅ System stabilized in 8 seconds (vs 45min manual response)")
    
    # Scenario 3: AWS-style outage
    logger.info("\n\n☁️  SCENARIO 3: Regional Outage (AWS-style)")
    logger.info("-" * 70)
    logger.info("Simulating US-EAST-1 failure...")
    
    await asyncio.sleep(2)
    logger.info("🚨 Monitoring Agent: Region latency: 50ms → 5000ms")
    logger.info("🚨 Monitoring Agent: Error rate: 0.1% → 85%")
    await asyncio.sleep(1)
    logger.info("🚑 Response Agent: EMERGENCY FAILOVER initiated")
    await asyncio.sleep(1)
    logger.info("   • Rerouting traffic to US-WEST-2")
    logger.info("   • Spinning up backup infrastructure")
    logger.info("   • Updating DNS records")
    await asyncio.sleep(2)
    logger.info("📢 Communication Agent: Notifying stakeholders")
    await asyncio.sleep(1)
    logger.info("✅ Failover complete in 47 seconds")
    logger.info("   • Zero customer-facing downtime")
    logger.info("   • 6.5M users protected")
    
    # Summary
    logger.info("\n\n" + "=" * 70)
    logger.info("�� DEMO SUMMARY")
    logger.info("=" * 70)
    logger.info("✅ 3 major incidents prevented autonomously")
    logger.info("✅ $5.3B+ in potential losses avoided")
    logger.info("✅ 6.5M+ users protected from outages")
    logger.info("✅ Average response time: <60 seconds (vs hours manually)")
    logger.info("\n💡 SuraAI: The immune system your infrastructure deserves")
    logger.info("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_demo())
