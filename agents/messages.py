"""
Centralized Message Models for SuraAI
ALL agents must import from here to ensure schema compatibility
"""
from uagents import Model
from typing import List

# ============================================================================
# CANARY AGENT MESSAGES
# ============================================================================

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

# ============================================================================
# MONITORING AGENT MESSAGES
# ============================================================================

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

# ============================================================================
# RESPONSE AGENT MESSAGES
# ============================================================================

class ResponseAction(Model):
    """Action taken by response agent"""
    action_id: str
    action_type: str
    target_systems: List[str]
    reason: str
    status: str
    timestamp: float
    lava_request_id: str = ""  # Track Lava usage

# ============================================================================
# COMMUNICATION AGENT MESSAGES
# ============================================================================

class StatusUpdate(Model):
    """Status update for stakeholders"""
    incident_id: str
    status: str  # "INVESTIGATING", "MITIGATING", "RESOLVED"
    title: str
    description: str
    affected_services: List[str]
    timestamp: float