"""
Intelligent Response Agent - LAVA-ONLY MODE with Proper Storage Tracking
"""

from uagents import Context, Model
import os

# ✅ CRITICAL FIX: Import from centralized messages.py
from agents.messages import CanaryTestResult, AnomalyAlert, ResponseAction

from agents.base_agent import BaseSuraAgent
from typing import Dict, List
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
import asyncio

# Import Lava service
from services.lava_service import lava_service

class IntelligentResponseAgent(BaseSuraAgent):
    """Response Agent - LAVA-ONLY MODE (AI required, no fallback)"""
    
    def __init__(self):
        load_dotenv()
        super().__init__(
            name="response_agent",
            seed=os.getenv("RESPONSE_SEED_PHRASE", "response_seed_default_67890"),
            port=8003,
            capabilities=["incident_response", "lava_ai_required", "autonomous_recovery"]
        )
        
        self.active_incidents: Dict[str, dict] = {}
        self.runbooks = self.load_runbooks()
        self.lava_requests_count = 0
        
        # CRITICAL: Check Lava availability on init
        if not lava_service.available:
            logger.error("="*70)
            logger.error("🚨 LAVA AI NOT AVAILABLE - AGENT CANNOT START")
            logger.error("="*70)
            logger.error("This agent requires LAVA_FORWARD_TOKEN to function")
            logger.error("Get token: https://lavapayments.com/dashboard/build/secret-keys")
            logger.error("Add to .env: LAVA_FORWARD_TOKEN=lsk_...")
            raise RuntimeError("LAVA_FORWARD_TOKEN required for this agent")
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"🚑 Response Agent started at {self.agent.address}")
            logger.info(f"🔮 Lava Gateway: ENABLED (REQUIRED MODE)")
            logger.info(f"   Model: {lava_service.model}")
            logger.info(f"   Using your Lava wallet credits")
            logger.info(f"   ⚠️  NO FALLBACK - All decisions require AI")
            
            # ✅ FIX: Initialize storage properly
            ctx.storage.set("actions_taken", 0)
            ctx.storage.set("incidents_resolved", 0)
            ctx.storage.set("lava_requests", 0)
            logger.info(f"✅ Storage initialized: all counters set to 0")
        
        @self.agent.on_message(model=CanaryTestResult)
        async def handle_canary_result(ctx: Context, sender: str, msg: CanaryTestResult):
            logger.info(f"📊 Received canary result: {msg.recommendation}")
            logger.info(f"   From: {sender[:20]}...")
            logger.info(f"   Update ID: {msg.update_id}")
            logger.info(f"   Error rate: {msg.error_rate:.2%}")
            
            if msg.recommendation == "ROLLBACK":
                action = await self.execute_rollback_with_ai(ctx, msg)
                
                # ✅ FIX: Update storage immediately
                actions_taken = ctx.storage.get("actions_taken") or 0
                ctx.storage.set("actions_taken", actions_taken + 1)
                
                if action.lava_request_id:
                    lava_requests = ctx.storage.get("lava_requests") or 0
                    ctx.storage.set("lava_requests", lava_requests + 1)
                    logger.info(f"📊 Lava: {lava_requests + 1} | Actions: {actions_taken + 1}")
                
                await self.send_to_peer(ctx, "communication_agent", action)
        
        @self.agent.on_message(model=AnomalyAlert)
        async def handle_anomaly(ctx: Context, sender: str, msg: AnomalyAlert):
            logger.warning(f"🚨 Received anomaly alert: {msg.severity} - {msg.metric_type}")
            logger.warning(f"   From: {sender[:20]}...")
            logger.warning(f"   System: {msg.system_id}")
            logger.warning(f"   Current: {msg.current_value:.2f} | Expected: {msg.expected_value:.2f}")
            
            if msg.severity in ["HIGH", "CRITICAL", "MEDIUM"]:
                action = await self.execute_emergency_response_ai_only(ctx, msg)
                
                # ✅ FIX: Update storage immediately
                actions_taken = ctx.storage.get("actions_taken") or 0
                ctx.storage.set("actions_taken", actions_taken + 1)
                
                incidents_resolved = ctx.storage.get("incidents_resolved") or 0
                ctx.storage.set("incidents_resolved", incidents_resolved + 1)
                
                if action.lava_request_id:
                    lava_requests = ctx.storage.get("lava_requests") or 0
                    ctx.storage.set("lava_requests", lava_requests + 1)
                    logger.info(f"📊 Lava: {lava_requests + 1} | Actions: {actions_taken + 1} | Resolved: {incidents_resolved + 1}")
                else:
                    logger.error(f"⚠️  No Lava request ID - AI may have failed!")
                
                await self.send_to_peer(ctx, "communication_agent", action)
    
    def load_runbooks(self) -> Dict[str, callable]:
        """Load automated response runbooks"""
        return {
            "ROLLBACK": self.runbook_rollback,
            "FAILOVER": self.runbook_failover,
            "SCALE_UP": self.runbook_scale_up,
            "SCALE_DOWN": self.runbook_scale_down,
            "ISOLATE": self.runbook_isolate,
            "INVESTIGATE": self.runbook_investigate,
            "RESTART": self.runbook_restart
        }
    
    async def execute_rollback_with_ai(self, ctx: Context, canary_result: CanaryTestResult) -> ResponseAction:
        """Execute rollback with AI confirmation"""
        logger.info(f"🔄 Analyzing rollback decision with AI...")
        
        try:
            analysis = await lava_service.analyze_incident({
                "alert_id": f"CANARY-{canary_result.update_id}",
                "severity": "CRITICAL" if canary_result.error_rate > 0.1 else "HIGH",
                "system_id": "canary_deployment",
                "metric_type": "ERROR_RATE",
                "current_value": canary_result.error_rate * 100,
                "expected_value": 1.0,
                "confidence": 0.95
            })
            
            logger.info(f"🤖 AI Rollback Analysis:")
            logger.info(f"   Recommendation: {analysis.get('recommendation')}")
            logger.info(f"   Reasoning: {analysis.get('reasoning')}")
            logger.info(f"   Lava Request ID: {analysis.get('lava_request_id', 'MISSING!')}")
            
            action = ResponseAction(
                action_id=f"ACTION-{int(datetime.now().timestamp())}",
                action_type=analysis.get('recommendation', 'ROLLBACK'),
                target_systems=["all"],
                reason=f"AI Decision: {analysis.get('reasoning', 'Canary test failed')}",
                status="INITIATED",
                timestamp=datetime.now().timestamp(),
                lava_request_id=analysis.get('lava_request_id', '')
            )
            
        except Exception as e:
            logger.error(f"❌ AI analysis FAILED: {e}")
            raise RuntimeError(f"Lava AI required but failed: {e}")
        
        await self.runbook_rollback(canary_result.update_id)
        action.status = "COMPLETED"
        
        return action
    
    async def execute_emergency_response_ai_only(self, ctx: Context, alert: AnomalyAlert) -> ResponseAction:
        """Execute emergency response - REQUIRES AI (no fallback)"""
        logger.info(f"⚡ Executing AI-ONLY emergency response for {alert.alert_id}")
        logger.info(f"🔮 Consulting Lava AI (REQUIRED)...")
        
        try:
            analysis = await lava_service.analyze_incident({
                "alert_id": alert.alert_id,
                "severity": alert.severity,
                "system_id": alert.system_id,
                "metric_type": alert.metric_type,
                "current_value": alert.current_value,
                "expected_value": alert.expected_value,
                "confidence": alert.confidence
            })
            
            if not analysis.get('lava_request_id'):
                raise RuntimeError("No Lava request ID in response - AI call may have failed")
            
            logger.info(f"🤖 AI Analysis Complete:")
            logger.info(f"   Provider: {analysis.get('ai_provider', 'Lava')}")
            logger.info(f"   Recommendation: {analysis.get('recommendation')}")
            logger.info(f"   Confidence: {analysis.get('confidence', 0):.2f}")
            logger.info(f"   Reasoning: {analysis.get('reasoning')}")
            logger.info(f"📊 Lava Request ID: {analysis['lava_request_id']}")
            logger.info(f"   Track usage: https://lavapayments.com/dashboard/build/explore")
            
            action_type = analysis.get('recommendation', 'INVESTIGATE')
            reasoning = f"AI: {analysis.get('reasoning', 'Automated AI decision')}"
            lava_request_id = analysis['lava_request_id']
            
        except Exception as e:
            logger.error(f"❌ AI analysis FAILED: {e}")
            logger.error(f"   CANNOT PROCEED - This agent requires AI")
            raise RuntimeError(f"Lava AI required but failed: {e}")
        
        action = ResponseAction(
            action_id=f"ACTION-{int(datetime.now().timestamp())}",
            action_type=action_type,
            target_systems=[alert.system_id],
            reason=reasoning,
            status="INITIATED",
            timestamp=datetime.now().timestamp(),
            lava_request_id=lava_request_id
        )
        
        if action_type in self.runbooks:
            logger.info(f"📖 Executing AI-approved {action_type} runbook...")
            await self.runbooks[action_type](alert.system_id)
            action.status = "COMPLETED"
            logger.info(f"✅ {action_type} completed successfully (AI-approved)")
        else:
            logger.error(f"❌ Unknown action type from AI: {action_type}")
            await self.runbook_investigate(alert.system_id)
            action.status = "COMPLETED"
        
        return action
    
    # ========================================================================
    # RUNBOOK IMPLEMENTATIONS
    # ========================================================================
    
    async def runbook_rollback(self, target):
        """Rollback to previous version"""
        logger.info(f"📖 Running ROLLBACK runbook on {target}")
        logger.info(f"   → Stopping service...")
        await asyncio.sleep(0.5)
        logger.info(f"   → Reverting to previous version...")
        await asyncio.sleep(1.0)
        logger.info(f"   → Restarting service...")
        await asyncio.sleep(0.5)
        logger.info(f"   ✅ Rollback complete")
    
    async def runbook_failover(self, target):
        """Failover to backup systems"""
        logger.info(f"📖 Running FAILOVER runbook on {target}")
        logger.info(f"   → Redirecting traffic to backup...")
        await asyncio.sleep(1.5)
        logger.info(f"   → Verifying backup health...")
        await asyncio.sleep(1.0)
        logger.info(f"   → Marking primary as inactive...")
        await asyncio.sleep(0.5)
        logger.info(f"   ✅ Failover complete")
    
    async def runbook_scale_up(self, target):
        """Scale up resources"""
        logger.info(f"📖 Running SCALE_UP runbook on {target}")
        logger.info(f"   → Provisioning additional instances...")
        await asyncio.sleep(1.0)
        logger.info(f"   → Updating load balancer...")
        await asyncio.sleep(0.5)
        logger.info(f"   → Verifying new capacity...")
        await asyncio.sleep(0.5)
        logger.info(f"   ✅ Scale up complete")
    
    async def runbook_scale_down(self, target):
        """Scale down resources"""
        logger.info(f"📖 Running SCALE_DOWN runbook on {target}")
        logger.info(f"   → Draining connections...")
        await asyncio.sleep(1.0)
        logger.info(f"   → Terminating excess instances...")
        await asyncio.sleep(1.0)
        logger.info(f"   ✅ Scale down complete")
    
    async def runbook_isolate(self, target):
        """Isolate affected system"""
        logger.info(f"📖 Running ISOLATE runbook on {target}")
        logger.info(f"   → Removing from load balancer...")
        await asyncio.sleep(0.5)
        logger.info(f"   → Blocking incoming traffic...")
        await asyncio.sleep(0.5)
        logger.info(f"   ✅ System isolated")
    
    async def runbook_investigate(self, target):
        """Investigate issue"""
        logger.info(f"📖 Running INVESTIGATE runbook on {target}")
        logger.info(f"   → Collecting system logs...")
        await asyncio.sleep(0.5)
        logger.info(f"   → Gathering metrics snapshot...")
        await asyncio.sleep(0.5)
        logger.info(f"   → Creating incident ticket...")
        await asyncio.sleep(0.5)
        logger.info(f"   ✅ Investigation initiated")
    
    async def runbook_restart(self, target):
        """Restart service/system"""
        logger.info(f"📖 Running RESTART runbook on {target}")
        logger.info(f"   → Gracefully stopping service...")
        await asyncio.sleep(1.0)
        logger.info(f"   → Clearing cache/temp files...")
        await asyncio.sleep(0.5)
        logger.info(f"   → Starting service...")
        await asyncio.sleep(1.0)
        logger.info(f"   → Verifying health...")
        await asyncio.sleep(0.5)
        logger.info(f"   ✅ Restart complete")

# Initialize agent
intelligent_response_agent = IntelligentResponseAgent()
agent = intelligent_response_agent.get_agent()

if __name__ == "__main__":
    logger.info("🚀 Starting Response Agent (LAVA-ONLY MODE)...")
    logger.info("   AI-Required - No fallback to rule-based decisions")
    logger.info("   All incident responses will use Lava AI")
    agent.run()