from uagents import Context, Model
import os


from agents.messages import ResponseAction, StatusUpdate

from agents.base_agent import BaseSuraAgent


from typing import List
from loguru import logger
from dotenv import load_dotenv
from datetime import datetime
import json

class CommunicationAgent(BaseSuraAgent):
    def __init__(self):
        load_dotenv()
        super().__init__(
            name="communication_agent",
            seed=os.getenv("COMMUNICATION_SEED_PHRASE"),
            port=8004,
            capabilities=["notifications", "status_updates", "stakeholder_communication"]
        )
        
        self.status_page = []
        self.notifications_sent = 0
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"📢 Communication Agent started at {self.agent.address}")
            
            # ✅ Initialize storage
            ctx.storage.set("notifications_sent", 0)
            logger.info(f"✅ Storage initialized: notifications_sent=0")
        
        @self.agent.on_message(model=ResponseAction)
        async def handle_action(ctx: Context, sender: str, msg: ResponseAction):
            logger.info(f"📨 Received action notification: {msg.action_type}")
            logger.info(f"   From: {sender[:20]}...")
            logger.info(f"   Action ID: {msg.action_id}")
            logger.info(f"   Status: {msg.status}")
            
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
            
            # ✅ Update storage IMMEDIATELY
            notifications_sent = ctx.storage.get("notifications_sent") or 0
            ctx.storage.set("notifications_sent", notifications_sent + 1)
            logger.info(f"📊 Notifications sent updated: {notifications_sent + 1}")
    
    async def publish_status_update(self, ctx: Context, status: StatusUpdate):
        """Publish to status page"""
        self.status_page.append(status.dict())
        logger.info(f"📄 Status page updated: {status.title}")
        
        # Write to file for dashboard
        try:
            with open("status_page.json", "w") as f:
                json.dump(self.status_page, f, indent=2)
            logger.info(f"✅ Status page file updated")
        except Exception as e:
            logger.error(f"❌ Failed to write status page: {e}")
    
    async def send_notifications(self, ctx: Context, status: StatusUpdate):
        """Send notifications to stakeholders"""
        # In production: email, Slack, PagerDuty, SMS, etc.
        logger.info(f"🔔 NOTIFICATION SENT:")
        logger.info(f"   Title: {status.title}")
        logger.info(f"   Status: {status.status}")
        logger.info(f"   Incident ID: {status.incident_id}")
        logger.info(f"   Affected: {', '.join(status.affected_services[:3])}")
        
        if len(status.affected_services) > 3:
            logger.info(f"   ... and {len(status.affected_services) - 3} more systems")

communication_agent = CommunicationAgent()
agent = communication_agent.get_agent()

if __name__ == "__main__":
    agent.run()