# Kenya Policy Benchmark

Source: `GEO_node_8891905584`
Speciality: `maternal`
Episodes: `30`

## Composite Ranking

| Rank | Policy | Composite | Avg Reward/Episode | Avg Travel | Avg Wait | Entropy | HHI |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | heuristic | 0.4947 | -62.2900 | 20.3250 | 57.5375 | 0.9862 | 0.2097 |
| 2 | random | 1.6000 | -195.4167 | 227.1971 | 17.0738 | 0.9989 | 0.0838 |
| 3 | ppo | 1.6562 | -96.4000 | 19.5000 | 101.0000 | 0.8113 | 0.6250 |

## Reward-Only Ranking

1. `heuristic` (-62.2900)
2. `ppo` (-96.4000)
3. `random` (-195.4167)

## Recommendation

- Composite winner: **`heuristic`**
- Best pure reward: **`heuristic`**
- Best equity proxy (highest entropy, lowest HHI): see `random` vs others in table.

## Composite Weights

- reward=1.0, travel=0.6, wait=0.8, hhi=0.4, entropy_gap=0.2, overloads=0.4