"""
FULL PIPELINE TEST - All 4 Agents Working Together

This demonstrates the complete SuraAI pipeline:
1. Canary Agent tests updates before deployment
2. Monitoring Agent detects anomalies in real-time
3. Response Agent takes action on incidents
4. Communication Agent notifies stakeholders

Prerequisites (run in separate terminals):
1. Terminal 1: python services/mock_infrastructure.py
2. Terminal 2: python agents/canary/canary_agent.py
3. Terminal 3: python agents/monitoring/monitoring_agent.py
4. Terminal 4: python agents/response/intelligent_response_agent.py
5. Terminal 5: python agents/communication/communication_agent.py
6. Terminal 6: python full_pipeline_test.py (this file)

Agent Flow:
  Update → Canary → Response → Communication
  Monitoring → Response → Communication
"""
import asyncio
import aiohttp
from uagents import Agent, Context, Model
from typing import List
from loguru import logger
import time
import os

MOCK_API = "http://localhost:8000"

# ============================================================================
# MESSAGE MODELS (Must match your agents)
# ============================================================================

class UpdatePackage(Model):
    """Update to send to Canary Agent"""
    update_id: str
    version: str
    description: str
    target_systems: List[str]
    timestamp: float

class CanaryTestResult(Model):
    """Result from Canary Agent"""
    update_id: str
    success: bool
    affected_systems: int
    error_rate: float
    latency_impact: float
    recommendation: str
    details: str

class AnomalyAlert(Model):
    """Alert from Monitoring Agent"""
    alert_id: str
    severity: str
    system_id: str
    metric_type: str
    current_value: float
    expected_value: float
    confidence: float
    timestamp: float
    recommendation: str

class ResponseAction(Model):
    """Action taken by Response Agent"""
    action_id: str
    action_type: str
    target_systems: List[str]
    reason: str
    status: str
    timestamp: float

class StatusUpdate(Model):
    """Status update from Communication Agent"""
    incident_id: str
    status: str
    title: str
    description: str
    affected_services: List[str]
    timestamp: float

# ============================================================================
# TEST COORDINATOR AGENT
# ============================================================================

test_agent = Agent(
    name="test_coordinator",
    seed="test_coordinator_seed_12345",
    port=9000
)

# Test metrics
metrics = {
    "scenarios_run": 0,
    "canary_responses": 0,
    "monitoring_alerts": 0,
    "response_actions": 0,
    "communication_updates": 0,
    "pipeline_complete": False
}

@test_agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize and run full pipeline test"""
    
    logger.info("\n" + "🚀"*35)
    logger.info("FULL PIPELINE TEST - All 4 Agents")
    logger.info("🚀"*35)
    logger.info(f"\nTest Coordinator: {test_agent.address}")
    
    await asyncio.sleep(3)
    
    # Check mock infrastructure
    logger.info("\n1️⃣ Checking mock infrastructure...")
    if not await check_mock_api():
        logger.error("❌ Mock infrastructure not running!")
        return
    logger.info("✅ Mock infrastructure ready")
    
    # Get agent addresses
    logger.info("\n2️⃣ Loading agent addresses...")
    agents = load_agent_addresses()
    
    if not any(agents.values()):
        logger.warning("\n⚠️  No agent addresses configured!")
        await show_setup_instructions()
        return
    
    # Show which agents are configured
    logger.info("\n✅ Configured agents:")
    for name, addr in agents.items():
        if addr:
            logger.info(f"   {name}: {addr[:20]}...")
        else:
            logger.warning(f"   {name}: NOT CONFIGURED")
    
    # Run pipeline tests
    logger.info("\n3️⃣ Running full pipeline tests...")
    await run_full_pipeline(ctx, agents)

# ============================================================================
# MESSAGE HANDLERS (Receive responses from agents)
# ============================================================================

@test_agent.on_message(model=CanaryTestResult)
async def handle_canary_result(ctx: Context, sender: str, msg: CanaryTestResult):
    """Canary Agent responded"""
    logger.info("\n" + "="*70)
    logger.info("📨 [1/4] CANARY AGENT RESPONSE")
    logger.info("="*70)
    logger.info(f"Update: {msg.update_id}")
    logger.info(f"Recommendation: {msg.recommendation}")
    logger.info(f"Error Rate: {msg.error_rate:.2%}")
    logger.info(f"Systems Tested: {msg.affected_systems}")
    logger.info(f"Details: {msg.details}")
    
    metrics["canary_responses"] += 1
    
    if msg.recommendation == "ROLLBACK":
        logger.info("\n🛡️  Canary blocked bad update!")
        logger.info("   → This triggers Response Agent in real system")
    elif msg.recommendation == "DEPLOY":
        logger.info("\n✅ Canary approved update")
        logger.info("   → Safe to deploy to all systems")

@test_agent.on_message(model=AnomalyAlert)
async def handle_monitoring_alert(ctx: Context, sender: str, msg: AnomalyAlert):
    """Monitoring Agent sent alert"""
    logger.info("\n" + "="*70)
    logger.info("📨 [2/4] MONITORING AGENT ALERT")
    logger.info("="*70)
    logger.info(f"System: {msg.system_id}")
    logger.info(f"Severity: {msg.severity}")
    logger.info(f"Metric: {msg.metric_type}")
    logger.info(f"Current: {msg.current_value:.1f}")
    logger.info(f"Expected: {msg.expected_value:.1f}")
    logger.info(f"Confidence: {msg.confidence:.2f}")
    
    metrics["monitoring_alerts"] += 1
    
    logger.info("\n👁️  Monitoring detected anomaly!")
    logger.info("   → This triggers Response Agent")

@test_agent.on_message(model=ResponseAction)
async def handle_response_action(ctx: Context, sender: str, msg: ResponseAction):
    """Response Agent took action"""
    logger.info("\n" + "="*70)
    logger.info("📨 [3/4] RESPONSE AGENT ACTION")
    logger.info("="*70)
    logger.info(f"Action: {msg.action_type}")
    logger.info(f"Target: {msg.target_systems}")
    logger.info(f"Reason: {msg.reason}")
    logger.info(f"Status: {msg.status}")
    
    metrics["response_actions"] += 1
    
    logger.info("\n🚑 Response Agent acted autonomously!")
    logger.info("   → This triggers Communication Agent")

@test_agent.on_message(model=StatusUpdate)
async def handle_status_update(ctx: Context, sender: str, msg: StatusUpdate):
    """Communication Agent sent update"""
    logger.info("\n" + "="*70)
    logger.info("📨 [4/4] COMMUNICATION AGENT UPDATE")
    logger.info("="*70)
    logger.info(f"Title: {msg.title}")
    logger.info(f"Status: {msg.status}")
    logger.info(f"Description: {msg.description}")
    logger.info(f"Affected: {msg.affected_services}")
    
    metrics["communication_updates"] += 1
    metrics["pipeline_complete"] = True
    
    logger.info("\n📢 Communication Agent notified stakeholders!")
    logger.info("   → Full pipeline complete!")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def check_mock_api():
    """Check if mock infrastructure is running"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{MOCK_API}/health", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                return resp.status == 200
    except:
        return False

def load_agent_addresses():
    """Load agent addresses from environment"""
    return {
        "canary": os.getenv("CANARY_AGENT_ADDRESS"),
        "monitoring": os.getenv("MONITORING_AGENT_ADDRESS"),
        "response": os.getenv("RESPONSE_AGENT_ADDRESS"),
        "communication": os.getenv("COMMUNICATION_AGENT_ADDRESS")
    }

async def get_systems():
    """Get systems from mock infrastructure"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{MOCK_API}/systems") as resp:
            data = await resp.json()
            return data['systems']

async def poison_systems(systems: List[str]):
    """Create failures in mock infrastructure"""
    async with aiohttp.ClientSession() as session:
        for system in systems:
            await session.post(f"{MOCK_API}/simulate-failure/{system}")

async def cleanup_systems(systems: List[str]):
    """Recover systems"""
    async with aiohttp.ClientSession() as session:
        for system in systems:
            await session.post(f"{MOCK_API}/rollback/{system}")

# ============================================================================
# FULL PIPELINE TEST SCENARIOS
# ============================================================================

async def run_full_pipeline(ctx: Context, agents: dict):
    """Run complete end-to-end pipeline test"""
    
    systems = await get_systems()
    
    # ========================================================================
    # SCENARIO 1: Bad Update (Full Pipeline)
    # ========================================================================
    
    logger.info("\n" + "🎬"*35)
    logger.info("SCENARIO 1: BAD UPDATE DETECTION & RESPONSE")
    logger.info("Tests: Canary → Response → Communication")
    logger.info("🎬"*35)
    
    metrics["scenarios_run"] += 1
    
    # Poison 20% of systems to simulate bad update
    poison_count = int(len(systems[:50]) * 0.2)
    poison_targets = systems[:poison_count]
    
    logger.info(f"\n💉 Pre-poisoning {poison_count} systems...")
    await poison_systems(poison_targets)
    logger.info("   ✅ Systems poisoned (simulating bad update effect)")
    
    # Send update to Canary Agent
    if agents["canary"]:
        logger.info(f"\n📤 Sending bad update to Canary Agent...")
        
        update = UpdatePackage(
            update_id="UPDATE-BAD-001",
            version="2.5.0-broken",
            description="Bad update that will fail canary test",
            target_systems=systems[:50],
            timestamp=time.time()
        )
        
        try:
            await ctx.send(agents["canary"], update)
            logger.info("✅ Sent to Canary Agent")
            logger.info("\n⏳ Expected flow:")
            logger.info("   1. Canary tests on 1% of systems")
            logger.info("   2. Detects high error rate")
            logger.info("   3. Sends ROLLBACK recommendation to Response")
            logger.info("   4. Response executes rollback")
            logger.info("   5. Communication notifies stakeholders")
        except Exception as e:
            logger.error(f"❌ Failed to send: {e}")
    else:
        logger.warning("⚠️  Canary agent not configured, skipping...")
    
    # Wait for pipeline to complete
    logger.info("\n⏳ Waiting 20 seconds for full pipeline...")
    for i in range(20):
        await asyncio.sleep(1)
        if metrics["pipeline_complete"]:
            logger.info("✅ Pipeline completed early!")
            break
    
    # Cleanup
    await cleanup_systems(poison_targets)
    
    await asyncio.sleep(3)
    
    # ========================================================================
    # SCENARIO 2: Real-time Monitoring Detection
    # ========================================================================
    
    logger.info("\n" + "🎬"*35)
    logger.info("SCENARIO 2: REAL-TIME ANOMALY DETECTION")
    logger.info("Tests: Monitoring → Response → Communication")
    logger.info("🎬"*35)
    
    metrics["scenarios_run"] += 1
    metrics["pipeline_complete"] = False
    
    target_system = "server-42"
    
    logger.info(f"\n💥 Creating CPU spike on {target_system}...")
    await poison_systems([target_system])
    
    logger.info("✅ Anomaly created in mock infrastructure")
    logger.info("\n⏳ Expected flow:")
    logger.info("   1. Monitoring Agent detects CPU spike (within 5s)")
    logger.info("   2. Sends AnomalyAlert to Response Agent")
    logger.info("   3. Response Agent analyzes with Groq AI")
    logger.info("   4. Response takes action (scale/rollback)")
    logger.info("   5. Communication notifies stakeholders")
    
    if agents["monitoring"]:
        logger.info("\n👁️  Monitoring Agent is running, should detect within 5-10s...")
    else:
        logger.warning("⚠️  Monitoring agent not configured")
        logger.info("   You can still see detection in logs if agent is running")
    
    # Wait for detection
    logger.info("\n⏳ Waiting 15 seconds for monitoring detection...")
    for i in range(15):
        await asyncio.sleep(1)
        if metrics["monitoring_alerts"] > 0:
            logger.info("✅ Monitoring alert received!")
            break
    
    # Cleanup
    await cleanup_systems([target_system])
    
    # ========================================================================
    # GENERATE FINAL REPORT
    # ========================================================================
    
    await asyncio.sleep(2)
    generate_final_report(agents)

# ============================================================================
# REPORTING
# ============================================================================

def generate_final_report(agents: dict):
    """Generate comprehensive test report"""
    
    logger.info("\n" + "="*70)
    logger.info("📊 FULL PIPELINE TEST REPORT")
    logger.info("="*70)
    
    # Agent status
    logger.info("\n🤖 Agent Status:")
    agent_statuses = {
        "Canary": metrics["canary_responses"] > 0,
        "Monitoring": metrics["monitoring_alerts"] > 0,
        "Response": metrics["response_actions"] > 0,
        "Communication": metrics["communication_updates"] > 0
    }
    
    for agent_name, active in agent_statuses.items():
        status = "✅ ACTIVE" if active else "❌ NO RESPONSE"
        logger.info(f"   {agent_name}: {status}")
    
    # Metrics
    logger.info("\n📈 Pipeline Metrics:")
    logger.info(f"   Scenarios Run: {metrics['scenarios_run']}")
    logger.info(f"   Canary Responses: {metrics['canary_responses']}")
    logger.info(f"   Monitoring Alerts: {metrics['monitoring_alerts']}")
    logger.info(f"   Response Actions: {metrics['response_actions']}")
    logger.info(f"   Communication Updates: {metrics['communication_updates']}")
    
    # Success assessment
    logger.info("\n🎯 Assessment:")
    
    active_count = sum(agent_statuses.values())
    
    if active_count == 4:
        logger.info("   ✅ EXCELLENT - All 4 agents working together!")
        logger.info("   Full autonomous disaster recovery pipeline operational")
    elif active_count >= 2:
        logger.info(f"   ⚠️  PARTIAL - {active_count}/4 agents responding")
        logger.info("   Some agents may not be running or configured")
    elif active_count == 1:
        logger.info("   ⚠️  MINIMAL - Only 1 agent responding")
        logger.info("   Start more agents for full pipeline demo")
    else:
        logger.info("   ❌ NO AGENTS RESPONDING")
        logger.info("   Check that agents are running and addresses are set")
    
    # Next steps
    logger.info("\n" + "="*70)
    logger.info("💡 NEXT STEPS")
    logger.info("="*70)
    
    if not agents["canary"]:
        logger.info("\n🐦 To test Canary Agent:")
        logger.info("   1. Start: python agents/canary/canary_agent.py")
        logger.info("   2. Copy address from logs")
        logger.info("   3. export CANARY_AGENT_ADDRESS='agent1q...'")
    
    if not agents["monitoring"]:
        logger.info("\n👁️  To test Monitoring Agent:")
        logger.info("   1. Start: python agents/monitoring/monitoring_agent.py")
        logger.info("   2. It auto-detects anomalies every 5s")
        logger.info("   3. Check logs/monitoring_agent.log")
    
    if not agents["response"]:
        logger.info("\n🚑 To test Response Agent:")
        logger.info("   1. Start: python agents/response/intelligent_response_agent.py")
        logger.info("   2. It receives alerts from Canary/Monitoring")
        logger.info("   3. Takes autonomous action")
    
    if not agents["communication"]:
        logger.info("\n📢 To test Communication Agent:")
        logger.info("   1. Start: python agents/communication/communication_agent.py")
        logger.info("   2. It receives actions from Response")
        logger.info("   3. Sends notifications")
    
    logger.info("\n📂 Check Logs:")
    logger.info("   tail -f logs/*.log")
    
    logger.info("\n" + "="*70)

async def show_setup_instructions():
    """Show how to set up agents"""
    
    logger.info("\n" + "="*70)
    logger.info("📚 SETUP INSTRUCTIONS")
    logger.info("="*70)
    
    logger.info("\nTo run full pipeline test, you need to:")
    
    logger.info("\n1️⃣ Start all 4 agents (separate terminals):")
    logger.info("   python agents/canary/canary_agent.py")
    logger.info("   python agents/monitoring/monitoring_agent.py")
    logger.info("   python agents/response/intelligent_response_agent.py")
    logger.info("   python agents/communication/communication_agent.py")
    
    logger.info("\n2️⃣ Copy agent addresses from startup logs:")
    logger.info("   Look for: 'Agent Address: agent1q...'")
    
    logger.info("\n3️⃣ Set environment variables:")
    logger.info("   export CANARY_AGENT_ADDRESS='agent1q...'")
    logger.info("   export MONITORING_AGENT_ADDRESS='agent1q...'")
    logger.info("   export RESPONSE_AGENT_ADDRESS='agent1q...'")
    logger.info("   export COMMUNICATION_AGENT_ADDRESS='agent1q...'")
    
    logger.info("\n4️⃣ Re-run this test:")
    logger.info("   python full_pipeline_test.py")
    
    logger.info("\n💡 TIP: You can test with just Canary first:")
    logger.info("   Just set CANARY_AGENT_ADDRESS and run")
    logger.info("   Then add other agents one by one")
    
    logger.info("\n" + "="*70)

if __name__ == "__main__":
    logger.info("\n🚀 Starting Full Pipeline Test...")
    logger.info("   Testing all 4 agents working together")
    test_agent.run()