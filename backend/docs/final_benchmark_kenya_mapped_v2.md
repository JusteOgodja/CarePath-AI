# Kenya Policy Benchmark

Source: `GEO_node_8891905584`
Speciality: `maternal`
Episodes: `40`

## Composite Ranking

| Rank | Policy | Composite | Avg Reward/Episode | Avg Travel | Avg Wait | Entropy | HHI |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | ppo | 1.2595 | -67.5177 | 22.0875 | 54.2750 | 0.9907 | 0.2059 |
| 2 | heuristic | 1.4269 | -70.0279 | 20.3250 | 57.5375 | 0.9862 | 0.2097 |
| 3 | random | 1.6000 | -160.7062 | 223.6413 | 17.7597 | 0.9994 | 0.0836 |

## Reward-Only Ranking

1. `ppo` (-67.5177)
2. `heuristic` (-70.0279)
3. `random` (-160.7062)

## Recommendation

- Composite winner: **`ppo`**
- Best pure reward: **`ppo`**
- Best equity proxy (highest entropy, lowest HHI): see `random` vs others in table.

## Composite Weights

- reward=1.0, travel=0.6, wait=0.8, hhi=0.4, entropy_gap=0.2, overloads=0.4