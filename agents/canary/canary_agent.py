from uagents import Context, Model
import os
from agents.base_agent import BaseSuraAgent, AgentMessage
from typing import Optional, List
import asyncio
import random
from loguru import logger
from dotenv import load_dotenv
from datetime import datetime

class UpdatePackage(Model):
    """Represents a software update to be tested"""
    update_id: str
    version: str
    description: str
    target_systems: List[str]
    timestamp: float

class CanaryTestResult(Model):
    """Result of canary testing"""
    update_id: str
    success: bool
    affected_systems: int
    error_rate: float
    latency_impact: float
    recommendation: str  # "DEPLOY", "ROLLBACK", "INVESTIGATE"
    details: str

class CanaryAgent(BaseSuraAgent):
    def __init__(self):
        load_dotenv()
        super().__init__(
            name="canary_agent",
            seed=os.getenv("CANARY_SEED_PHRASE"),
            port=8001,
            capabilities=["canary_testing", "deployment_validation"]  # ADD THIS
        )
        
        self.canary_percentage = 0.001  # 0.1% of systems
        self.test_duration = 30  # seconds
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"🐦 Canary Agent started at {self.agent.address}")
            ctx.storage.set("tests_run", 0)
            ctx.storage.set("incidents_prevented", 0)
        
        @self.agent.on_message(model=UpdatePackage)
        async def handle_update(ctx: Context, sender: str, msg: UpdatePackage):
            logger.info(f"📦 Received update {msg.update_id} for testing")
            
            # Run canary test
            result = await self.run_canary_test(ctx, msg)
            
            # Send result to Response Agent
            await self.send_to_peer(ctx, "response_agent", CanaryTestResult(**result))

            logger.info(f"✅ Canary test complete: {result['recommendation']}")
    
    async def run_canary_test(self, ctx: Context, update: UpdatePackage) -> dict:
        """Simulate canary deployment and testing"""
        logger.info(f"🧪 Starting canary test for {update.update_id}")
        
        # Select canary systems (0.1% of fleet)
        total_systems = len(update.target_systems)
        canary_count = max(1, int(total_systems * self.canary_percentage))
        canary_systems = random.sample(update.target_systems, canary_count)
        
        logger.info(f"📊 Testing on {canary_count} of {total_systems} systems")
        
        # Simulate deployment
        await asyncio.sleep(2)
        
        # Simulate monitoring period
        logger.info(f"⏱️  Monitoring for {self.test_duration} seconds...")
        error_count = 0
        
        for i in range(self.test_duration):
            await asyncio.sleep(1)
            
            # Simulate checking system health
            # THIS IS WHERE YOU'D INTEGRATE REAL MONITORING
            if random.random() < 0.02:  # 2% chance of error per second
                error_count += 1
                logger.warning(f"⚠️  Error detected on canary system")
        
        error_rate = error_count / canary_count
        latency_impact = random.uniform(-0.1, 0.3)  # Simulated latency change
        
        # Determine recommendation
        if error_rate > 0.05:  # More than 5% error rate
            recommendation = "ROLLBACK"
            ctx.storage.set("incidents_prevented", ctx.storage.get("incidents_prevented") + 1)
        elif error_rate > 0.01 or latency_impact > 0.2:
            recommendation = "INVESTIGATE"
        else:
            recommendation = "DEPLOY"
        
        ctx.storage.set("tests_run", ctx.storage.get("tests_run") + 1)
        
        return {
            "update_id": update.update_id,
            "success": recommendation == "DEPLOY",
            "affected_systems": canary_count,
            "error_rate": error_rate,
            "latency_impact": latency_impact,
            "recommendation": recommendation,
            "details": f"Tested on {canary_count} systems for {self.test_duration}s. Error rate: {error_rate:.2%}"
        }

# Initialize agent
canary_agent = CanaryAgent()
agent = canary_agent.get_agent()

if __name__ == "__main__":
    agent.run()
