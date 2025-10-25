"""
COMPLETE END-TO-END TEST PIPELINE
Tests all 4 agents working together with full disaster recovery scenarios

This simulates real-world incidents like AWS/CrowdStrike outages:
1. Bad updates caught by Canary before wide deployment
2. Real-time anomaly detection by Monitoring
3. Autonomous recovery by Response Agent
4. Stakeholder notifications by Communication Agent

Prerequisites:
1. Start mock infrastructure: python services/mock_infrastructure.py
2. Start agents (they auto-register): 
   - python agents/canary/canary_agent.py
   - python agents/monitoring/monitoring_agent.py
   - python agents/response/intelligent_response_agent.py
   - python agents/communication/communication_agent.py
3. Run this test: python e2e_test_pipeline.py
"""

import asyncio
import aiohttp
from uagents import Agent, Context, Model
from typing import List, Dict
from loguru import logger
import time
import os
from agents.registry import registry
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

MOCK_API = "http://localhost:8000"
TEST_DURATION = 60  # seconds per scenario
POLL_INTERVAL = 1  # check registry every N seconds

# ============================================================================
# MESSAGE MODELS
# ============================================================================

class UpdatePackage(Model):
    update_id: str
    version: str
    description: str
    target_systems: List[str]
    timestamp: float

class CanaryTestResult(Model):
    update_id: str
    success: bool
    affected_systems: int
    error_rate: float
    latency_impact: float
    recommendation: str
    details: str

class AnomalyAlert(Model):
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
    action_id: str
    action_type: str
    target_systems: List[str]
    reason: str
    status: str
    timestamp: float

class StatusUpdate(Model):
    incident_id: str
    status: str
    title: str
    description: str
    affected_services: List[str]
    timestamp: float

# ============================================================================
# TEST ORCHESTRATOR
# ============================================================================

class E2ETestOrchestrator:
    """Orchestrates complete end-to-end testing"""
    
    def __init__(self):
        self.agent = Agent(
            name="e2e_test_orchestrator",
            seed="e2e_test_seed_999",
            port=9999
        )
        
        self.metrics = {
            "tests_run": 0,
            "canary_caught_bad_updates": 0,
            "monitoring_detected_anomalies": 0,
            "autonomous_recoveries": 0,
            "notifications_sent": 0,
            "total_incidents_prevented": 0
        }
        
        self.message_log = []
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup message handlers to track agent responses"""
        
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info("\n" + "🚀"*35)
            logger.info("END-TO-END TEST PIPELINE STARTED")
            logger.info("🚀"*35)
            logger.info(f"\nOrchestrator Address: {self.agent.address}")
            
            await asyncio.sleep(2)
            await self.run_full_test_suite(ctx)
        
        @self.agent.on_message(model=CanaryTestResult)
        async def on_canary_result(ctx: Context, sender: str, msg: CanaryTestResult):
            self.log_message("Canary Agent", msg.__class__.__name__, msg.dict())
            if msg.recommendation == "ROLLBACK":
                self.metrics["canary_caught_bad_updates"] += 1
                self.metrics["total_incidents_prevented"] += 1
        
        @self.agent.on_message(model=AnomalyAlert)
        async def on_anomaly(ctx: Context, sender: str, msg: AnomalyAlert):
            self.log_message("Monitoring Agent", msg.__class__.__name__, msg.dict())
            self.metrics["monitoring_detected_anomalies"] += 1
        
        @self.agent.on_message(model=ResponseAction)
        async def on_response(ctx: Context, sender: str, msg: ResponseAction):
            self.log_message("Response Agent", msg.__class__.__name__, msg.dict())
            if msg.status == "COMPLETED":
                self.metrics["autonomous_recoveries"] += 1
        
        @self.agent.on_message(model=StatusUpdate)
        async def on_communication(ctx: Context, sender: str, msg: StatusUpdate):
            self.log_message("Communication Agent", msg.__class__.__name__, msg.dict())
            self.metrics["notifications_sent"] += 1
    
    def log_message(self, source: str, msg_type: str, data: dict):
        """Log intercepted messages"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "type": msg_type,
            "data": data
        }
        self.message_log.append(log_entry)
        logger.debug(f"📨 Intercepted: {source} -> {msg_type}")
    
    async def run_full_test_suite(self, ctx: Context):
        """Run complete test suite"""
        
        # Wait for agents to register
        logger.info("\n⏳ Waiting for agents to register...")
        await self.wait_for_agents()
        
        # Check mock infrastructure
        if not await self.check_mock_infrastructure():
            logger.error("❌ Mock infrastructure not available!")
            return
        
        # Run test scenarios
        await self.test_scenario_1_bad_update(ctx)
        await asyncio.sleep(5)
        
        await self.test_scenario_2_cpu_spike(ctx)
        await asyncio.sleep(5)
        
        await self.test_scenario_3_memory_leak(ctx)
        await asyncio.sleep(5)
        
        await self.test_scenario_4_cascading_failure(ctx)
        
        # Generate final report
        await asyncio.sleep(5)
        self.generate_final_report()
    
    async def wait_for_agents(self, timeout: int = 30):
        """Wait for all agents to register"""
        required_agents = ["canary_agent", "monitoring_agent", "response_agent", "communication_agent"]
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            registry.load_registry()  # Reload from file
            registered = registry.get_all_agents()
            
            found = [name for name in required_agents if name in registered]
            
            if len(found) == 4:
                logger.info(f"✅ All 4 agents registered!")
                registry.print_registry()
                return True
            
            logger.info(f"⏳ Found {len(found)}/4 agents: {', '.join(found)}")
            await asyncio.sleep(2)
        
        logger.warning(f"⚠️  Timeout: Only found {len(found)}/4 agents")
        return False
    
    async def check_mock_infrastructure(self) -> bool:
        """Verify mock infrastructure is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{MOCK_API}/health", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    if resp.status == 200:
                        logger.info("✅ Mock infrastructure is running")
                        return True
        except:
            logger.error("❌ Mock infrastructure not responding")
            logger.error("   Start it with: python services/mock_infrastructure.py")
        return False
    
    async def get_systems(self) -> List[str]:
        """Get systems from mock infrastructure"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{MOCK_API}/systems") as resp:
                data = await resp.json()
                return data['systems']
    
    async def poison_system(self, system_id: str):
        """Inject failure into system"""
        async with aiohttp.ClientSession() as session:
            await session.post(f"{MOCK_API}/simulate-failure/{system_id}")
    
    async def recover_system(self, system_id: str):
        """Recover poisoned system"""
        async with aiohttp.ClientSession() as session:
            await session.post(f"{MOCK_API}/rollback/{system_id}")
    
    # ========================================================================
    # TEST SCENARIOS (Like Real-World Outages)
    # ========================================================================
    
    async def test_scenario_1_bad_update(self, ctx: Context):
        """
        SCENARIO 1: Bad Software Update (CrowdStrike-style)
        
        Simulates a faulty update that would crash systems.
        Canary Agent should detect and prevent full deployment.
        """
        logger.info("\n" + "🎬"*35)
        logger.info("SCENARIO 1: BAD SOFTWARE UPDATE")
        logger.info("Simulating CrowdStrike-style faulty update")
        logger.info("🎬"*35)
        
        self.metrics["tests_run"] += 1
        
        systems = await self.get_systems()
        target_systems = systems[:50]  # First 50 systems
        
        # Pre-poison 20% to simulate bad update effect
        poison_count = int(len(target_systems) * 0.2)
        logger.info(f"\n💉 Pre-poisoning {poison_count} systems (simulating bad update)")
        
        for sys in target_systems[:poison_count]:
            await self.poison_system(sys)
        
        # Send to Canary Agent
        canary_addr = registry.get_agent_address("canary_agent")
        if canary_addr:
            logger.info(f"\n📤 Sending bad update to Canary Agent...")
            
            update = UpdatePackage(
                update_id="UPDATE-FAULTY-2025-001",
                version="2.5.0-broken",
                description="Faulty kernel update (will crash systems)",
                target_systems=target_systems,
                timestamp=time.time()
            )
            
            await ctx.send(canary_addr, update)
            logger.info("✅ Sent to Canary Agent")
            logger.info("\n⏳ Expected: Canary tests on 1%, detects failures, prevents deployment")
        else:
            logger.error("❌ Canary Agent not registered!")
        
        # Wait for pipeline
        logger.info("\n⏳ Waiting 30 seconds for Canary testing...")
        await asyncio.sleep(30)
        
        # Cleanup
        for sys in target_systems[:poison_count]:
            await self.recover_system(sys)
        
        logger.info("✅ Scenario 1 complete")
    
    async def test_scenario_2_cpu_spike(self, ctx: Context):
        """
        SCENARIO 2: CPU Spike Detection
        
        Simulates sudden CPU spike (like a runaway process).
        Monitoring should detect, Response should take action.
        """
        logger.info("\n" + "🎬"*35)
        logger.info("SCENARIO 2: CPU SPIKE DETECTION")
        logger.info("Simulating runaway process causing CPU spike")
        logger.info("🎬"*35)
        
        self.metrics["tests_run"] += 1
        
        target = "server-25"
        logger.info(f"\n💥 Creating CPU spike on {target}...")
        await self.poison_system(target)
        
        logger.info("✅ CPU spike injected")
        logger.info("\n⏳ Expected flow:")
        logger.info("   1. Monitoring detects CPU anomaly (~5-10s)")
        logger.info("   2. Sends alert to Response Agent")
        logger.info("   3. Response Agent analyzes with AI")
        logger.info("   4. Takes autonomous action (scale/restart)")
        logger.info("   5. Communication notifies stakeholders")
        
        await asyncio.sleep(20)
        
        await self.recover_system(target)
        logger.info("✅ Scenario 2 complete")
    
    async def test_scenario_3_memory_leak(self, ctx: Context):
        """
        SCENARIO 3: Memory Leak Detection
        
        Simulates gradual memory consumption.
        """
        logger.info("\n" + "🎬"*35)
        logger.info("SCENARIO 3: MEMORY LEAK DETECTION")
        logger.info("🎬"*35)
        
        self.metrics["tests_run"] += 1
        
        targets = ["server-10", "server-11", "server-12"]
        logger.info(f"\n🐛 Simulating memory leak on {len(targets)} systems...")
        
        for target in targets:
            await self.poison_system(target)
        
        logger.info("\n⏳ Monitoring should detect memory anomalies...")
        await asyncio.sleep(25)
        
        for target in targets:
            await self.recover_system(target)
        
        logger.info("✅ Scenario 3 complete")
    
    async def test_scenario_4_cascading_failure(self, ctx: Context):
        """
        SCENARIO 4: Cascading Failure (AWS-style)
        
        Simulates multiple systems failing in succession.
        """
        logger.info("\n" + "🎬"*35)
        logger.info("SCENARIO 4: CASCADING FAILURE")
        logger.info("Simulating AWS-style availability zone failure")
        logger.info("🎬"*35)
        
        self.metrics["tests_run"] += 1
        
        # Simulate cascading failure
        targets = [f"server-{i}" for i in range(30, 40)]
        
        logger.info(f"\n💥 Triggering cascading failure on {len(targets)} systems...")
        
        for i, target in enumerate(targets):
            await self.poison_system(target)
            logger.info(f"   ⚡ System {i+1}/{len(targets)} failed")
            await asyncio.sleep(2)  # Cascade over time
        
        logger.info("\n⏳ Multiple alerts should trigger autonomous response...")
        await asyncio.sleep(30)
        
        # Cleanup
        for target in targets:
            await self.recover_system(target)
        
        logger.info("✅ Scenario 4 complete")
    
    def generate_final_report(self):
        """Generate comprehensive test report"""
        
        logger.info("\n" + "="*70)
        logger.info("📊 END-TO-END TEST REPORT")
        logger.info("="*70)
        
        # Agent participation
        logger.info("\n🤖 Agent Participation:")
        agents = registry.get_all_agents()
        for name, info in agents.items():
            logger.info(f"   ✅ {name} - {info.address[:20]}...")
        
        # Test metrics
        logger.info("\n📈 Test Metrics:")
        logger.info(f"   Test Scenarios Run: {self.metrics['tests_run']}")
        logger.info(f"   Bad Updates Caught: {self.metrics['canary_caught_bad_updates']}")
        logger.info(f"   Anomalies Detected: {self.metrics['monitoring_detected_anomalies']}")
        logger.info(f"   Autonomous Recoveries: {self.metrics['autonomous_recoveries']}")
        logger.info(f"   Notifications Sent: {self.metrics['notifications_sent']}")
        logger.info(f"   Total Incidents Prevented: {self.metrics['total_incidents_prevented']}")
        
        # Message flow analysis
        logger.info(f"\n📨 Message Flow Analysis:")
        logger.info(f"   Total Messages Intercepted: {len(self.message_log)}")
        
        if self.message_log:
            logger.info("\n   Recent Messages:")
            for msg in self.message_log[-10:]:
                logger.info(f"   - [{msg['timestamp']}] {msg['source']} -> {msg['type']}")
        
        # Assessment
        logger.info("\n🎯 System Assessment:")
        
        score = 0
        if self.metrics['canary_caught_bad_updates'] > 0:
            score += 25
            logger.info("   ✅ Canary deployment protection: WORKING")
        
        if self.metrics['monitoring_detected_anomalies'] > 0:
            score += 25
            logger.info("   ✅ Real-time monitoring: WORKING")
        
        if self.metrics['autonomous_recoveries'] > 0:
            score += 25
            logger.info("   ✅ Autonomous recovery: WORKING")
        
        if self.metrics['notifications_sent'] > 0:
            score += 25
            logger.info("   ✅ Stakeholder communication: WORKING")
        
        logger.info(f"\n   Overall Score: {score}/100")
        
        if score == 100:
            logger.info("\n   🏆 EXCELLENT - Full autonomous disaster recovery operational!")
        elif score >= 75:
            logger.info("\n   ✅ GOOD - Core systems working, minor issues")
        elif score >= 50:
            logger.info("\n   ⚠️  PARTIAL - Some components need attention")
        else:
            logger.info("\n   ❌ NEEDS WORK - Multiple systems not responding")
        
        logger.info("\n" + "="*70)
        logger.info("💡 Next: Check logs/ for detailed agent activity")
        logger.info("="*70)

# ============================================================================
# MAIN
# ============================================================================

def main():
    orchestrator = E2ETestOrchestrator()
    orchestrator.agent.run()

if __name__ == "__main__":
    logger.info("🚀 Starting End-to-End Test Pipeline...")
    main()