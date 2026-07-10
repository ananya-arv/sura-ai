"""
Scenario definitions and signal synthesis shared across the Sura.ai experiments.

Design notes (why this file exists rather than reusing e2e_test_pipeline.py):

  * The original pipeline routes every scenario through the mock's
    /simulate-failure endpoint, which hardcodes cpu=95, memory=98
    (services/mock_infrastructure.py:90-93). Because MonitoringAgent.detect_anomaly
    checks CPU *before* memory (agents/monitoring/monitoring_agent.py:159-201),
    every injected failure collapses into a single "CPU / HIGH" alert regardless
    of the scenario's narrative. That makes the four scenarios statistically
    indistinguishable at the AnomalyAlert level (orientation finding #4).

  * To evaluate decision quality per scenario type we instead *synthesize* the
    metric signature each scenario is meant to represent (a memory leak really
    drives memory, not CPU), then run the REAL detection thresholds over it.
    We do not touch the mock or the agents. This keeps the original numbers
    reproducible while giving the experiments differentiated, realistic signals.

  * Thresholds below are copied verbatim from the live code so the experiments
    never invent new numbers.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from agents.messages import AnomalyAlert, CanaryTestResult

# ---------------------------------------------------------------------------
# Thresholds pulled directly from the live code (do not invent new numbers).
# ---------------------------------------------------------------------------
CPU_ANOMALY_RATIO = 2.0     # monitoring_agent.py:159  cpu > baseline * 2.0
MEM_ANOMALY_RATIO = 1.8     # monitoring_agent.py:189  memory > baseline * 1.8
ERROR_COUNT_LIMIT = 10      # monitoring_agent.py:174  error_count > 10
CANARY_ROLLBACK_ER = 0.05   # canary_agent.py:222      error_rate > 0.05 -> ROLLBACK
CANARY_INVESTIGATE_ER = 0.01  # canary_agent.py:225    error_rate > 0.01 -> INVESTIGATE

# Nominal healthy baselines (mock init ranges: cpu 20-40, memory 30-50).
BASELINE_CPU = 30.0
BASELINE_MEM = 40.0

# The full action vocabulary the Response Agent can emit (runbook keys,
# intelligent_response_agent.py:109-117) plus the canary DEPLOY verb.
ACTION_VOCAB = [
    "ROLLBACK", "FAILOVER", "SCALE_UP", "SCALE_DOWN",
    "ISOLATE", "INVESTIGATE", "RESTART", "DEPLOY",
]

# ===========================================================================
# GROUND TRUTH  (authoritative -- from the paper's "Agent Activation Sequence")
# ---------------------------------------------------------------------------
# Each scenario maps to the SET of acceptable correct actions (primary first),
# taken verbatim from the paper's table:
#   Faulty Update      -> Decision: ROLLBACK
#   Zone Failure       -> Executes FAILOVER runbook
#   Memory Leak        -> Sequential: RESTART then SCALE_UP
#   Cascading Failure  -> Parallel: ISOLATE affected + FAILOVER healthy
# Success = the agent's action is in the scenario's set. An action outside the
# set (but still an action) is a wrong-action; INVESTIGATE / no-op is a miss.
# ===========================================================================
GROUND_TRUTH: Dict[str, List[str]] = {
    "faulty_update": ["ROLLBACK"],
    "zone_failure": ["FAILOVER"],
    "memory_leak": ["RESTART", "SCALE_UP"],
    "cascading_failure": ["ISOLATE", "FAILOVER"],
}
GROUND_TRUTH_IS_TENTATIVE = False  # authoritative: paper's Agent Activation Sequence table


def primary_action(scenario: str) -> str:
    """The first (headline) correct action for a scenario."""
    return GROUND_TRUTH[scenario][0]


@dataclass
class Trial:
    """
    One synthesized trial == one incident.

    `anomaly` / `canary_result` is the PRIMARY signal used for per-incident
    decision scoring (success / wrong-action), so every scenario contributes
    exactly N comparable decisions. `burst` holds the full set of alerts the
    monitoring loop would raise for this incident (for a cascading zone failure
    that is many systems polled repeatedly); it is used only to measure alert
    consolidation, never for success scoring.
    """
    scenario: str
    trial_index: int
    system_id: str
    # raw synthesized metrics (of the primary signal)
    cpu: float
    memory: float
    error_count: int
    error_rate: float          # only meaningful for the canary/faulty-update path
    # the primary signal handed to a response agent (exactly one is set)
    anomaly: Optional[AnomalyAlert] = None
    canary_result: Optional[CanaryTestResult] = None
    # full alert burst for consolidation measurement (>=1 for anomaly scenarios)
    burst: List[AnomalyAlert] = field(default_factory=list)
    seed: int = 0

    @property
    def is_canary(self) -> bool:
        return self.canary_result is not None

    @property
    def has_signal(self) -> bool:
        """Whether the synthesized metrics actually tripped a detection threshold."""
        return self.anomaly is not None or self.canary_result is not None


def synth_anomaly_alert(system_id: str, cpu: float, memory: float,
                        error_count: int) -> Optional[AnomalyAlert]:
    """
    Stateless re-implementation of MonitoringAgent.detect_anomaly
    (agents/monitoring/monitoring_agent.py:139-208), evaluated against fixed
    healthy baselines. Same order of checks (CPU -> errors -> memory), same
    thresholds, same severities/recommendations. Returns None if nothing trips.
    """
    now = datetime.now().timestamp()

    if cpu > BASELINE_CPU * CPU_ANOMALY_RATIO:
        return AnomalyAlert(
            alert_id=f"ALERT-{system_id}-{int(now)}",
            severity="HIGH", system_id=system_id, metric_type="CPU",
            current_value=cpu, expected_value=BASELINE_CPU,
            confidence=0.9, timestamp=now, recommendation="INVESTIGATE_HIGH_CPU",
        )
    if error_count > ERROR_COUNT_LIMIT:
        return AnomalyAlert(
            alert_id=f"ALERT-{system_id}-{int(now)}",
            severity="CRITICAL", system_id=system_id, metric_type="ERRORS",
            current_value=float(error_count), expected_value=0.0,
            confidence=0.95, timestamp=now, recommendation="ROLLBACK_IMMEDIATELY",
        )
    if memory > BASELINE_MEM * MEM_ANOMALY_RATIO:
        return AnomalyAlert(
            alert_id=f"ALERT-{system_id}-{int(now)}",
            severity="MEDIUM", system_id=system_id, metric_type="MEMORY",
            current_value=memory, expected_value=BASELINE_MEM,
            confidence=0.85, timestamp=now, recommendation="INVESTIGATE_MEMORY_LEAK",
        )
    return None


# ---------------------------------------------------------------------------
# Per-scenario metric generators. Each returns (cpu, memory, error_count,
# error_rate) for one trial, given a seeded RNG. Distributions are centered
# firmly in-scenario with modest noise so that a small fraction of trials land
# near a threshold -> produces a realistic, non-degenerate decision spread.
# ---------------------------------------------------------------------------
def _gen_faulty_update(rng: random.Random):
    # Faulty deploy: high canary error rate. CPU/mem nominal (canary path).
    error_rate = rng.uniform(0.02, 0.25)     # well above the 0.01 flag line
    return BASELINE_CPU, BASELINE_MEM, 0, error_rate


def _gen_zone_failure(rng: random.Random):
    # Availability-zone failure: ~33% of nodes go down together; a downed node
    # reads as high CPU / near-failed (mock simulate-failure sets cpu=95).
    cpu = rng.gauss(93.0, 5.0)
    memory = rng.gauss(75.0, 8.0)
    return max(0.0, cpu), max(0.0, memory), 0, 0.0


def _gen_memory_leak(rng: random.Random):
    # Leak: memory climbs (>1.8x -> >72), CPU stays near baseline so the memory
    # branch is actually reachable (CPU is checked first in detect_anomaly).
    cpu = rng.gauss(BASELINE_CPU + 5, 5.0)
    memory = rng.gauss(85.0, 6.0)
    return max(0.0, cpu), max(0.0, memory), 0, 0.0


def _gen_cascading(rng: random.Random):
    # Zone failure: each affected node reads as a high-CPU node (like the mock).
    cpu = rng.gauss(93.0, 5.0)
    memory = rng.gauss(70.0, 8.0)
    return max(0.0, cpu), max(0.0, memory), 0, 0.0


SCENARIO_GENERATORS = {
    "faulty_update": _gen_faulty_update,
    "zone_failure": _gen_zone_failure,
    "memory_leak": _gen_memory_leak,
    "cascading_failure": _gen_cascading,
}

# Multi-system scenarios emit a burst of correlated alerts (used to measure alert
# consolidation). Spec: (n_systems, n_polls, base_server_index).
#  * Zone failure: ~33% of nodes fail simultaneously, consolidated over a 60s
#    window (paper step 2).
#  * Cascading failure: nodes fail progressively at 5s intervals; the monitor
#    re-polls each failed node several times -- that repeated polling, NOT any
#    dedup algorithm, is what produced the paper's ~4.4:1 alert-to-action ratio
#    (184 alerts / 42 actions; orientation finding #6).
BURST_SPEC = {
    "zone_failure": (33, 2, 0),
    "cascading_failure": (10, 4, 40),
}

SCENARIO_ORDER = ["faulty_update", "zone_failure", "memory_leak", "cascading_failure"]

SCENARIO_LABELS = {
    "faulty_update": "S1 Faulty Update",
    "zone_failure": "S2 Zone Failure",
    "memory_leak": "S3 Memory Leak",
    "cascading_failure": "S4 Cascading Failure",
}


def generate_trials(scenario: str, n: int, master_seed: int) -> List[Trial]:
    """
    Produce `n` reproducible trials for a scenario. The RNG is seeded from
    (master_seed, scenario) so each scenario is independent yet fully
    reproducible, and the seed is recorded on every Trial.
    """
    gen = SCENARIO_GENERATORS[scenario]
    scenario_seed = hash((master_seed, scenario)) & 0xFFFFFFFF
    rng = random.Random(scenario_seed)

    trials: List[Trial] = []
    for i in range(n):
        if scenario == "faulty_update":
            cpu, mem, ec, er = gen(rng)
            t = Trial(scenario=scenario, trial_index=i, system_id="canary_deployment",
                      cpu=cpu, memory=mem, error_count=ec, error_rate=er,
                      seed=scenario_seed)
            t.canary_result = CanaryTestResult(
                update_id=f"UPDATE-{i}",
                success=er < CANARY_INVESTIGATE_ER,
                affected_systems=1, error_rate=er, latency_impact=0.0,
                recommendation="ROLLBACK" if er > CANARY_ROLLBACK_ER else "DEPLOY",
                details="synthesized faulty-update trial",
            )
            trials.append(t)

        elif scenario in BURST_SPEC:
            # One incident: n_systems nodes fail, each polled n_polls times ->
            # a burst of correlated CPU alerts across distinct systems.
            n_systems, n_polls, base = BURST_SPEC[scenario]
            burst: List[AnomalyAlert] = []
            primary_cpu = primary_mem = 0.0
            for s in range(n_systems):
                sysid = f"server-{base + s}"
                for _poll in range(n_polls):
                    cpu, mem, ec, er = gen(rng)
                    a = synth_anomaly_alert(sysid, cpu, mem, ec)
                    if a is not None:
                        burst.append(a)
                    if s == 0 and _poll == 0:
                        primary_cpu, primary_mem = cpu, mem
            t = Trial(scenario=scenario, trial_index=i,
                      system_id=f"server-{base}",
                      cpu=primary_cpu, memory=primary_mem, error_count=0,
                      error_rate=0.0, seed=scenario_seed)
            # Primary signal = first alert of the burst (single-alert view the
            # real Response Agent actually sees per message).
            t.anomaly = burst[0] if burst else None
            t.burst = burst
            trials.append(t)

        else:
            cpu, mem, ec, er = gen(rng)
            sysid = f"server-{i % 10}"
            t = Trial(scenario=scenario, trial_index=i, system_id=sysid,
                      cpu=cpu, memory=mem, error_count=ec, error_rate=er,
                      seed=scenario_seed)
            t.anomaly = synth_anomaly_alert(sysid, cpu, mem, ec)
            t.burst = [t.anomaly] if t.anomaly else []
            trials.append(t)

    return trials
