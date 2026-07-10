"""
RuleBasedResponseAgent -- the deterministic baseline for Experiment 1.

It receives the *same* AnomalyAlert / CanaryTestResult messages as the real
IntelligentResponseAgent, but replaces the Lava/Claude call with a fixed
decision tree built exclusively from thresholds that already exist in the
codebase (no new numbers). This isolates the contribution of LLM reasoning:
same inputs, same runbook vocabulary, same downstream action -- only the
decision function differs.

Structural note (surfaced as an experiment finding): a per-alert threshold rule
has no access to cross-system context, so it can never emit FAILOVER or ISOLATE
-- those require noticing that *many* systems failed together. That blind spot
is exactly what the cascading-failure scenario is designed to expose.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from agents.messages import AnomalyAlert, CanaryTestResult
from experiments.common.scenarios import (
    CPU_ANOMALY_RATIO, MEM_ANOMALY_RATIO, ERROR_COUNT_LIMIT,
    CANARY_ROLLBACK_ER, CANARY_INVESTIGATE_ER,
)


@dataclass
class RuleDecision:
    action: str            # one of ACTION_VOCAB, or "NONE" if no action taken
    reason: str            # human-readable rule that fired
    used_ai: bool = False  # always False here; kept for schema parity with LLM records


class RuleBasedResponseAgent:
    """
    Deterministic decision tree. Every branch cites the live threshold it mirrors.
    `dedup_window` optionally suppresses repeat actions on a system already being
    remediated within the same scenario burst (used to measure alert
    consolidation the way the paper reports it).
    """

    def __init__(self, enable_dedup: bool = True):
        self.enable_dedup = enable_dedup
        self._active_systems: Dict[str, str] = {}  # system_id -> action in flight

    # -- reset between scenarios so dedup state never leaks across scenarios ----
    def reset(self) -> None:
        self._active_systems.clear()

    # -- anomaly path (mirrors handle_anomaly in the real agent) ---------------
    def decide_anomaly(self, alert: AnomalyAlert) -> RuleDecision:
        # Real agent only engages on MEDIUM/HIGH/CRITICAL (intelligent_response_agent.py:88)
        if alert.severity not in ("MEDIUM", "HIGH", "CRITICAL"):
            return RuleDecision("NONE", f"severity {alert.severity} below action floor")

        ratio = alert.current_value / alert.expected_value if alert.expected_value else 0.0
        mtype = alert.metric_type.upper()

        # Order matches detect_anomaly's own precedence.
        if mtype == "ERRORS" or alert.severity == "CRITICAL":
            action, reason = "ROLLBACK", f"error/critical signal (limit>{ERROR_COUNT_LIMIT})"
        elif mtype == "CPU" and ratio > CPU_ANOMALY_RATIO:
            action, reason = "SCALE_UP", f"CPU {ratio:.1f}x baseline (>{CPU_ANOMALY_RATIO}x)"
        elif mtype == "MEMORY" and ratio > MEM_ANOMALY_RATIO:
            action, reason = "RESTART", f"memory {ratio:.1f}x baseline (>{MEM_ANOMALY_RATIO}x)"
        else:
            action, reason = "INVESTIGATE", "signal below actionable thresholds"

        return self._apply_dedup(alert.system_id, action, reason)

    # -- canary path (mirrors handle_canary_result in the real agent) ----------
    def decide_canary(self, result: CanaryTestResult) -> RuleDecision:
        er = result.error_rate
        if er > CANARY_ROLLBACK_ER:
            return RuleDecision("ROLLBACK", f"error_rate {er:.3f} > {CANARY_ROLLBACK_ER}")
        if er > CANARY_INVESTIGATE_ER:
            return RuleDecision("INVESTIGATE", f"error_rate {er:.3f} > {CANARY_INVESTIGATE_ER}")
        return RuleDecision("DEPLOY", f"error_rate {er:.3f} <= {CANARY_INVESTIGATE_ER}")

    # -- dedup: one in-flight action per system --------------------------------
    def _apply_dedup(self, system_id: str, action: str, reason: str) -> RuleDecision:
        if self.enable_dedup and system_id in self._active_systems:
            return RuleDecision("NONE",
                                f"deduplicated: {system_id} already actioned "
                                f"({self._active_systems[system_id]})")
        if action != "NONE":
            self._active_systems[system_id] = action
        return RuleDecision(action, reason)
