"""
Enhanced Monitoring Agent - Collects metrics from mock infrastructure API
"""
from uagents import Context, Model
from agents.base_agent import BaseSuraAgent
import asyncio
import aiohttp
from typing import Dict, List, Optional
from loguru import logger
from datetime import datetime

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
            port=8002,
            capabilities=["monitoring", "anomaly_detection", "real_time_polling"]  # ADD THIS
        )
        
        self.monitoring_interval = 5  # seconds
        self.baseline_metrics: Dict[str, Dict] = {}
        self.anomaly_threshold = 0.8
        self.mock_infrastructure_url = "http://localhost:8000"  # Mock API
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.info(f"👁️  Monitoring Agent started at {self.agent.address}")
            ctx.storage.set("anomalies_detected", 0)
            
            # Start continuous monitoring
            asyncio.create_task(self.monitor_loop(ctx))
    
    async def monitor_loop(self, ctx: Context):
        """Continuous monitoring loop - pulls from mock infrastructure"""
        
        # Get list of systems from mock infrastructure
        systems = await self.get_monitored_systems()
        logger.info(f"📊 Monitoring {len(systems)} systems")
        
        while True:
            for system_id in systems:
                try:
                    # Collect real metrics from mock API
                    metrics = await self.collect_metrics(system_id)
                    
                    # Detect anomalies
                    anomaly = await self.detect_anomaly(system_id, metrics)
                    
                    if anomaly:
                        logger.warning(f"🚨 ANOMALY DETECTED on {system_id}")
                        logger.warning(f"   Metric: {anomaly.metric_type}")
                        logger.warning(f"   Current: {anomaly.current_value:.2f}")
                        logger.warning(f"   Expected: {anomaly.expected_value:.2f}")
                        
                        ctx.storage.set("anomalies_detected", 
                                      ctx.storage.get("anomalies_detected") + 1)
                        
                        # Send alert to Response Agent
                        await self.send_to_peer(ctx, "response_agent", anomaly)
                
                except Exception as e:
                    logger.error(f"Error monitoring {system_id}: {e}")
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def get_monitored_systems(self) -> List[str]:
        """Get list of systems from mock infrastructure"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.mock_infrastructure_url}/systems") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("systems", [])[:10]  # Monitor first 10 for demo
                    else:
                        logger.error(f"Failed to get systems: {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"Failed to connect to mock infrastructure: {e}")
            return [f"server-{i}" for i in range(10)]  # Fallback
    
    async def collect_metrics(self, system_id: str) -> SystemMetrics:
        """
        Collect REAL metrics from mock infrastructure API
        This replaces the psutil simulation
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.mock_infrastructure_url}/system/{system_id}"
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # Extract metrics from mock infrastructure response
                        return SystemMetrics(
                            system_id=system_id,
                            cpu_usage=data.get("cpu", 0.0),
                            memory_usage=data.get("memory", 0.0),
                            disk_usage=50.0,  # Mock doesn't track this yet
                            network_latency=20.0,  # Can add to mock later
                            error_count=0 if data.get("status") == "healthy" else 10,
                            timestamp=datetime.now().timestamp()
                        )
                    else:
                        logger.error(f"System {system_id} not found")
                        return None
        
        except Exception as e:
            logger.error(f"Failed to collect metrics for {system_id}: {e}")
            return None
    
    async def detect_anomaly(self, system_id: str, metrics: SystemMetrics) -> Optional[AnomalyAlert]:
        """Detect if metrics indicate an anomaly"""
        
        if not metrics:
            return None
        
        # Get or create baseline for this system
        if system_id not in self.baseline_metrics:
            self.baseline_metrics[system_id] = {
                "cpu": metrics.cpu_usage,
                "memory": metrics.memory_usage,
                "latency": metrics.network_latency,
                "errors": metrics.error_count
            }
            logger.info(f"📊 Established baseline for {system_id}")
            return None
        
        baseline = self.baseline_metrics[system_id]
        
        # Check for CPU anomaly (2x normal)
        if metrics.cpu_usage > baseline["cpu"] * 2.0:
            logger.warning(f"⚠️  CPU anomaly: {metrics.cpu_usage:.1f}% vs baseline {baseline['cpu']:.1f}%")
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
        
        # Check for error count spike
        if metrics.error_count > 10:
            logger.warning(f"⚠️  Error spike: {metrics.error_count} errors detected")
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
        
        # Check for memory anomaly
        if metrics.memory_usage > baseline["memory"] * 1.8:
            logger.warning(f"⚠️  Memory anomaly: {metrics.memory_usage:.1f}% vs baseline {baseline['memory']:.1f}%")
            return AnomalyAlert(
                alert_id=f"ALERT-{system_id}-{int(datetime.now().timestamp())}",
                severity="MEDIUM",
                system_id=system_id,
                metric_type="MEMORY",
                current_value=metrics.memory_usage,
                expected_value=baseline["memory"],
                confidence=0.85,
                timestamp=datetime.now().timestamp(),
                recommendation="INVESTIGATE_MEMORY_LEAK"
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