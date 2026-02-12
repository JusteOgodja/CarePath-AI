# CarePath Scenario Summary

Patients per scenario: **120**

## Ranking

| Rank | Scenario | Composite | Avg Score | Avg Wait | Avg Travel | Fallbacks | Failures | HHI | Entropy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | complex_maternal_stable | 9.68 | 9.68 | 33.52 | 30.10 | 0 | 0 | 0.2524 | 0.9966 |
| 2 | complex_pediatric_shock | 11.09 | 11.09 | 42.57 | 30.12 | 0 | 0 | 0.2512 | 0.9982 |
| 3 | demo_maternal_stable | 121.63 | 91.63 | 83.23 | 36.33 | 18 | 0 | 0.5022 | 0.9968 |
| 4 | demo_maternal_shock | 172.86 | 124.53 | 107.39 | 39.54 | 29 | 0 | 0.5068 | 0.9902 |

## Recommendation

- Recommended primary setup: `complex_maternal_stable` (lowest composite score `9.68`).
- Keep `demo_maternal_shock` as stress-test baseline.
- Use scenarios with shocks for resilience validation before clinical demo.
- Best setup requires no fallback usage in this benchmark window.

## Scoring Weights

- composite = 1.0*avg_score + 2.0*100*fallback_rate + 5.0*100*failure_rate