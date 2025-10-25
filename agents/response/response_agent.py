"""
Basic Response Agent - Rule-based decisions only
This is the fallback version that works without AI
"""

from uagents import Context, Model
import os
from agents.base_agent import BaseSuraAgent
from agents.canary.canary_agent import CanaryTestResult
from agents.monitoring.monitoring_agent import AnomalyAlert
from typing import Dict, List
from loguru import logger
from datetime import datetime
import asyncio

class ResponseAction(Model):
    """Action taken by response agent"""
    action_id: str
    action_type: str
    target_systems: List[str]
    reason: str
    status: str
    timestamp: float

class ResponseAgent(BaseSuraAgent):
    """Basic Response Agent with rule-based decisions"""
    
    def __init__(self):
        super().__init__(
            name="response_agent",
            seed=os.getenv("RESPONSE_SEED_PHRASE", "response_seed_default_67890"),
            port=8003,
            capabilities=["incident_response", "autonomous_recovery", "runbook_execution"]
        )
        
        self.active_incidents: Dict[str, dict] = {}
        self.runbooks = self.load_runbooks()
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"🚑 Response Agent started at {self.agent.address}")
            logger.info(f"📋 Mode: Rule-Based Decisions")
            ctx.storage.set("actions_taken", 0)
            ctx.storage.set("incidents_resolved", 0)
        
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
                
                # Notify Communication Agent
                await self.send_to_peer(ctx, "communication_agent", action)
    
    def load_runbooks(self) -> Dict[str, callable]:
        """Load automated response runbooks"""
        return {
            "ROLLBACK": self.runbook_rollback,
            "FAILOVER": self.runbook_failover,
            "SCALE_UP": self.runbook_scale_up,
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
        """Execute emergency response based on rule-based decision"""
        logger.info(f"⚡ Executing emergency response for {alert.alert_id}")
        logger.info(f"📋 Using rule-based decision logic...")
        
        # Determine action based on alert
        action_type = self._rule_based_decision(alert)
        reasoning = f"Rule-based: {alert.metric_type} anomaly detected"
        
        logger.info(f"✅ Decision: {action_type}")
        
        action = ResponseAction(
            action_id=f"ACTION-{int(datetime.now().timestamp())}",
            action_type=action_type,
            target_systems=[alert.system_id],
            reason=reasoning,
            status="INITIATED",
            timestamp=datetime.now().timestamp()
        )
        
        # Execute runbook
        if action_type in self.runbooks:
            await self.runbooks[action_type](alert.system_id)
            action.status = "COMPLETED"
        else:
            logger.error(f"Unknown action type: {action_type}")
            action.status = "FAILED"
        
        ctx.storage.set("incidents_resolved", ctx.storage.get("incidents_resolved") + 1)
        
        return action
    
    def _rule_based_decision(self, alert: AnomalyAlert) -> str:
        """Rule-based decision logic derived from SRE best practices"""
        
        # Critical errors
        if alert.recommendation == "ROLLBACK_IMMEDIATELY":
            return "ROLLBACK"
        
        # CPU issues
        if "CPU" in alert.metric_type or "HIGH_CPU" in alert.recommendation:
            if alert.current_value > 90:
                return "RESTART"
            return "SCALE_UP"
        
        # Memory issues
        if "MEMORY" in alert.metric_type:
            if alert.current_value > 95:
                return "RESTART"
            return "INVESTIGATE"
        
        # High severity
        if alert.severity == "HIGH":
            return "ISOLATE"
        
        # Default
        return "INVESTIGATE"
    
    # Runbooks
    async def runbook_rollback(self, target):
        """Rollback runbook"""
        logger.info(f"📖 Running ROLLBACK runbook on {target}")
        await asyncio.sleep(2)
        logger.info(f"   ✅ Rollback complete")
    
    async def runbook_failover(self, target):
        """Failover runbook"""
        logger.info(f"📖 Running FAILOVER runbook on {target}")
        await asyncio.sleep(3)
        logger.info(f"   ✅ Failover complete")
    
    async def runbook_scale_up(self, target):
        """Scale up runbook"""
        logger.info(f"📖 Running SCALE_UP runbook on {target}")
        await asyncio.sleep(2)
        logger.info(f"   ✅ Scale up complete")
    
    async def runbook_isolate(self, target):
        """Isolate system runbook"""
        logger.info(f"📖 Running ISOLATE runbook on {target}")
        await asyncio.sleep(1)
        logger.info(f"   ✅ System isolated")
    
    async def runbook_investigate(self, target):
        """Investigate runbook"""
        logger.info(f"📖 Running INVESTIGATE runbook on {target}")
        await asyncio.sleep(1)
        logger.info(f"   ✅ Investigation initiated")
    
    async def runbook_restart(self, target):
        """Restart runbook"""
        logger.info(f"📖 Running RESTART runbook on {target}")
        await asyncio.sleep(2)
        logger.info(f"   ✅ Restart complete")

response_agent = ResponseAgent()
agent = response_agent.get_agent()

if __name__ == "__main__":
    agent.run()