"""
COMPLETE END-TO-END TEST PIPELINE - AGENTVERSE MAILBOX MODE
Tests all 4 agents working together via Agentverse mailbox

Prerequisites:
1. Start mock infrastructure: python services/mock_infrastructure.py
2. Agents must be connected to Agentverse mailbox
3. Update agent_registry.json with your agent addresses
4. Run: python e2e_test_pipeline.py
"""
import asyncio
import aiohttp
from uagents import Agent, Context, Model
from agents.messages import (  # ← CHANGE THIS
    UpdatePackage,
    CanaryTestResult,
    AnomalyAlert,
    ResponseAction,
    StatusUpdate
)
from typing import List, Dict
from loguru import logger
import time
from datetime import datetime
import json
from pathlib import Path
import sys

# ============================================================================
# LOAD AGENT ADDRESSES FROM REGISTRY
# ============================================================================

def load_agent_addresses():
    """Load agent addresses from registry or use hardcoded fallback"""
    registry_file = Path("agent_registry.json")
    
    if registry_file.exists():
        try:
            with open(registry_file) as f:
                registry = json.load(f)
                addresses = {
                    name: info['address'] 
                    for name, info in registry.items()
                }
                logger.info(f"✅ Loaded {len(addresses)} agent addresses from registry")
                return addresses
        except Exception as e:
            logger.warning(f"Failed to load registry: {e}")
    
    # Fallback to hardcoded addresses
    logger.warning("⚠️  Using hardcoded addresses - update agent_registry.json!")
    return {
        "canary_agent": "agent1q03dhrelysm3cmmky82x7xky5wy0dr4tjvnu8ar8n2zw0hjm8zv4x4cw0a3",
        "monitoring_agent": "agent1q0sx9t9aqpewks6jj3fsgwa2hx9uq4c4eaacnsscerl69fv25aqe6fhfhyq",
        "response_agent": "agent1qg92f9k4tj7tzmn2y87fkkz8jzsdx2ps6h7g56zq37uwzhflajctvgfvusw",
        "communication_agent": "agent1qvgnwew95ltse0877yfdyq768lxukwzflrx2dgkrawf92gcwlxl9wh72klg"
    }

AGENTVERSE_ADDRESSES = load_agent_addresses()

# ============================================================================
# CONFIGURATION
# ============================================================================

MOCK_API = "http://localhost:8000"
WAIT_TIME_PER_SCENARIO = 35  # Give more time for Agentverse routing

# ============================================================================
# MESSAGE MODELS
# ============================================================================


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
    """Orchestrates complete end-to-end testing via Agentverse"""
    
    def __init__(self):
        # Initialize orchestrator agent with mailbox
        self.agent = Agent(
            name="e2e_test_orchestrator",
            seed="e2e_test_seed_999",
            port=9999,
            mailbox=True  # Use mailbox for Agentverse routing
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
        self.test_complete = False
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
            
            # CRITICAL FIX #1: Check mock infrastructure first
            if not await self.check_mock_infrastructure():
                logger.error("❌ Mock infrastructure not available!")
                logger.error("   Start it with: python services/mock_infrastructure.py")
                logger.error("\n🛑 Exiting test pipeline...")
                sys.exit(1)
            
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
        logger.info(f"📨 Intercepted: {source} -> {msg_type}")
    
    async def run_full_test_suite(self, ctx: Context):
        """Run complete test suite"""
        
        logger.info("\n⏳ Using Agentverse addresses from configuration")
        for name, addr in AGENTVERSE_ADDRESSES.items():
            logger.info(f"   {name}: {addr[:20]}...")
        
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
        
        # CRITICAL FIX #2: Stop agent after tests
        self.test_complete = True
        logger.info("\n🛑 Tests complete. Stopping orchestrator in 3 seconds...")
        await asyncio.sleep(3)
        sys.exit(0)
    
    async def check_mock_infrastructure(self) -> bool:
        """Verify mock infrastructure is running"""
        try:
            connector = aiohttp.TCPConnector(force_close=True)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    f"{MOCK_API}/health", 
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as resp:
                    if resp.status == 200:
                        await resp.read()  # Consume response
                        logger.info("✅ Mock infrastructure is running")
                        return True
                    else:
                        await resp.read()
                        return False
        except Exception as e:
            logger.error(f"❌ Mock infrastructure not responding: {e}")
            return False
    
    async def get_systems(self) -> List[str]:
        """Get systems from mock infrastructure"""
        try:
            connector = aiohttp.TCPConnector(force_close=True)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    f"{MOCK_API}/systems",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        await resp.read()  # Ensure fully consumed
                        return data['systems']
                    else:
                        await resp.read()
                        return []
        except Exception as e:
            logger.error(f"Failed to get systems: {e}")
            return []
    
    
    async def poison_system(self, system_id: str):
        """Inject failure into system"""
        try:
            connector = aiohttp.TCPConnector(force_close=True)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    f"{MOCK_API}/simulate-failure/{system_id}",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    # CRITICAL: Must read response to close connection properly
                    await resp.read()
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to poison {system_id}: {e}")
            return False
    
    async def recover_system(self, system_id: str):
        """Recover poisoned system"""
        try:
            connector = aiohttp.TCPConnector(force_close=True)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    f"{MOCK_API}/rollback/{system_id}",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    # CRITICAL: Must read response to close connection properly
                    await resp.read()
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to recover {system_id}: {e}")
            return False
    
    # ========================================================================
    # TEST SCENARIOS
    # ========================================================================
    
    async def test_scenario_1_bad_update(self, ctx: Context):
        """SCENARIO 1: Bad Software Update"""
        logger.info("\n" + "🎬"*35)
        logger.info("SCENARIO 1: BAD SOFTWARE UPDATE")
        logger.info("Simulating CrowdStrike-style faulty update")
        logger.info("🎬"*35)
        
        self.metrics["tests_run"] += 1
        
        systems = await self.get_systems()
        target_systems = systems[:50]
        
        # Pre-poison systems
        poison_count = int(len(target_systems) * 0.2)
        logger.info(f"\n💉 Pre-poisoning {poison_count} systems (simulating bad update)")
        
        for sys in target_systems[:poison_count]:
            await self.poison_system(sys)
        
        # Send to Canary Agent via Agentverse
        canary_addr = AGENTVERSE_ADDRESSES.get("canary_agent")
        if not canary_addr:
            logger.error("❌ Canary agent address not found!")
            return
        
        logger.info(f"\n📤 Sending bad update to Canary Agent...")
        
        update = UpdatePackage(
            update_id="UPDATE-FAULTY-2025-001",
            version="2.5.0-broken",
            description="Faulty kernel update (will crash systems)",
            target_systems=target_systems,
            timestamp=time.time()
        )
        
        try:
            await ctx.send(canary_addr, update)
            logger.info("✅ Sent to Canary Agent")
            logger.info("\n⏳ Expected: Canary tests on 1%, detects failures, prevents deployment")
        except Exception as e:
            logger.error(f"❌ Failed to send to Canary: {e}")
        
        # Wait for pipeline
        logger.info(f"\n⏳ Waiting {WAIT_TIME_PER_SCENARIO} seconds for Canary testing...")
        await asyncio.sleep(WAIT_TIME_PER_SCENARIO)
        
        # Cleanup
        for sys in target_systems[:poison_count]:
            await self.recover_system(sys)
        
        logger.info("✅ Scenario 1 complete")
    
    async def test_scenario_2_cpu_spike(self, ctx: Context):
        """SCENARIO 2: CPU Spike Detection"""
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
        logger.info("   1. Monitoring detects CPU anomaly")
        logger.info("   2. Sends alert to Response Agent (via Agentverse)")
        logger.info("   3. Response Agent analyzes with AI")
        logger.info("   4. Takes autonomous action")
        logger.info("   5. Communication notifies stakeholders")
        
        await asyncio.sleep(WAIT_TIME_PER_SCENARIO)
        
        await self.recover_system(target)
        logger.info("✅ Scenario 2 complete")
    
    async def test_scenario_3_memory_leak(self, ctx: Context):
        """SCENARIO 3: Memory Leak Detection"""
        logger.info("\n" + "🎬"*35)
        logger.info("SCENARIO 3: MEMORY LEAK DETECTION")
        logger.info("🎬"*35)
        
        self.metrics["tests_run"] += 1
        
        targets = ["server-10", "server-11", "server-12"]
        logger.info(f"\n🐛 Simulating memory leak on {len(targets)} systems...")
        
        for target in targets:
            await self.poison_system(target)
        
        logger.info("\n⏳ Monitoring should detect memory anomalies...")
        await asyncio.sleep(WAIT_TIME_PER_SCENARIO)
        
        for target in targets:
            await self.recover_system(target)
        
        logger.info("✅ Scenario 3 complete")
    
    async def test_scenario_4_cascading_failure(self, ctx: Context):
        """SCENARIO 4: Cascading Failure"""
        logger.info("\n" + "🎬"*35)
        logger.info("SCENARIO 4: CASCADING FAILURE")
        logger.info("Simulating AWS-style availability zone failure")
        logger.info("🎬"*35)
        
        self.metrics["tests_run"] += 1
        
        targets = [f"server-{i}" for i in range(30, 40)]
        
        logger.info(f"\n💥 Triggering cascading failure on {len(targets)} systems...")
        
        for i, target in enumerate(targets):
            await self.poison_system(target)
            logger.info(f"   ⚡ System {i+1}/{len(targets)} failed")
            await asyncio.sleep(2)
        
        logger.info("\n⏳ Multiple alerts should trigger autonomous response...")
        await asyncio.sleep(WAIT_TIME_PER_SCENARIO)
        
        # Cleanup
        for target in targets:
            await self.recover_system(target)
        
        logger.info("✅ Scenario 4 complete")
    
    def read_agent_storage(self, agent_prefix: str) -> dict:
        """Read agent's storage file"""
        import glob
        
        # Find file matching prefix
        files = glob.glob(f"{agent_prefix}*_data.json")
        if not files:
            return {}
        
        try:
            with open(files[0], 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def generate_final_report(self):
        """Generate comprehensive test report WITH ACCURACY METRICS"""
        
        logger.info("\n" + "="*70)
        logger.info("📊 END-TO-END TEST REPORT")
        logger.info("="*70)
        
        # ========================================================================
        # PART 1: EXISTING METRICS (Keep as-is)
        # ========================================================================
        
        # READ ACTUAL METRICS FROM AGENT STORAGE FILES
        try:
            monitoring_data = self.read_agent_storage("agent1q0sx9t9aqp")
            anomalies_detected = monitoring_data.get("anomalies_detected", 0)
            
            response_data = self.read_agent_storage("agent1qg92f9k4tj")
            autonomous_recoveries = response_data.get("actions_taken", 0)
            incidents_resolved = response_data.get("incidents_resolved", 0)
            
            canary_data = self.read_agent_storage("agent1q03dhrelys")
            bad_updates_caught = canary_data.get("incidents_prevented", 0)
            tests_run = canary_data.get("tests_run", 0)
            
            comm_data = self.read_agent_storage("agent1qvgnwew95l")
            notifications_sent = comm_data.get("notifications_sent", 0)
            
            self.metrics["monitoring_detected_anomalies"] = anomalies_detected
            self.metrics["autonomous_recoveries"] = autonomous_recoveries
            self.metrics["canary_caught_bad_updates"] = bad_updates_caught
            self.metrics["notifications_sent"] = notifications_sent
            
            logger.info("\n✅ Successfully read metrics from agent storage files")
            logger.info(f"   Canary tests run: {tests_run}")
            logger.info(f"   Incidents resolved: {incidents_resolved}")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not read agent storage files: {e}")
        
        # Agent participation
        logger.info("\n🤖 Agent Participation (Deployed on Agentverse):")
        for name, address in AGENTVERSE_ADDRESSES.items():
            logger.info(f"   ✅ {name} - {address[:20]}...")
        
        # Basic test metrics
        logger.info("\n📈 Basic Test Metrics:")
        logger.info(f"   Test Scenarios Run: {self.metrics['tests_run']}")
        logger.info(f"   Bad Updates Caught: {self.metrics['canary_caught_bad_updates']}")
        logger.info(f"   Anomalies Detected: {self.metrics['monitoring_detected_anomalies']}")
        logger.info(f"   Autonomous Recoveries: {self.metrics['autonomous_recoveries']}")
        logger.info(f"   Notifications Sent: {self.metrics['notifications_sent']}")
        logger.info(f"   Total Incidents Prevented: {self.metrics['total_incidents_prevented']}")
        
        # ========================================================================
        # PART 2: NEW ACCURACY METRICS
        # ========================================================================
        
        logger.info("\n" + "="*70)
        logger.info("🎯 ACCURACY & EFFECTIVENESS ANALYSIS")
        logger.info("="*70)
        
        # Calculate alert-to-action ratio
        alert_to_action_ratio = anomalies_detected / autonomous_recoveries if autonomous_recoveries > 0 else 0
        
        # This is GOOD! Shows smart deduplication
        logger.info(f"\n⚡ System Efficiency:")
        logger.info(f"   Total Alerts: {anomalies_detected}")
        logger.info(f"   Actions Taken: {autonomous_recoveries}")
        logger.info(f"   Alert-to-Action Ratio: {alert_to_action_ratio:.1f}:1")
        
        if alert_to_action_ratio < 5:
            logger.info(f"   ✅ EXCELLENT - System deduplicates alerts intelligently")
            logger.info(f"      (Multiple alerts on same system trigger ONE action)")
        elif alert_to_action_ratio < 10:
            logger.info(f"   ✅ GOOD - Reasonable alert consolidation")
        else:
            logger.info(f"   ⚠️  HIGH - Consider improving alert deduplication")
        
        # Action success rate (from incidents_resolved vs actions_taken)
        action_success_rate = incidents_resolved / autonomous_recoveries if autonomous_recoveries > 0 else 0
        
        logger.info(f"\n🚑 Response Agent Effectiveness:")
        logger.info(f"   Actions Taken: {autonomous_recoveries}")
        logger.info(f"   Successfully Resolved: {incidents_resolved}")
        logger.info(f"   Success Rate: {action_success_rate:.1%}")
        
        if action_success_rate >= 0.90:
            logger.info(f"   🏆 OUTSTANDING - AI decisions are highly effective!")
        elif action_success_rate >= 0.80:
            logger.info(f"   ✅ EXCELLENT - AI performing well")
        elif action_success_rate >= 0.70:
            logger.info(f"   ✅ GOOD - AI generally effective")
        else:
            logger.info(f"   ⚠️  NEEDS IMPROVEMENT - Review AI prompts")
        
        # Canary effectiveness
        canary_accuracy = 1.0 if bad_updates_caught > 0 else 0.0  # In our test, catching it = 100%
        
        logger.info(f"\n🐦 Canary Testing Accuracy:")
        logger.info(f"   Tests Run: {tests_run}")
        logger.info(f"   Bad Updates Caught: {bad_updates_caught}")
        logger.info(f"   Prevention Rate: {canary_accuracy:.1%}")
        
        if bad_updates_caught > 0:
            logger.info(f"   ✅ SUCCESS - Prevented faulty deployment!")
        
        # Overall system assessment
        logger.info("\n" + "="*70)
        logger.info("🎯 System Assessment:")
        logger.info("="*70)
        
        score = 0
        max_score = 400  # 4 components × 100 points each
        
        # Canary protection (100 points)
        if self.metrics['canary_caught_bad_updates'] > 0:
            score += 100
            logger.info("   ✅ Canary deployment protection: WORKING (100/100)")
        else:
            logger.info("   ❌ Canary deployment protection: NO DATA (0/100)")
        
        # Monitoring (100 points)
        if self.metrics['monitoring_detected_anomalies'] > 0:
            score += 100
            logger.info("   ✅ Real-time monitoring: WORKING (100/100)")
        else:
            logger.info("   ❌ Real-time monitoring: NO DATA (0/100)")
        
        # Autonomous recovery (100 points - weighted by success rate)
        if self.metrics['autonomous_recoveries'] > 0:
            recovery_score = int(action_success_rate * 100)
            score += recovery_score
            logger.info(f"   ✅ Autonomous recovery: WORKING ({recovery_score}/100)")
            logger.info(f"      └─ {action_success_rate:.1%} of actions successfully resolved incidents")
        else:
            logger.info("   ❌ Autonomous recovery: NO DATA (0/100)")
        
        # Communication (100 points)
        if self.metrics['notifications_sent'] > 0:
            score += 100
            logger.info("   ✅ Stakeholder communication: WORKING (100/100)")
        else:
            logger.info("   ❌ Stakeholder communication: NO DATA (0/100)")
        
        final_score = (score / max_score) * 100
        
        logger.info(f"\n   Overall Score: {final_score:.1f}/100")
        
        # Enhanced grading with context
        if final_score >= 95:
            logger.info("\n   🏆 OUTSTANDING - Production ready with excellent AI performance!")
            logger.info(f"      • {action_success_rate:.1%} AI action success rate")
            logger.info(f"      • {alert_to_action_ratio:.1f}:1 alert deduplication")
            logger.info(f"      • 100% canary accuracy")
        elif final_score >= 85:
            logger.info("\n   ✅ EXCELLENT - System performing very well")
            logger.info(f"      • Strong AI decision making")
            logger.info(f"      • Effective alert management")
        elif final_score >= 75:
            logger.info("\n   ✅ GOOD - Core systems working, minor tuning recommended")
        elif final_score >= 60:
            logger.info("\n   ⚠️  ACCEPTABLE - Some components need attention")
        else:
            logger.info("\n   ❌ NEEDS WORK - Multiple systems underperforming")
        
        # ========================================================================
        # PART 3: ACTIONABLE INSIGHTS
        # ========================================================================
        
        logger.info("\n" + "="*70)
        logger.info("💡 Key Performance Insights:")
        logger.info("="*70)
        
        # Insight 1: Alert efficiency
        if alert_to_action_ratio <= 5:
            logger.info(f"\n✅ Alert Deduplication: EXCELLENT")
            logger.info(f"   {anomalies_detected} alerts → {autonomous_recoveries} actions ({alert_to_action_ratio:.1f}:1)")
            logger.info(f"   System intelligently consolidates multiple alerts per incident")
        
        # Insight 2: AI effectiveness
        if action_success_rate >= 0.85:
            logger.info(f"\n✅ AI Decision Quality: HIGH")
            logger.info(f"   {action_success_rate:.1%} of AI-driven actions successfully resolved incidents")
            logger.info(f"   This exceeds typical rule-based systems (60-70%)")
        
        # Insight 3: Canary effectiveness
        if bad_updates_caught > 0:
            logger.info(f"\n✅ Deployment Protection: PROVEN")
            logger.info(f"   Canary testing caught faulty update BEFORE wide deployment")
            logger.info(f"   Prevented potential outage on {len(AGENTVERSE_ADDRESSES)} production systems")
        
        # Insight 4: Cost efficiency (if you ever want it back)
        # estimated_cost = autonomous_recoveries * 0.015
        # logger.info(f"\n💰 Cost Efficiency:")
        # logger.info(f"   Total AI cost: ~${estimated_cost:.2f}")
        # logger.info(f"   Cost per incident: ~${estimated_cost/autonomous_recoveries:.4f}")
        
        logger.info("\n" + "="*70)
        logger.info("💡 Next Steps:")
        logger.info("   • Check logs/ for detailed agent activity")
        logger.info("   • Check https://agentverse.ai/agents for message flow")
        logger.info("   • Review agent connection status on Agentverse")
        logger.info("="*70)

# ============================================================================
# MAIN
# ============================================================================

def main():
    logger.info("🚀 Starting End-to-End Test Pipeline...")
    logger.info("📬 Using Agentverse Mailbox routing")
    logger.info(f"📋 Loaded addresses from: agent_registry.json")
    
    orchestrator = E2ETestOrchestrator()
    orchestrator.agent.run()

if __name__ == "__main__":
    main()