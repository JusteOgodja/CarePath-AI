# Kenya Policy Benchmark

Source: `GEO_node_8891905584`
Speciality: `maternal`
Episodes: `5`

## Composite Ranking

| Rank | Policy | Composite | Avg Reward/Episode | Avg Travel | Avg Wait | Entropy | HHI |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | ppo | 1.1792 | -61.0500 | 21.3375 | 54.9750 | 0.9921 | 0.2050 |
| 2 | heuristic | 1.4096 | -62.2900 | 20.3250 | 57.5375 | 0.9862 | 0.2097 |
| 3 | random | 1.6000 | -190.6340 | 220.1750 | 18.1175 | 0.9937 | 0.0860 |

## Reward-Only Ranking

1. `ppo` (-61.0500)
2. `heuristic` (-62.2900)
3. `random` (-190.6340)

## Recommendation

- Composite winner: **`ppo`**
- Best pure reward: **`ppo`**
- Best equity proxy (highest entropy, lowest HHI): see `random` vs others in table.

## Composite Weights

- reward=1.0, travel=0.6, wait=0.8, hhi=0.4, entropy_gap=0.2, overloads=0.4