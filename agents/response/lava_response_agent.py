"""
Response Agent using Lava AI for incident analysis
This replaces Groq with Claude Sonnet 3.5 through Lava
"""

from agents.response.response_agent import ResponseAgent, ResponseAction
from services.lava_service import lava_service
from uagents import Context
from loguru import logger
import os

class LavaResponseAgent(ResponseAgent):
    """Enhanced Response Agent with Claude Sonnet 3.5 via Lava"""
    
    def __init__(self):
        super().__init__()
        logger.info("🌊 Using Lava AI (Claude Sonnet 3.5) for incident analysis")
    
    async def execute_emergency_response(self, ctx: Context, alert) -> ResponseAction:
        """AI-enhanced emergency response using Claude via Lava"""
        logger.info(f"🤖 Using Claude Sonnet 3.5 (via Lava) for incident analysis...")
        
        # Prepare incident data
        incident_data = {
            "alert_id": alert.alert_id,
            "severity": alert.severity,
            "system_id": alert.system_id,
            "metric_type": alert.metric_type,
            "current_value": alert.current_value,
            "expected_value": alert.expected_value,
            "confidence": alert.confidence
        }
        
        # Get AI analysis through Lava
        ai_analysis = await lava_service.analyze_incident(incident_data)
        
        logger.info(f"🧠 Claude Recommendation: {ai_analysis.get('recommendation')} "
                   f"(confidence: {ai_analysis.get('confidence', 0):.2f})")
        logger.info(f"💰 Track costs at: https://lavapayments.com/dashboard")
        
        # Use AI recommendation if high confidence
        if ai_analysis.get('confidence', 0) > 0.75:
            action_type = ai_analysis['recommendation']
            reasoning = ai_analysis.get('reasoning', 'Claude-recommended action')
        else:
            # Fallback to rule-based
            logger.warning("Low Claude confidence, using rule-based decision")
            return await super().execute_emergency_response(ctx, alert)
        
        # Execute action
        action = ResponseAction(
            action_id=f"ACTION-LAVA-{alert.alert_id}",
            action_type=action_type,
            target_systems=[alert.system_id],
            reason=f"Claude Analysis (Lava): {reasoning}",
            status="INITIATED",
            timestamp=alert.timestamp
        )
        
        # Execute runbook
        if action_type in self.runbooks:
            await self.runbooks[action_type](alert.system_id)
            action.status = "COMPLETED"
        else:
            logger.error(f"Unknown action type: {action_type}")
            action.status = "FAILED"
        
        return action

# Use Lava-powered Response Agent
lava_response_agent = LavaResponseAgent()
agent = lava_response_agent.get_agent()

if __name__ == "__main__":
    agent.run()