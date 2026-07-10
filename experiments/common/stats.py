"""
Shared statistics helpers for the Sura.ai evaluation experiments.

Kept dependency-light (pure Python + math) so every experiment can import it
without pulling scipy. The Wilson score interval is used throughout instead of
the normal approximation because our per-scenario N (50) is small enough that
the normal approximation misbehaves near p=0 and p=1.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Dict, List

# 95% two-sided z. Kept as a constant so every experiment reports the same CI.
Z_95 = 1.959963984540054


@dataclass
class ProportionResult:
    """A success rate with its Wilson 95% confidence interval."""
    successes: int
    trials: int
    rate: float          # point estimate k/n
    ci_low: float        # Wilson lower bound
    ci_high: float       # Wilson upper bound
    z: float = Z_95

    def as_dict(self) -> Dict:
        return asdict(self)

    def pretty(self) -> str:
        """e.g. '0.860 [0.735, 0.931] (43/50)'"""
        return (
            f"{self.rate:.3f} [{self.ci_low:.3f}, {self.ci_high:.3f}] "
            f"({self.successes}/{self.trials})"
        )


def wilson_interval(successes: int, trials: int, z: float = Z_95) -> ProportionResult:
    """
    Wilson score interval for a binomial proportion.

    Reference: Wilson (1927). Preferred over the normal ('Wald') approximation
    for small N and for rates near 0 or 1, both of which we hit constantly here
    (e.g. a rule that catches 50/50 or 0/50).
    """
    if trials <= 0:
        return ProportionResult(successes=0, trials=0, rate=0.0,
                                ci_low=0.0, ci_high=0.0, z=z)

    p = successes / trials
    z2 = z * z
    denom = 1.0 + z2 / trials
    center = (p + z2 / (2 * trials)) / denom
    half = (z * math.sqrt(p * (1 - p) / trials + z2 / (4 * trials * trials))) / denom
    lo = max(0.0, center - half)
    hi = min(1.0, center + half)
    return ProportionResult(successes=successes, trials=trials, rate=p,
                            ci_low=lo, ci_high=hi, z=z)


def summarize_latencies(values: List[float]) -> Dict[str, float]:
    """
    Distribution summary used by the timing experiment (Exp 2) and reused for
    any numeric metric. Returns mean/median/p90/p99/min/max/n/stdev.
    Percentiles use linear interpolation between order statistics.
    """
    if not values:
        return {k: 0.0 for k in
                ("n", "mean", "median", "p90", "p99", "min", "max", "stdev")}

    s = sorted(values)
    n = len(s)

    def pct(q: float) -> float:
        if n == 1:
            return s[0]
        idx = q * (n - 1)
        lo = int(math.floor(idx))
        hi = int(math.ceil(idx))
        if lo == hi:
            return s[lo]
        frac = idx - lo
        return s[lo] * (1 - frac) + s[hi] * frac

    mean = sum(s) / n
    var = sum((x - mean) ** 2 for x in s) / n if n > 1 else 0.0
    return {
        "n": float(n),
        "mean": mean,
        "median": pct(0.50),
        "p90": pct(0.90),
        "p99": pct(0.99),
        "min": s[0],
        "max": s[-1],
        "stdev": math.sqrt(var),
    }
