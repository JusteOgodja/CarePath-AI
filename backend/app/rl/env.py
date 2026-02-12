from __future__ import annotations

from dataclasses import dataclass

import gymnasium as gym
import networkx as nx
import numpy as np
from gymnasium import spaces

from app.services.graph_service import GraphService


@dataclass(frozen=True)
class DestinationState:
    node_id: str
    travel_minutes: float
    initial_capacity: int
    initial_wait: float


class ReferralEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        *,
        source_id: str,
        speciality: str,
        patients_per_episode: int = 80,
        wait_increment: int = 3,
        recovery_interval: int = 5,
        recovery_amount: int = 2,
        overload_penalty: float = 30.0,
        reward_scale: float = 100.0,
    ) -> None:
        super().__init__()
        self.source_id = source_id
        self.speciality = speciality
        self.patients_per_episode = patients_per_episode
        self.wait_increment = wait_increment
        self.recovery_interval = recovery_interval
        self.recovery_amount = recovery_amount
        self.overload_penalty = overload_penalty
        self.reward_scale = reward_scale

        self.graph_service = GraphService()
        self.destinations: list[DestinationState] = []
        self._load_destinations()

        n_dest = len(self.destinations)
        if n_dest == 0:
            raise ValueError("No reachable destination for configured source/speciality")

        # Obs: [capacities..., waits..., travel_times..., step_ratio]
        obs_size = (3 * n_dest) + 1
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(obs_size,), dtype=np.float32)
        self.action_space = spaces.Discrete(n_dest)

        self.capacities: list[int] = []
        self.waits: list[float] = []
        self.travel_times: list[float] = [d.travel_minutes for d in self.destinations]
        self.initial_capacities: list[int] = [d.initial_capacity for d in self.destinations]

        self.current_step = 0

    def _load_destinations(self) -> None:
        self.graph_service.reload()
        candidates = self.graph_service.candidate_destinations(self.speciality)
        destinations: list[DestinationState] = []

        for node_id in candidates:
            if node_id == self.source_id:
                continue
            try:
                _, travel = self.graph_service.shortest_path(self.source_id, node_id)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

            attrs = self.graph_service.node(node_id)
            destinations.append(
                DestinationState(
                    node_id=node_id,
                    travel_minutes=float(travel),
                    initial_capacity=int(attrs["capacity_available"]),
                    initial_wait=float(attrs["estimated_wait_minutes"]),
                )
            )

        self.destinations = destinations

    def _get_obs(self) -> np.ndarray:
        max_capacity = max(max(self.initial_capacities), 1)
        max_wait = max(max(self.waits) if self.waits else 1.0, 1.0)
        max_travel = max(max(self.travel_times) if self.travel_times else 1.0, 1.0)

        cap_part = [cap / max_capacity for cap in self.capacities]
        wait_part = [w / max_wait for w in self.waits]
        travel_part = [t / max_travel for t in self.travel_times]
        step_ratio = [self.current_step / max(self.patients_per_episode, 1)]

        return np.array(cap_part + wait_part + travel_part + step_ratio, dtype=np.float32)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self.current_step = 0
        self.capacities = [d.initial_capacity for d in self.destinations]
        self.waits = [d.initial_wait for d in self.destinations]
        return self._get_obs(), {}

    def _apply_recovery(self) -> None:
        if self.recovery_interval <= 0 or self.recovery_amount <= 0:
            return
        if self.current_step <= 0 or self.current_step % self.recovery_interval != 0:
            return

        for idx, max_cap in enumerate(self.initial_capacities):
            self.capacities[idx] = min(max_cap, self.capacities[idx] + self.recovery_amount)
            self.waits[idx] = max(0.0, self.waits[idx] - (2.0 * self.recovery_amount))

    def step(self, action: int):
        action_idx = int(action)
        if action_idx < 0 or action_idx >= len(self.destinations):
            raise ValueError("Invalid action index")

        travel = self.travel_times[action_idx]
        wait = self.waits[action_idx]
        cap = self.capacities[action_idx]

        overload = cap <= 0
        reward = -((travel + wait) / self.reward_scale)
        if overload:
            reward -= self.overload_penalty / self.reward_scale
        else:
            self.capacities[action_idx] -= 1

        self.waits[action_idx] += self.wait_increment

        self.current_step += 1
        self._apply_recovery()

        terminated = self.current_step >= self.patients_per_episode
        truncated = False

        info = {
            "destination_id": self.destinations[action_idx].node_id,
            "travel_minutes": travel,
            "wait_minutes": wait,
            "overload": overload,
        }

        return self._get_obs(), float(reward), terminated, truncated, info

    def destination_ids(self) -> list[str]:
        return [d.node_id for d in self.destinations]

    def snapshot(self) -> dict[str, list[float | int]]:
        return {
            "capacities": list(self.capacities),
            "waits": list(self.waits),
            "travel_times": list(self.travel_times),
        }
