from __future__ import annotations

import math
import random
from collections import Counter
from typing import Callable

from stable_baselines3 import PPO

from app.rl.env import ReferralEnv
from app.rl.heuristic_policy import choose_action
from app.rl.random_policy import choose_random_action


def _normalized_entropy(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total == 0 or len(counts) <= 1:
        return 0.0
    probs = [count / total for count in counts.values()]
    entropy = -sum(p * math.log(p) for p in probs)
    return entropy / math.log(len(counts))


def _hhi(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return sum((count / total) ** 2 for count in counts.values())


def _evaluate_policy(
    env: ReferralEnv,
    *,
    episodes: int,
    action_fn: Callable[[dict], int],
    seed_base: int,
) -> dict:
    total_reward = 0.0
    total_overloads = 0
    total_travel = 0.0
    total_wait = 0.0
    total_steps = 0
    destination_counts: Counter[str] = Counter()

    for episode in range(episodes):
        obs, _ = env.reset(seed=seed_base + episode)
        done = False
        while not done:
            snap = env.snapshot()
            action = action_fn({"obs": obs, "snapshot": snap})
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += float(reward)
            total_travel += float(info["travel_minutes"])
            total_wait += float(info["wait_minutes"])
            total_steps += 1
            if info["overload"]:
                total_overloads += 1
            destination_counts[info["destination_id"]] += 1
            done = terminated or truncated

    episode_denom = max(episodes, 1)
    step_denom = max(total_steps, 1)
    overload_rate = total_overloads / step_denom

    return {
        "avg_reward_per_episode": total_reward / episode_denom,
        "avg_overloads_per_episode": total_overloads / episode_denom,
        "avg_travel": total_travel / step_denom,
        "avg_wait": total_wait / step_denom,
        "failure_rate": 0.0,
        "fallback_rate": overload_rate,
        "entropy_norm": _normalized_entropy(destination_counts),
        "hhi": _hhi(destination_counts),
        "destination_distribution": dict(destination_counts),
    }


def evaluate_heuristic(env: ReferralEnv, episodes: int, overload_penalty: float, seed_base: int = 1000) -> dict:
    def action_fn(data: dict) -> int:
        snap = data["snapshot"]
        decision = choose_action(
            capacities=[int(v) for v in snap["capacities"]],
            waits=[float(v) for v in snap["waits"]],
            travel_times=[float(v) for v in snap["travel_times"]],
            overload_penalty=overload_penalty,
        )
        return int(decision.action)

    return _evaluate_policy(env, episodes=episodes, action_fn=action_fn, seed_base=seed_base)


def evaluate_random(env: ReferralEnv, episodes: int, seed_base: int = 1000) -> dict:
    rng = random.Random(seed_base)

    def action_fn(data: dict) -> int:
        snap = data["snapshot"]
        return choose_random_action([int(v) for v in snap["capacities"]], rng)

    return _evaluate_policy(env, episodes=episodes, action_fn=action_fn, seed_base=seed_base)


def evaluate_ppo(model: PPO, env: ReferralEnv, episodes: int, seed_base: int = 1000) -> dict:
    def action_fn(data: dict) -> int:
        action, _ = model.predict(data["obs"], deterministic=True)
        return int(action)

    return _evaluate_policy(env, episodes=episodes, action_fn=action_fn, seed_base=seed_base)

