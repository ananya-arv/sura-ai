"""
Prompt variants for Experiment 5.

Control = the production single-shot prompt (LavaAIService._build_incident_prompt).
CoT     = a chain-of-thought variant that forces explicit step-by-step reasoning
          before the recommendation, structured like the paper's example
          ("Step 1: CPU usage is 3.2x baseline. Step 2: ... Recommendation: RESTART"),
          returned as JSON with a `reasoning_steps` array so the chain is
          machine-scoreable.
"""
from __future__ import annotations

from typing import Dict


def control_prompt(service, incident: Dict) -> str:
    """The exact production prompt (reused, not reimplemented)."""
    return service._build_incident_prompt(incident)


def cot_prompt(incident: Dict) -> str:
    return f"""Analyze this production incident. Think step by step BEFORE deciding.

Incident Data:
- Alert ID: {incident.get('alert_id')}
- Severity: {incident.get('severity')}
- System: {incident.get('system_id')}
- Metric: {incident.get('metric_type')}
- Current Value: {incident.get('current_value')}
- Expected Value: {incident.get('expected_value')}
- Confidence: {incident.get('confidence', 0):.2f}

Reason explicitly, e.g. "Step 1: CPU usage is 3.2x baseline. Step 2: sustained
high CPU with no traffic spike indicates a runaway process. Step 3: restarting
clears the process. Recommendation: RESTART".

Respond with ONLY this JSON (no markdown, no code fences):
{{
    "reasoning_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
    "root_cause": "brief diagnosis",
    "recommendation": "ROLLBACK",
    "confidence": 0.85,
    "reasoning": "one-sentence justification linking metrics to the action"
}}

Choose recommendation from: ROLLBACK, FAILOVER, SCALE_UP, ISOLATE, INVESTIGATE, RESTART"""


# Diagnosis / metric / action vocabulary for the automatic explainability rubric.
_METRIC_TERMS = ("baseline", "ratio", "%", "cpu", "memory", "error rate",
                 "threshold", "usage", "exceed", "x normal", "x baseline")
_DIAGNOSIS_TERMS = ("leak", "spike", "overload", "exhaust", "saturat", "failure",
                    "cascade", "zone", "runaway", "contention", "degrad", "outage")
_ACTION_TERMS = ("restart", "rollback", "failover", "isolate", "scale", "deploy",
                 "investigate", "reboot", "revert")


def explainability_score(recommendation: str, reasoning: str,
                         reasoning_steps) -> int:
    """
    0-2 rubric, computed automatically:
      2 = traceable chain: observed metric -> intermediate diagnosis -> action
      1 = partial (metric OR diagnosis present)
      0 = bare assertion, no reasoning
    """
    text = (reasoning or "")
    if reasoning_steps:
        text = text + " " + " ".join(str(s) for s in reasoning_steps)
    t = text.lower()
    metric = any(term in t for term in _METRIC_TERMS)
    diagnosis = any(term in t for term in _DIAGNOSIS_TERMS)
    action = any(term in t for term in _ACTION_TERMS) or bool(recommendation)
    multi_step = bool(reasoning_steps) and len(reasoning_steps) >= 2

    if metric and diagnosis and (action or multi_step):
        return 2
    if metric or diagnosis:
        return 1
    return 0
