# Kenya Policy Benchmark

Source: `GEO_node_8891905584`
Speciality: `maternal`
Episodes: `3`

## Composite Ranking

| Rank | Policy | Composite | Avg Reward/Episode | Avg Travel | Avg Wait | Entropy | HHI |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | ppo | 1.0854 | -61.5500 | 20.9500 | 55.9875 | 0.9882 | 0.2072 |
| 2 | heuristic | 1.4431 | -67.4500 | 19.6500 | 64.6625 | 0.9779 | 0.2159 |
| 3 | random | 1.6000 | -198.5600 | 229.0792 | 19.1208 | 0.9928 | 0.0863 |

## Reward-Only Ranking

1. `ppo` (-61.5500)
2. `heuristic` (-67.4500)
3. `random` (-198.5600)

## Recommendation

- Composite winner: **`ppo`**
- Best pure reward: **`ppo`**
- Best equity proxy (highest entropy, lowest HHI): see `random` vs others in table.

## Composite Weights

- reward=1.0, travel=0.6, wait=0.8, hhi=0.4, entropy_gap=0.2, overloads=0.4