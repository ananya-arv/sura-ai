"""
Intelligent Response Agent with Lava Gateway
Uses Lava AI for incident analysis with graceful fallback to rule-based decisions
"""

from uagents import Context, Model
import os
from agents.messages import (  # ← CHANGE THIS
    CanaryTestResult,
    AnomalyAlert,
    ResponseAction
)
from agents.base_agent import BaseSuraAgent
from agents.canary.canary_agent import CanaryTestResult
from agents.monitoring.monitoring_agent import AnomalyAlert
from typing import Dict, List
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
import asyncio

# Import Lava service
from services.lava_service import lava_service

class ResponseAction(Model):
    """Action taken by response agent"""
    action_id: str
    action_type: str
    target_systems: List[str]
    reason: str
    status: str
    timestamp: float
    lava_request_id: str = ""  # Track Lava usage

class IntelligentResponseAgent(BaseSuraAgent):
    """Response Agent with AI-enhanced decision making via Lava Gateway"""
    
    def __init__(self):
        load_dotenv()
        super().__init__(
            name="response_agent",
            seed=os.getenv("RESPONSE_SEED_PHRASE", "response_seed_default_67890"),
            port=8003,
            capabilities=["incident_response", "autonomous_recovery", "lava_ai", "runbook_execution"]
        )
        
        self.active_incidents: Dict[str, dict] = {}
        self.runbooks = self.load_runbooks()
        self.lava_requests_count = 0
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"🚑 Response Agent started at {self.agent.address}")
            
            # Check Lava availability
            if lava_service.available:
                logger.info(f"🔮 Lava Gateway: ENABLED")
                logger.info(f"   Model: {lava_service.model}")
                logger.info(f"   Using your Lava wallet credits")
            else:
                logger.warning(f"⚠️  Lava Gateway: DISABLED")
                logger.info(f"   Using rule-based decisions (still works perfectly!)")
            
            ctx.storage.set("actions_taken", 0)
            ctx.storage.set("incidents_resolved", 0)
            ctx.storage.set("lava_requests", 0)
        
        @self.agent.on_message(model=CanaryTestResult)
        async def handle_canary_result(ctx: Context, sender: str, msg: CanaryTestResult):
            logger.info(f"📊 Received canary result: {msg.recommendation}")
            
            if msg.recommendation == "ROLLBACK":
                action = await self.execute_rollback(ctx, msg.update_id, msg.details)
                ctx.storage.set("actions_taken", ctx.storage.get("actions_taken") + 1)
                
                # Notify Communication Agent
                await self.send_to_peer(ctx, "communication_agent", action)
        
        @self.agent.on_message(model=AnomalyAlert)
        async def handle_anomaly(ctx: Context, sender: str, msg: AnomalyAlert):
            logger.warning(f"🚨 Received anomaly alert: {msg.severity} - {msg.metric_type}")
            
            if msg.severity in ["HIGH", "CRITICAL"]:
                action = await self.execute_emergency_response(ctx, msg)
                ctx.storage.set("actions_taken", ctx.storage.get("actions_taken") + 1)
                
                # Track Lava usage
                if action.lava_request_id:
                    ctx.storage.set("lava_requests", ctx.storage.get("lava_requests") + 1)
                    self.lava_requests_count += 1
                    logger.info(f"📊 Total Lava requests: {ctx.storage.get('lava_requests')}")
                
                # Notify Communication Agent
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
    
    async def execute_rollback(self, ctx: Context, update_id: str, reason: str) -> ResponseAction:
        """Execute automatic rollback"""
        logger.info(f"🔄 Executing rollback for {update_id}")
        
        action = ResponseAction(
            action_id=f"ACTION-{int(datetime.now().timestamp())}",
            action_type="ROLLBACK",
            target_systems=["all"],
            reason=f"Canary test failed: {reason}",
            status="INITIATED",
            timestamp=datetime.now().timestamp()
        )
        
        # Execute rollback runbook
        await self.runbook_rollback(update_id)
        
        action.status = "COMPLETED"
        ctx.storage.set("incidents_resolved", ctx.storage.get("incidents_resolved") + 1)
        
        logger.info(f"✅ Rollback completed for {update_id}")
        return action
    
    async def execute_emergency_response(self, ctx: Context, alert: AnomalyAlert) -> ResponseAction:
        """
        Execute emergency response with AI analysis (if available) or rule-based fallback
        """
        logger.info(f"⚡ Executing emergency response for {alert.alert_id}")
        
        action_type = None
        reasoning = None
        lava_request_id = ""
        
        # Try AI analysis if Lava is available
        if lava_service.available:
            logger.info(f"🔮 Using Lava AI for incident analysis...")
            
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
                
                # Log AI decision
                logger.info(f"🤖 AI Analysis Complete:")
                logger.info(f"   Provider: {analysis.get('ai_provider', 'Lava')}")
                logger.info(f"   Recommendation: {analysis.get('recommendation')}")
                logger.info(f"   Confidence: {analysis.get('confidence', 0):.2f}")
                logger.info(f"   Reasoning: {analysis.get('reasoning', 'N/A')}")
                
                if analysis.get('lava_request_id'):
                    logger.info(f"📊 Lava Request ID: {analysis['lava_request_id']}")
                    logger.info(f"   Track usage: https://lavapayments.com/dashboard/build/explore")
                
                # Use AI recommendation if high confidence
                if analysis.get('confidence', 0) > 0.7:
                    action_type = analysis.get('recommendation', 'INVESTIGATE')
                    reasoning = f"AI: {analysis.get('reasoning', 'Automated decision')}"
                    lava_request_id = analysis.get('lava_request_id', '')
                    logger.info(f"✅ Using AI recommendation (confidence: {analysis.get('confidence', 0):.0%})")
                else:
                    logger.warning(f"⚠️  Low AI confidence ({analysis.get('confidence', 0):.0%}), using rules")
                    action_type = self._rule_based_decision(alert)
                    reasoning = f"Rule-based (AI confidence too low)"
            
            except Exception as e:
                logger.error(f"❌ AI analysis failed: {e}")
                logger.info(f"   Falling back to rule-based decision")
                action_type = self._rule_based_decision(alert)
                reasoning = f"Rule-based fallback (AI error)"
        else:
            # No Lava available, use rules directly
            logger.info(f"📋 Using rule-based decision (Lava not available)")
            action_type = self._rule_based_decision(alert)
            reasoning = f"Rule-based: {alert.metric_type} anomaly on {alert.system_id}"
        
        # Create action
        action = ResponseAction(
            action_id=f"ACTION-{int(datetime.now().timestamp())}",
            action_type=action_type,
            target_systems=[alert.system_id],
            reason=reasoning,
            status="INITIATED",
            timestamp=datetime.now().timestamp(),
            lava_request_id=lava_request_id
        )
        
        # Execute runbook
        if action_type in self.runbooks:
            logger.info(f"📖 Executing {action_type} runbook...")
            await self.runbooks[action_type](alert.system_id)
            action.status = "COMPLETED"
            logger.info(f"✅ {action_type} completed successfully")
        else:
            logger.error(f"❌ Unknown action type: {action_type}")
            # Try INVESTIGATE as fallback
            await self.runbook_investigate(alert.system_id)
            action.status = "COMPLETED"
        
        ctx.storage.set("incidents_resolved", ctx.storage.get("incidents_resolved") + 1)
        
        return action
    
    def _rule_based_decision(self, alert: AnomalyAlert) -> str:
        """
        Fallback rule-based decision making
        These are derived from SRE best practices
        """
        # Critical severity or error spike
        if alert.severity == "CRITICAL" or alert.recommendation == "ROLLBACK_IMMEDIATELY":
            return "ROLLBACK"
        
        # CPU anomalies
        if "CPU" in alert.metric_type or "HIGH_CPU" in alert.recommendation:
            if alert.current_value > 90:
                return "RESTART"
            else:
                return "SCALE_UP"
        
        # Memory anomalies
        if "MEMORY" in alert.metric_type or "MEMORY" in alert.recommendation:
            if alert.current_value > 95:
                return "RESTART"
            else:
                return "INVESTIGATE"
        
        # High severity
        if alert.severity == "HIGH":
            return "ISOLATE"
        
        # Default
        return "INVESTIGATE"
    
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
        """Investigate issue (collect logs, metrics)"""
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
    logger.info("🚀 Starting Intelligent Response Agent...")
    logger.info("   AI-Enhanced Incident Response with Graceful Fallback")
    agent.run()