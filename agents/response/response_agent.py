from uagents import Context, Model
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
    action_type: str  # "ROLLBACK", "FAILOVER", "SCALE", "ISOLATE"
    target_systems: List[str]
    reason: str
    status: str  # "INITIATED", "IN_PROGRESS", "COMPLETED", "FAILED"
    timestamp: float

class ResponseAgent(BaseSuraAgent):
    def __init__(self):
        super().__init__(
            name="response_agent",
            seed="response_seed_phrase_11111",
            port=8003
        )
        
        self.active_incidents: Dict[str, dict] = {}
        self.runbooks = self.load_runbooks()
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"🚑 Response Agent started at {self.agent.address}")
            ctx.storage.set("actions_taken", 0)
            ctx.storage.set("incidents_resolved", 0)
        
        @self.agent.on_message(model=CanaryTestResult)
        async def handle_canary_result(ctx: Context, sender: str, msg: CanaryTestResult):
            logger.info(f"📊 Received canary result: {msg.recommendation}")
            
            if msg.recommendation == "ROLLBACK":
                action = await self.execute_rollback(ctx, msg.update_id, msg.details)
                ctx.storage.set("actions_taken", ctx.storage.get("actions_taken") + 1)
                
                # Notify Communication Agent
                await ctx.send(
                    "agent1q...",  # Communication agent address
                    action
                )
        
        @self.agent.on_message(model=AnomalyAlert)
        async def handle_anomaly(ctx: Context, sender: str, msg: AnomalyAlert):
            logger.warning(f"🚨 Received anomaly alert: {msg.severity} - {msg.metric_type}")
            
            if msg.severity in ["HIGH", "CRITICAL"]:
                action = await self.execute_emergency_response(ctx, msg)
                ctx.storage.set("actions_taken", ctx.storage.get("actions_taken") + 1)
                
                # Notify Communication Agent
                await ctx.send(
                    "agent1q...",  # Communication agent address
                    action
                )
    
    def load_runbooks(self) -> Dict[str, callable]:
        """Load automated response runbooks"""
        return {
            "ROLLBACK": self.runbook_rollback,
            "FAILOVER": self.runbook_failover,
            "SCALE_UP": self.runbook_scale_up,
            "ISOLATE": self.runbook_isolate
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
        """Execute emergency response based on anomaly"""
        logger.info(f"⚡ Executing emergency response for {alert.alert_id}")
        
        # Determine action based on recommendation
        if alert.recommendation == "ROLLBACK_IMMEDIATELY":
            action_type = "ROLLBACK"
            runbook = self.runbooks["ROLLBACK"]
        elif "HIGH_CPU" in alert.recommendation:
            action_type = "SCALE_UP"
            runbook = self.runbooks["SCALE_UP"]
        else:
            action_type = "ISOLATE"
            runbook = self.runbooks["ISOLATE"]
        
        action = ResponseAction(
            action_id=f"ACTION-{int(datetime.now().timestamp())}",
            action_type=action_type,
            target_systems=[alert.system_id],
            reason=f"Anomaly detected: {alert.metric_type} = {alert.current_value}",
            status="INITIATED",
            timestamp=datetime.now().timestamp()
        )
        
        # Execute runbook
        await runbook(alert.system_id)
        
        action.status = "COMPLETED"
        ctx.storage.set("incidents_resolved", ctx.storage.get("incidents_resolved") + 1)
        
        return action
    
    async def runbook_rollback(self, target):
        """Rollback runbook"""
        logger.info(f"📖 Running ROLLBACK runbook on {target}")
        await asyncio.sleep(2)  # Simulate rollback time
        logger.info(f"✅ Rollback complete")
    
    async def runbook_failover(self, target):
        """Failover runbook"""
        logger.info(f"📖 Running FAILOVER runbook on {target}")
        await asyncio.sleep(3)
        logger.info(f"✅ Failover complete")
    
    async def runbook_scale_up(self, target):
        """Scale up runbook"""
        logger.info(f"📖 Running SCALE_UP runbook on {target}")
        await asyncio.sleep(2)
        logger.info(f"✅ Scale up complete")
    
    async def runbook_isolate(self, target):
        """Isolate system runbook"""
        logger.info(f"📖 Running ISOLATE runbook on {target}")
        await asyncio.sleep(1)
        logger.info(f"✅ System isolated")

response_agent = ResponseAgent()
agent = response_agent.get_agent()

if __name__ == "__main__":
    agent.run()
