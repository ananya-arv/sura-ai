"""
Intelligent Response Agent with Lava Gateway
Uses Lava to route AI requests with usage tracking
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

class LavaResponseAgent(BaseSuraAgent):
    """Response Agent powered by Lava Gateway"""
    
    def __init__(self):
        super().__init__(
            name="response_agent",
            seed=os.getenv("RESPONSE_SEED_PHRASE"),
            port=8003,
            capabilities=["incident_response", "autonomous_recovery", "lava_ai"]
        )
        
        self.active_incidents: Dict[str, dict] = {}
        self.runbooks = self.load_runbooks()
        self.lava_requests = []  # Track Lava usage
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"🚑 Response Agent started at {self.agent.address}")
            logger.info(f"🔮 Lava Gateway: {'Enabled' if lava_service.forward_token else 'Disabled (fallback mode)'}")
            
            ctx.storage.set("actions_taken", 0)
            ctx.storage.set("incidents_resolved", 0)
            ctx.storage.set("lava_requests", 0)
            
            # Test Lava connection
            if lava_service.forward_token:
                status = await lava_service.test_connection()
                logger.info(f"   Lava Status: {status.get('test_request', 'Not tested')}")
                if status.get('lava_request_id'):
                    logger.info(f"   Test Request ID: {status['lava_request_id']}")
        
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
        """
        Execute emergency response using Lava Gateway AI
        This is where the magic happens!
        """
        logger.info(f"⚡ Executing emergency response for {alert.alert_id}")
        logger.info(f"🔮 Using Lava Gateway for AI analysis...")
        
        # Get AI analysis through Lava
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
            logger.info(f"   Provider: {analysis.get('ai_provider')}")
            logger.info(f"   Recommendation: {analysis.get('recommendation')}")
            logger.info(f"   Confidence: {analysis.get('confidence', 0):.2f}")
            logger.info(f"   Reasoning: {analysis.get('reasoning')}")
            
            if analysis.get('lava_request_id'):
                logger.info(f"📊 Lava Request ID: {analysis['lava_request_id']}")
                logger.info(f"   Track usage: https://www.lavapayments.com/dashboard/build/explore")
            
            # Use AI recommendation if high confidence
            if analysis.get('confidence', 0) > 0.75:
                action_type = analysis['recommendation']
                reasoning = f"Lava AI ({analysis.get('confidence', 0):.0%} confident): {analysis.get('reasoning')}"
                lava_request_id = analysis.get('lava_request_id', '')
            else:
                # Fall back to rule-based
                logger.warning(f"Low AI confidence ({analysis.get('confidence', 0):.0%}), using rules")
                action_type = self._rule_based_decision(alert)
                reasoning = f"Rule-based (AI confidence too low)"
                lava_request_id = ''
        
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # Fallback to rules
            action_type = self._rule_based_decision(alert)
            reasoning = f"Fallback to rules (AI error: {str(e)[:50]})"
            lava_request_id = ''
        
        # Create action
        action = ResponseAction(
            action_id=f"ACTION-LAVA-{int(datetime.now().timestamp())}",
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
            logger.error(f"Unknown action type: {action_type}")
            action.status = "FAILED"
        
        ctx.storage.set("incidents_resolved", ctx.storage.get("incidents_resolved") + 1)
        
        return action
    
    def _rule_based_decision(self, alert: AnomalyAlert) -> str:
        """Fallback rule-based decision making"""
        if alert.recommendation == "ROLLBACK_IMMEDIATELY":
            return "ROLLBACK"
        elif "HIGH_CPU" in alert.recommendation:
            return "SCALE_UP"
        elif "MEMORY" in alert.recommendation:
            return "INVESTIGATE"
        else:
            return "ISOLATE"
    
    # Runbook implementations
    async def runbook_rollback(self, target):
        """Rollback runbook"""
        logger.info(f"📖 Running ROLLBACK runbook on {target}")
        await asyncio.sleep(2)
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
    
    async def runbook_scale_down(self, target):
        """Scale down runbook"""
        logger.info(f"📖 Running SCALE_DOWN runbook on {target}")
        await asyncio.sleep(2)
        logger.info(f"✅ Scale down complete")
    
    async def runbook_isolate(self, target):
        """Isolate system runbook"""
        logger.info(f"📖 Running ISOLATE runbook on {target}")
        await asyncio.sleep(1)
        logger.info(f"✅ System isolated")

# Initialize agent
lava_response_agent = LavaResponseAgent()
agent = lava_response_agent.get_agent()

if __name__ == "__main__":
    agent.run()