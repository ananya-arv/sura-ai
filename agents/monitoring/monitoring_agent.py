from uagents import Context, Model
from agents.base_agent import BaseSuraAgent
import asyncio
import psutil
import requests
from typing import Dict, List
from loguru import logger
from datetime import datetime
import random

class SystemMetrics(Model):
    """Real-time system metrics"""
    system_id: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    error_count: int
    timestamp: float

class AnomalyAlert(Model):
    """Alert when anomaly detected"""
    alert_id: str
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    system_id: str
    metric_type: str
    current_value: float
    expected_value: float
    confidence: float
    timestamp: float
    recommendation: str

class MonitoringAgent(BaseSuraAgent):
    def __init__(self):
        super().__init__(
            name="monitoring_agent",
            seed="monitoring_seed_phrase_67890",
            port=8002
        )
        
        self.monitoring_interval = 5  # seconds
        self.baseline_metrics: Dict[str, Dict] = {}
        self.anomaly_threshold = 0.8
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"👁️  Monitoring Agent started at {self.agent.address}")
            ctx.storage.set("anomalies_detected", 0)
            
            # Start continuous monitoring
            asyncio.create_task(self.monitor_loop(ctx))
        
        @self.agent.on_interval(period=self.monitoring_interval)
        async def monitor_systems(ctx: Context):
            # This runs every 5 seconds
            pass
    
    async def monitor_loop(self, ctx: Context):
        """Continuous monitoring loop"""
        monitored_systems = [f"server-{i}" for i in range(10)]  # Mock systems
        
        while True:
            for system_id in monitored_systems:
                metrics = await self.collect_metrics(system_id)
                anomaly = await self.detect_anomaly(system_id, metrics)
                
                if anomaly:
                    logger.warning(f"🚨 ANOMALY DETECTED on {system_id}")
                    ctx.storage.set("anomalies_detected", ctx.storage.get("anomalies_detected") + 1)
                    
                    # Send alert to Response Agent
                    await ctx.send(
                        "agent1q2kxet3vh0scsf0sm7y2erzz33cve6tv5uk63x64upw5g68fr9vx44lgw",
                        anomaly
                    )
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def collect_metrics(self, system_id: str) -> SystemMetrics:
        """Collect metrics from a system"""
        # In production, this would call actual monitoring APIs
        # For demo, we simulate with psutil + randomness
        
        return SystemMetrics(
            system_id=system_id,
            cpu_usage=psutil.cpu_percent() + random.uniform(-10, 10),
            memory_usage=psutil.virtual_memory().percent + random.uniform(-5, 5),
            disk_usage=psutil.disk_usage('/').percent,
            network_latency=random.uniform(10, 50),
            error_count=random.randint(0, 5),
            timestamp=datetime.now().timestamp()
        )
    
    async def detect_anomaly(self, system_id: str, metrics: SystemMetrics) -> Optional[AnomalyAlert]:
        """Detect if metrics indicate an anomaly"""
        
        # Get or create baseline for this system
        if system_id not in self.baseline_metrics:
            self.baseline_metrics[system_id] = {
                "cpu": metrics.cpu_usage,
                "memory": metrics.memory_usage,
                "latency": metrics.network_latency,
                "errors": metrics.error_count
            }
            return None
        
        baseline = self.baseline_metrics[system_id]
        
        # Check for anomalies
        if metrics.cpu_usage > baseline["cpu"] * 2.0:  # 2x normal CPU
            return AnomalyAlert(
                alert_id=f"ALERT-{system_id}-{int(datetime.now().timestamp())}",
                severity="HIGH",
                system_id=system_id,
                metric_type="CPU",
                current_value=metrics.cpu_usage,
                expected_value=baseline["cpu"],
                confidence=0.9,
                timestamp=datetime.now().timestamp(),
                recommendation="INVESTIGATE_HIGH_CPU"
            )
        
        if metrics.error_count > 10:
            return AnomalyAlert(
                alert_id=f"ALERT-{system_id}-{int(datetime.now().timestamp())}",
                severity="CRITICAL",
                system_id=system_id,
                metric_type="ERRORS",
                current_value=float(metrics.error_count),
                expected_value=float(baseline["errors"]),
                confidence=0.95,
                timestamp=datetime.now().timestamp(),
                recommendation="ROLLBACK_IMMEDIATELY"
            )
        
        # Update baseline (exponential moving average)
        alpha = 0.1
        baseline["cpu"] = alpha * metrics.cpu_usage + (1 - alpha) * baseline["cpu"]
        baseline["memory"] = alpha * metrics.memory_usage + (1 - alpha) * baseline["memory"]
        
        return None

monitoring_agent = MonitoringAgent()
agent = monitoring_agent.get_agent()

if __name__ == "__main__":
    agent.run()
