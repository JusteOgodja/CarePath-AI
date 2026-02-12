# Kenya Policy Benchmark

Source: `GEO_node_8891905584`
Speciality: `maternal`
Episodes: `40`

## Composite Ranking

| Rank | Policy | Composite | Avg Reward/Episode | Avg Travel | Avg Wait | Entropy | HHI |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | ppo | 1.2474 | -63.7542 | 21.3375 | 54.9750 | 0.9921 | 0.2050 |
| 2 | heuristic | 1.4102 | -65.2539 | 20.3250 | 57.5375 | 0.9862 | 0.2097 |
| 3 | random | 1.6000 | -211.4069 | 223.6413 | 17.7597 | 0.9994 | 0.0836 |

## Reward-Only Ranking

1. `ppo` (-63.7542)
2. `heuristic` (-65.2539)
3. `random` (-211.4069)

## Recommendation

- Composite winner: **`ppo`**
- Best pure reward: **`ppo`**
- Best equity proxy (highest entropy, lowest HHI): see `random` vs others in table.

## Composite Weights

- reward=1.0, travel=0.6, wait=0.8, hhi=0.4, entropy_gap=0.2, overloads=0.4