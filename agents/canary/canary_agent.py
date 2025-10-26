"""
AI-Enhanced Canary Agent - Uses Lava AI for deployment decisions
Instead of rule-based thresholds, asks Claude to analyze canary test results
"""
from uagents import Context, Model
import os

from agents.messages import UpdatePackage, CanaryTestResult
from agents.base_agent import BaseSuraAgent
from typing import Optional, List
import asyncio
import random
from loguru import logger
from dotenv import load_dotenv
from datetime import datetime

# Import Lava AI service
from services.lava_service import lava_service

class CanaryAgent(BaseSuraAgent):
    def __init__(self):
        load_dotenv()
        super().__init__(
            name="canary_agent",
            seed=os.getenv("CANARY_SEED_PHRASE"),
            port=8001,
            capabilities=["canary_testing", "deployment_validation", "ai_decision_making"],
        )
        
        self.canary_percentage = 0.01  # 1% of systems (more reliable than 0.1%)
        self.test_duration = 30  # seconds
        
        # Check if AI is available
        self.ai_available = lava_service.available
        
        if self.ai_available:
            logger.info("🤖 AI-Enhanced Canary Agent")
            logger.info("   Will consult Claude for deployment decisions")
        else:
            logger.warning("⚠️  AI not available - using rule-based fallback")
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"🐦 Canary Agent started at {self.agent.address}")
            
            ctx.storage.set("tests_run", 0)
            ctx.storage.set("incidents_prevented", 0)
            ctx.storage.set("ai_decisions", 0)
            
            logger.info(f"✅ Storage initialized")
            logger.info(f"🤖 AI Mode: {'ENABLED' if self.ai_available else 'DISABLED (rule-based fallback)'}")
        
        @self.agent.on_message(model=UpdatePackage)
        async def handle_update(ctx: Context, sender: str, msg: UpdatePackage):
            logger.info(f"📦 Received update {msg.update_id} for testing")
            logger.info(f"   From: {sender[:20]}...")
            logger.info(f"   Version: {msg.version}")
            logger.info(f"   Target systems: {len(msg.target_systems)}")
            
            # Run canary test (collects metrics)
            test_metrics = await self.run_canary_test(ctx, msg)
            
            # Ask AI to make the decision
            decision = await self.get_ai_decision(ctx, msg, test_metrics)
            
            # Build result with AI decision
            result = CanaryTestResult(
                update_id=msg.update_id,
                success=decision['recommendation'] == "DEPLOY",
                affected_systems=test_metrics['canary_count'],
                error_rate=test_metrics['error_rate'],
                latency_impact=test_metrics['latency_impact'],
                recommendation=decision['recommendation'],
                details=decision['reasoning']
            )
            
            # Update storage
            tests_run = ctx.storage.get("tests_run") or 0
            ctx.storage.set("tests_run", tests_run + 1)
            
            if decision['used_ai']:
                ai_decisions = ctx.storage.get("ai_decisions") or 0
                ctx.storage.set("ai_decisions", ai_decisions + 1)
            
            if result.recommendation == "ROLLBACK":
                incidents_prevented = ctx.storage.get("incidents_prevented") or 0
                ctx.storage.set("incidents_prevented", incidents_prevented + 1)
                logger.warning(f"🛡️  Bad update prevented! Total: {incidents_prevented + 1}")
            
            # Send result to Response Agent
            logger.info(f"📤 Sending AI-backed decision to Response Agent...")
            success = await self.send_to_peer(ctx, "response_agent", result)
            
            if success:
                logger.info(f"✅ Decision sent: {result.recommendation}")
                logger.info(f"   AI Reasoning: {decision['reasoning'][:100]}...")
            else:
                logger.error(f"❌ Failed to send result")
    
    async def run_canary_test(self, ctx: Context, update: UpdatePackage) -> dict:
        """
        Run canary deployment and collect metrics
        (No decision-making here, just data collection)
        """
        logger.info(f"🧪 Starting canary test for {update.update_id}")
        
        # Select canary systems
        total_systems = len(update.target_systems)
        canary_count = max(1, int(total_systems * self.canary_percentage))
        canary_systems = random.sample(update.target_systems, canary_count)
        
        logger.info(f"📊 Testing on {canary_count} of {total_systems} systems")
        
        # Simulate deployment
        await asyncio.sleep(2)
        
        # Monitor for errors
        logger.info(f"⏱️  Monitoring for {self.test_duration} seconds...")
        error_count = 0
        warning_count = 0
        
        for i in range(self.test_duration):
            await asyncio.sleep(1)
            
            # Simulate checking system health
            if "broken" in update.version.lower() or "faulty" in update.description.lower():
                # Broken updates have higher error rate
                if random.random() < 0.1:  # 10% chance per second
                    error_count += 1
                    logger.warning(f"⚠️  Error detected on canary system")
                elif random.random() < 0.15:  # 15% chance of warnings
                    warning_count += 1
        
        error_rate = error_count / (canary_count * self.test_duration) if canary_count > 0 else 0
        warning_rate = warning_count / (canary_count * self.test_duration) if canary_count > 0 else 0
        latency_impact = random.uniform(-0.1, 0.3)
        
        logger.info(f"📈 Test metrics collected:")
        logger.info(f"   Errors: {error_count} (rate: {error_rate:.4f})")
        logger.info(f"   Warnings: {warning_count} (rate: {warning_rate:.4f})")
        logger.info(f"   Latency impact: {latency_impact:+.2f}x")
        
        return {
            "canary_count": canary_count,
            "total_systems": total_systems,
            "error_count": error_count,
            "warning_count": warning_count,
            "error_rate": error_rate,
            "warning_rate": warning_rate,
            "latency_impact": latency_impact,
            "test_duration": self.test_duration
        }
    
    async def get_ai_decision(self, ctx: Context, update: UpdatePackage, metrics: dict) -> dict:
        """
        Ask Claude (via Lava) to analyze canary test results and make deployment decision
        """
        if not self.ai_available:
            logger.warning("⚠️  AI not available, using rule-based fallback")
            return self._fallback_decision(metrics)
        
        logger.info("🤖 Consulting Claude for deployment decision...")
        
        # Build analysis request for Lava
        analysis_data = {
            "alert_id": f"CANARY-{update.update_id}",
            "severity": "HIGH" if metrics['error_rate'] > 0.01 else "MEDIUM",
            "system_id": "canary_deployment",
            "metric_type": "CANARY_TEST_RESULTS",
            "current_value": metrics['error_rate'] * 100,  # As percentage
            "expected_value": 0.0,  # Expecting no errors
            "confidence": 0.95,
            "additional_context": {
                "update_id": update.update_id,
                "version": update.version,
                "description": update.description,
                "canary_systems": metrics['canary_count'],
                "total_systems": metrics['total_systems'],
                "errors": metrics['error_count'],
                "warnings": metrics['warning_count'],
                "error_rate": f"{metrics['error_rate']:.4f}",
                "warning_rate": f"{metrics['warning_rate']:.4f}",
                "latency_impact": f"{metrics['latency_impact']:+.2f}x",
                "test_duration": metrics['test_duration']
            }
        }
        
        try:
            # Ask Lava AI for decision
            ai_result = await lava_service.analyze_canary_deployment(analysis_data)
            
            recommendation = ai_result.get('recommendation', 'INVESTIGATE')
            reasoning = ai_result.get('reasoning', 'AI analysis completed')
            confidence = ai_result.get('confidence', 0.7)
            lava_request_id = ai_result.get('lava_request_id', '')
            
            logger.info(f"🤖 Claude's Decision:")
            logger.info(f"   Recommendation: {recommendation}")
            logger.info(f"   Confidence: {confidence:.2f}")
            logger.info(f"   Reasoning: {reasoning[:150]}...")
            
            if lava_request_id:
                logger.info(f"📊 Lava Request ID: {lava_request_id}")
            
            return {
                "recommendation": recommendation,
                "reasoning": f"AI Analysis: {reasoning}",
                "confidence": confidence,
                "used_ai": True,
                "lava_request_id": lava_request_id
            }
            
        except Exception as e:
            logger.error(f"❌ AI decision failed: {e}")
            logger.warning("⚠️  Falling back to rule-based decision")
            return self._fallback_decision(metrics)
    
    def _fallback_decision(self, metrics: dict) -> dict:
        """Rule-based fallback when AI is unavailable"""
        error_rate = metrics['error_rate']
        latency_impact = metrics['latency_impact']
        
        if error_rate > 0.05:  # >5% error rate
            recommendation = "ROLLBACK"
            reasoning = f"High error rate detected: {error_rate:.2%}"
        elif error_rate > 0.01 or latency_impact > 0.2:
            recommendation = "INVESTIGATE"
            reasoning = f"Elevated metrics: {error_rate:.2%} errors, {latency_impact:+.2f}x latency"
        else:
            recommendation = "DEPLOY"
            reasoning = "All metrics within acceptable range"
        
        return {
            "recommendation": recommendation,
            "reasoning": f"Rule-based: {reasoning}",
            "confidence": 0.8,
            "used_ai": False,
            "lava_request_id": ""
        }

# Initialize agent
canary_agent = CanaryAgent()
agent = canary_agent.get_agent()

if __name__ == "__main__":
    agent.run()