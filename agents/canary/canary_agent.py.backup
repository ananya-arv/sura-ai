"""
Fixed Canary Agent - Uses centralized message models
"""
from uagents import Context, Model
import os

# ✅ CRITICAL FIX: Import from centralized messages.py
from agents.messages import UpdatePackage, CanaryTestResult

from agents.base_agent import BaseSuraAgent
from typing import Optional, List
import asyncio
import random
from loguru import logger
from dotenv import load_dotenv
from datetime import datetime

class CanaryAgent(BaseSuraAgent):
    def __init__(self):
        load_dotenv()
        super().__init__(
            name="canary_agent",
            seed=os.getenv("CANARY_SEED_PHRASE"),
            port=8001,
            capabilities=["canary_testing", "deployment_validation"],
        )
        
        self.canary_percentage = 0.001  # 0.1% of systems
        self.test_duration = 30  # seconds
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"🐦 Canary Agent started at {self.agent.address}")
            
            # ✅ FIX: Initialize storage properly
            ctx.storage.set("tests_run", 0)
            ctx.storage.set("incidents_prevented", 0)
            
            logger.info(f"✅ Storage initialized: tests_run=0, incidents_prevented=0")
        
        @self.agent.on_message(model=UpdatePackage)
        async def handle_update(ctx: Context, sender: str, msg: UpdatePackage):
            logger.info(f"📦 Received update {msg.update_id} for testing")
            logger.info(f"   From: {sender[:20]}...")
            logger.info(f"   Version: {msg.version}")
            logger.info(f"   Target systems: {len(msg.target_systems)}")
            
            # Run canary test
            result = await self.run_canary_test(ctx, msg)
            
            # ✅ FIX: Update storage IMMEDIATELY after test
            tests_run = ctx.storage.get("tests_run") or 0
            ctx.storage.set("tests_run", tests_run + 1)
            logger.info(f"📊 Tests run updated: {tests_run + 1}")
            
            if result['recommendation'] == "ROLLBACK":
                incidents_prevented = ctx.storage.get("incidents_prevented") or 0
                ctx.storage.set("incidents_prevented", incidents_prevented + 1)
                logger.info(f"🛡️  Bad update prevented! Total: {incidents_prevented + 1}")
            
            # Send result to Response Agent
            canary_result = CanaryTestResult(**result)
            
            logger.info(f"📤 Sending result to Response Agent...")
            success = await self.send_to_peer(ctx, "response_agent", canary_result)
            
            if success:
                logger.info(f"✅ CanaryTestResult sent successfully")
            else:
                logger.error(f"❌ Failed to send CanaryTestResult")
            
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
            # Higher error rate for "broken" updates
            if "broken" in update.version.lower() or "faulty" in update.description.lower():
                if random.random() < 0.05:  # 5% chance of error per second for bad updates
                    error_count += 1
                    logger.warning(f"⚠️  Error detected on canary system")
        
        error_rate = error_count / canary_count if canary_count > 0 else 0
        latency_impact = random.uniform(-0.1, 0.3)  # Simulated latency change
        
        # Determine recommendation
        if error_rate > 0.05:  # More than 5% error rate
            recommendation = "ROLLBACK"
            logger.warning(f"🚨 HIGH ERROR RATE: {error_rate:.2%} - Recommending ROLLBACK")
        elif error_rate > 0.01 or latency_impact > 0.2:
            recommendation = "INVESTIGATE"
            logger.warning(f"⚠️  Elevated metrics - Recommending INVESTIGATE")
        else:
            recommendation = "DEPLOY"
            logger.info(f"✅ Tests passed - Recommending DEPLOY")
        
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