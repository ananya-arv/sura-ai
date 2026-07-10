# Experiment 4 - Expanded Canary Testing

- 10 trials/case × 5 cases = 50 total, seed `42`, model `claude-sonnet-4-6`

## Decision by case type (block = ROLLBACK or INVESTIGATE)

| Case | error-rate band | LLM block-rate | LLM rollback | LLM mean conf | Rule block-rate |
|---|---|--:|--:|--:|--:|
| clean | 0.000–0.005 | 0.60 | 0.00 | 0.78 | 0.00 |
| borderline | 0.005–0.010 | 1.00 | 0.00 | 0.74 | 0.00 |
| faulty_mild | 0.011–0.030 | 1.00 | 0.30 | 0.84 | 1.00 |
| faulty_moderate | 0.030–0.080 | 1.00 | 1.00 | 0.93 | 1.00 |
| faulty_severe | 0.150–0.300 | 1.00 | 1.00 | 0.97 | 1.00 |

## Headline rates (95% Wilson CI)

| Agent | Prevention rate (faulty→blocked) | False-rollback rate (clean→blocked) |
|---|---|---|
| rule | 1.000 [0.886, 1.000] (30/30) | 0.000 [0.000, 0.278] (0/10) |
| llm | 1.000 [0.886, 1.000] (30/30) | 0.600 [0.313, 0.832] (6/10) |

## Empirical LLM decision boundary

- Stated canary threshold: **error rate 0.01**
- Highest error rate the LLM still DEPLOYED: **0.0027438661080822803**
- Lowest error rate the LLM BLOCKED: **0.00025308155754520336**

See `boundary.png` for the DEPLOY/BLOCK decision vs error rate (LLM & rule).
