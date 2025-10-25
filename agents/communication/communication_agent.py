from uagents import Context, Model
from agents.base_agent import BaseSuraAgent
from agents.response.response_agent import ResponseAction
from typing import List
from loguru import logger
from datetime import datetime
import json

class StatusUpdate(Model):
    """Status update for stakeholders"""
    incident_id: str
    status: str  # "INVESTIGATING", "MITIGATING", "RESOLVED"
    title: str
    description: str
    affected_services: List[str]
    timestamp: float

class CommunicationAgent(BaseSuraAgent):
    def __init__(self):
        super().__init__(
            name="communication_agent",
            seed="communication_seed_phrase_22222",
            port=8004
        )
        
        self.status_page = []
        self.notifications_sent = 0
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"📢 Communication Agent started at {self.agent.address}")
            ctx.storage.set("notifications_sent", 0)
        
        @self.agent.on_message(model=ResponseAction)
        async def handle_action(ctx: Context, sender: str, msg: ResponseAction):
            logger.info(f"📨 Received action notification: {msg.action_type}")
            
            # Create status update
            status = StatusUpdate(
                incident_id=msg.action_id,
                status="RESOLVED" if msg.status == "COMPLETED" else "MITIGATING",
                title=f"{msg.action_type} - {msg.reason}",
                description=f"Automated {msg.action_type} executed on {len(msg.target_systems)} systems",
                affected_services=msg.target_systems,
                timestamp=msg.timestamp
            )
            
            # Publish status update
            await self.publish_status_update(ctx, status)
            
            # Send notifications
            await self.send_notifications(ctx, status)
            
            ctx.storage.set("notifications_sent", ctx.storage.get("notifications_sent") + 1)
    
    async def publish_status_update(self, ctx: Context, status: StatusUpdate):
        """Publish to status page"""
        self.status_page.append(status.dict())
        logger.info(f"📄 Status page updated: {status.title}")
        
        # Write to file for dashboard
        with open("status_page.json", "w") as f:
            json.dump(self.status_page, f, indent=2)
    
    async def send_notifications(self, ctx: Context, status: StatusUpdate):
        """Send notifications to stakeholders"""
        # In production: email, Slack, PagerDuty, SMS, etc.
        logger.info(f"🔔 NOTIFICATION SENT:")
        logger.info(f"   Title: {status.title}")
        logger.info(f"   Status: {status.status}")
        logger.info(f"   Affected: {', '.join(status.affected_services[:3])}")

communication_agent = CommunicationAgent()
agent = communication_agent.get_agent()

if __name__ == "__main__":
    agent.run()
