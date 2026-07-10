"""
Steady-state false-positive harness for Experiment 3.

The original paper never measured how often the system fires WITHOUT a real
incident. We run the Monitoring Agent's REAL stateful detector
(`MonitoringAgent.detect_anomaly`, with its per-system learned baseline + EMA)
against a healthy metric stream for an extended, accelerated-time simulation
with ZERO injected failures, and count:

  * false-positive alerts (detector fires on healthy noise)
  * how many escalate to a Response action attempt (all of them -- there is no
    confidence/consolidation gate, orientation finding #1)
  * how many the LLM would actually remediate vs correctly abstain
    (the LLM is the only thing that could catch a false alarm)
  * false-positive rate per hour of operation

Modeling note: against the committed mock, healthy metrics are constant, so the
detector never fires and FP rate is trivially 0 -- not informative. The FP
driver in any real deployment is *benign transient load spikes* (a cron job, a
GC pause) that a naive `cpu > 2x baseline` rule flags but a good monitor should
not. We model those explicitly; the FP rate is sensitive to that model, so all
noise parameters are recorded in the output.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional

NON_ACTIONS = {"NONE", "INVESTIGATE"}


def make_monitor():
    """A MonitoringAgent shell with a live baseline dict but no uAgent/network.

    detect_anomaly only touches self.baseline_metrics, so an uninitialized
    instance runs the real detection logic faithfully.
    """
    from agents.monitoring.monitoring_agent import MonitoringAgent, SystemMetrics
    mon = MonitoringAgent.__new__(MonitoringAgent)
    mon.baseline_metrics = {}
    return mon, SystemMetrics


async def run_steady_state(
    n_systems: int,
    cycles: int,
    interval_s: int,
    cpu_sigma: float,
    mem_sigma: float,
    transient_prob: float,
    transient_mult_range,
    seed: int,
    llm,
) -> Dict:
    """Run the accelerated steady-state simulation. Returns a result dict."""
    mon, SystemMetrics = make_monitor()
    rng = random.Random(hash((seed, "steady_state")) & 0xFFFFFFFF)

    # Per-system healthy means (mirrors the mock's init ranges).
    means = {
        f"server-{i}": (rng.uniform(20, 40), rng.uniform(30, 50))
        for i in range(n_systems)
    }

    fps: List[Dict] = []
    total_polls = 0
    transient_count = 0

    for c in range(cycles):
        for sysid, (cpu_mean, mem_mean) in means.items():
            total_polls += 1
            cpu = rng.gauss(cpu_mean, cpu_sigma)
            mem = rng.gauss(mem_mean, mem_sigma)
            is_transient = rng.random() < transient_prob
            if is_transient:
                transient_count += 1
                # benign spike above the 2x line on CPU (a real cron/GC blip)
                cpu = cpu_mean * rng.uniform(*transient_mult_range)

            metrics = SystemMetrics(
                system_id=sysid, cpu_usage=max(0.0, cpu),
                memory_usage=max(0.0, mem), disk_usage=50.0,
                network_latency=20.0, error_count=0, timestamp=c * interval_s,
            )
            alert = await mon.detect_anomaly(sysid, metrics)
            if alert is None:
                continue

            # A false positive: no failure was injected anywhere.
            rec = {
                "cycle": c, "sim_time_s": c * interval_s, "system_id": sysid,
                "metric_type": alert.metric_type, "severity": alert.severity,
                "current_value": round(alert.current_value, 2),
                "expected_value": round(alert.expected_value, 2),
                "was_transient": is_transient,
                # No confidence gate -> this alert WILL reach the Response agent.
                "escalated_to_response": True,
                "llm_action": None, "llm_would_remediate": None,
            }
            if llm is not None and llm.available:
                res = await llm.analyze_incident({
                    "alert_id": alert.alert_id, "severity": alert.severity,
                    "system_id": alert.system_id, "metric_type": alert.metric_type,
                    "current_value": alert.current_value,
                    "expected_value": alert.expected_value,
                    "confidence": alert.confidence,
                })
                action = res.get("recommendation", "INVESTIGATE")
                rec["llm_action"] = action
                rec["llm_would_remediate"] = action not in NON_ACTIONS
            fps.append(rec)

    sim_seconds = cycles * interval_s
    hours = sim_seconds / 3600.0
    fp_count = len(fps)
    llm_remediated = sum(1 for f in fps if f.get("llm_would_remediate"))
    llm_caught = sum(1 for f in fps if f.get("llm_would_remediate") is False)

    return {
        "params": {
            "n_systems": n_systems, "cycles": cycles, "interval_s": interval_s,
            "sim_seconds": sim_seconds, "sim_minutes": round(sim_seconds / 60, 1),
            "cpu_sigma": cpu_sigma, "mem_sigma": mem_sigma,
            "transient_prob": transient_prob,
            "transient_mult_range": list(transient_mult_range),
            "seed": seed,
        },
        "totals": {
            "total_polls": total_polls,
            "transients_injected": transient_count,
            "false_positive_alerts": fp_count,
            "escalated_to_response": fp_count,  # no gate -> all escalate
            "llm_false_remediations": llm_remediated,
            "llm_correctly_abstained": llm_caught,
        },
        "rates": {
            "fp_alerts_per_hour": fp_count / hours if hours else 0.0,
            "false_remediations_per_hour": llm_remediated / hours if hours else 0.0,
            "fp_per_1000_polls": (fp_count / total_polls * 1000) if total_polls else 0.0,
        },
        "events": fps,
    }
