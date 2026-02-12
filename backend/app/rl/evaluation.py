from __future__ import annotations

from collections import Counter

from app.rl.env import ReferralEnv
from app.rl.heuristic_policy import choose_action


def evaluate_heuristic(env: ReferralEnv, episodes: int, overload_penalty: float) -> dict:
    total_reward = 0.0
    total_overloads = 0
    destination_counts: Counter[str] = Counter()

    for _ in range(episodes):
        env.reset()
        done = False
        while not done:
            snap = env.snapshot()
            decision = choose_action(
                capacities=[int(v) for v in snap["capacities"]],
                waits=[float(v) for v in snap["waits"]],
                travel_times=[float(v) for v in snap["travel_times"]],
                overload_penalty=overload_penalty,
            )
            _, reward, terminated, truncated, info = env.step(decision.action)
            total_reward += reward
            if info["overload"]:
                total_overloads += 1
            destination_counts[info["destination_id"]] += 1
            done = terminated or truncated

    denom = max(episodes, 1)
    return {
        "avg_reward_per_episode": total_reward / denom,
        "avg_overloads_per_episode": total_overloads / denom,
        "destinations": dict(destination_counts),
    }
