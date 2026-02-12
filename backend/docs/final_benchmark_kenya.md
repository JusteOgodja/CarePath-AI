# Kenya Policy Benchmark

Source: `GEO_node_8891905584`
Speciality: `maternal`
Episodes: `30`

## Composite Ranking

| Rank | Policy | Composite | Avg Reward/Episode | Avg Travel | Avg Wait | Entropy | HHI |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | ppo | 0.6913 | -71.6400 | 17.3750 | 72.1750 | 0.9785 | 0.2134 |
| 2 | random | 1.8000 | -74.2313 | 20.9417 | 71.8475 | 0.9996 | 0.2002 |
| 3 | heuristic | 2.1525 | -73.5900 | 11.0875 | 80.9000 | 0.8844 | 0.2637 |

## Reward-Only Ranking

1. `ppo` (-71.6400)
2. `heuristic` (-73.5900)
3. `random` (-74.2313)

## Recommendation

- Composite winner: **`ppo`**
- Best pure reward: **`ppo`**
- Best equity proxy (highest entropy, lowest HHI): see `random` vs others in table.

## Composite Weights

- reward=1.0, travel=0.8, wait=0.6, hhi=0.5, entropy_gap=0.3, overloads=0.4