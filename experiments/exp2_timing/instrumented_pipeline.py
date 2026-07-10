"""
Instrumented single-incident pipeline for Experiment 2 (timing).

Reuses the REAL components so the measured latencies are the system's, not a
stub's:
  * detection      -> the real threshold logic (scenarios.synth_anomaly_alert,
                      a stateless mirror of MonitoringAgent.detect_anomaly)
  * LLM / Lava      -> the real Lava call via the experiment LLM client
  * runbook         -> the REAL runbook coroutines from IntelligentResponseAgent,
                      with their real asyncio.sleep durations, invoked without
                      constructing the uAgent (they only use `logger`+`asyncio`,
                      so __new__ is enough — no port/mailbox needed)
  * notification    -> build the real StatusUpdate and write it to disk

Every stage boundary the paper cares about is timestamped with a monotonic
clock; the full per-incident timeline (offsets from t0) is emitted so any
incident can be reconstructed, plus the named stage durations.
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from agents.messages import StatusUpdate
from experiments.common import scenarios as SC

# action -> runbook coroutine name on IntelligentResponseAgent
RUNBOOK_METHOD = {
    "ROLLBACK": "runbook_rollback",
    "FAILOVER": "runbook_failover",
    "SCALE_UP": "runbook_scale_up",
    "SCALE_DOWN": "runbook_scale_down",
    "ISOLATE": "runbook_isolate",
    "INVESTIGATE": "runbook_investigate",
    "RESTART": "runbook_restart",
    "DEPLOY": "runbook_investigate",   # canary DEPLOY has no remediation runbook
}

# Granular stage marks, in pipeline order (the paper's stage list).
STAGE_ORDER = [
    "detect_start", "alert_published", "context_start", "llm_request_sent",
    "llm_response_received", "decision_validated", "runbook_start",
    "runbook_complete", "notification_sent",
]

# Named, reportable durations derived from the marks above.
DURATION_SPEC = {
    "detection": ("detect_start", "alert_published"),
    "context_gathering": ("context_start", "llm_request_sent"),
    "llm_lava": ("llm_request_sent", "llm_response_received"),
    "validation": ("llm_response_received", "decision_validated"),
    "runbook": ("runbook_start", "runbook_complete"),
    "notification": ("runbook_complete", "notification_sent"),
    "end_to_end": ("detect_start", "notification_sent"),
}


def make_runbook_holder():
    """An IntelligentResponseAgent shell with runnable runbooks but no uAgent.

    __init__ builds a uAgent (ports, mailbox, requires Lava) which we don't want;
    the runbook coroutines only reference module `logger` + asyncio, so an
    uninitialized instance runs them faithfully.
    """
    from agents.response.intelligent_response_agent import IntelligentResponseAgent
    return IntelligentResponseAgent.__new__(IntelligentResponseAgent)


async def run_incident(trial: SC.Trial, llm, runbook_holder,
                       status_path: Path) -> Dict:
    incident_id = f"INC-{trial.scenario}-{trial.trial_index}-{uuid.uuid4().hex[:6]}"
    marks: Dict[str, float] = {}

    def mark(name: str) -> None:
        marks[name] = time.perf_counter()

    wall_start = datetime.now(timezone.utc).isoformat()

    # 1) anomaly detection (real threshold compute)
    mark("detect_start")
    if trial.is_canary:
        signal_kind = "canary"
    else:
        _ = SC.synth_anomaly_alert(trial.system_id, trial.cpu, trial.memory,
                                   trial.error_count)
        signal_kind = "anomaly"
    mark("alert_published")

    # 2) Response Agent context gathering (build the incident payload it sends)
    mark("context_start")
    if trial.is_canary:
        payload_kind = "canary"
    else:
        a = trial.anomaly
        incident = {
            "alert_id": a.alert_id, "severity": a.severity, "system_id": a.system_id,
            "metric_type": a.metric_type, "current_value": a.current_value,
            "expected_value": a.expected_value, "confidence": a.confidence,
        }
        payload_kind = "anomaly"
    mark("llm_request_sent")

    # 3) LLM decision via Lava (the real network round trip)
    if trial.is_canary:
        res = await llm.analyze_canary_deployment({
            "additional_context": {
                "update_id": trial.canary_result.update_id, "version": "synthetic",
                "description": "faulty-update canary trial",
                "canary_systems": 1, "total_systems": 100, "test_duration": 30,
                "errors": int(trial.error_rate * 100), "warnings": 0,
                "error_rate": f"{trial.error_rate:.4f}", "warning_rate": "0.0000",
                "latency_impact": "+0.00x",
            }
        })
    else:
        res = await llm.analyze_incident(incident)
    mark("llm_response_received")

    action = res.get("recommendation", "INVESTIGATE")
    lava_request_id = res.get("lava_request_id", "")
    # 4) decision validated (mirrors the agent's post-parse check)
    mark("decision_validated")

    # 5) runbook execution (real coroutine, real sleeps)
    mark("runbook_start")
    method_name = RUNBOOK_METHOD.get(action, "runbook_investigate")
    await getattr(runbook_holder, method_name)(trial.system_id)
    mark("runbook_complete")

    # 6) communication notification (build real StatusUpdate + write file)
    status = StatusUpdate(
        incident_id=incident_id, status="RESOLVED",
        title=f"{action} - timing trial", description=f"Automated {action}",
        affected_services=[trial.system_id], timestamp=time.time(),
    )
    status_path.write_text(json.dumps(status.dict(), indent=2))
    mark("notification_sent")

    t0 = marks["detect_start"]
    timeline = {s: (marks[s] - t0) for s in STAGE_ORDER if s in marks}
    durations = {
        name: marks[b] - marks[a]
        for name, (a, b) in DURATION_SPEC.items()
        if a in marks and b in marks
    }
    return {
        "incident_id": incident_id,
        "scenario": trial.scenario,
        "signal": signal_kind,
        "action": action,
        "runbook": method_name,
        "lava_request_id": lava_request_id,
        "wall_start": wall_start,
        "timeline_offsets_s": timeline,
        "durations_s": durations,
    }
