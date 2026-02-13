from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx

from app.core.config import get_recommendation_policy_default, get_rl_model_path
from app.services.graph_service import GraphService
from app.services.schemas import PathStep, RecommandationRequest, RecommandationResponse, ScoreBreakdown


SEVERITY_WEIGHTS = {
    "low": 1.0,
    "medium": 1.3,
    "high": 1.7,
}


def compute_final_score(*, travel_minutes: float, wait_minutes: float, capacity: int, severity: str) -> float:
    severity_weight = SEVERITY_WEIGHTS[severity]
    capacity_factor = max(capacity, 1)
    return severity_weight * (travel_minutes + wait_minutes) / capacity_factor


@dataclass
class CandidateScore:
    node_id: str
    path: list[str]
    travel_minutes: float
    wait_minutes: float
    capacity: int
    severity: str

    @property
    def score(self) -> float:
        # Lower is better: severity-weighted (travel + wait) adjusted by available capacity.
        return compute_final_score(
            travel_minutes=self.travel_minutes,
            wait_minutes=self.wait_minutes,
            capacity=self.capacity,
            severity=self.severity,
        )

    @property
    def capacity_factor_used(self) -> float:
        return float(max(self.capacity, 1))

    @property
    def raw_cost(self) -> float:
        return self.travel_minutes + self.wait_minutes

    @property
    def severity_weight(self) -> float:
        return SEVERITY_WEIGHTS[self.severity]


class Recommender:
    def __init__(self) -> None:
        self.graph_service = GraphService()
        self._rl_model: Any = None
        self._rl_model_path: str | None = None

    def _build_scored_candidates(self, payload: RecommandationRequest) -> list[CandidateScore]:
        candidates = self.graph_service.candidate_destinations(payload.needed_speciality)
        if not candidates:
            raise ValueError("No available destination for requested speciality")

        non_self_candidates = [node_id for node_id in candidates if node_id != payload.current_centre_id]
        if not non_self_candidates:
            raise ValueError("No available destination other than current centre")

        scored: list[CandidateScore] = []
        for node_id in non_self_candidates:
            try:
                path, travel = self.graph_service.shortest_path(payload.current_centre_id, node_id)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

            attrs = self.graph_service.node(node_id)
            scored.append(
                CandidateScore(
                    node_id=node_id,
                    path=path,
                    travel_minutes=travel,
                    wait_minutes=float(attrs["estimated_wait_minutes"]),
                    capacity=int(attrs["capacity_available"]),
                    severity=payload.severity,
                )
            )
        return scored

    def _heuristic_best(self, scored: list[CandidateScore]) -> CandidateScore:
        if not scored:
            raise ValueError("No reachable destination found from current centre")
        return min(scored, key=lambda c: c.score)

    def _load_rl_model(self):
        model_path = get_rl_model_path()
        if self._rl_model is not None and self._rl_model_path == model_path:
            return self._rl_model

        path = Path(model_path)
        if not path.exists():
            raise RuntimeError(f"RL model not found: {path}")

        try:
            from stable_baselines3 import PPO
        except Exception as exc:  # pragma: no cover - depends on optional deps
            raise RuntimeError("stable-baselines3 is not installed") from exc

        self._rl_model = PPO.load(str(path))
        self._rl_model_path = model_path
        return self._rl_model

    def _rl_best(self, scored: list[CandidateScore]) -> CandidateScore:
        if not scored:
            raise ValueError("No reachable destination found from current centre")

        try:
            import numpy as np
        except Exception as exc:  # pragma: no cover - depends on optional deps
            raise RuntimeError("numpy is not installed") from exc

        model = self._load_rl_model()
        capacities = [max(c.capacity, 1) for c in scored]
        waits = [c.wait_minutes for c in scored]
        travels = [c.travel_minutes for c in scored]

        max_capacity = max(capacities) if capacities else 1
        max_wait = max(waits) if waits else 1.0
        max_travel = max(travels) if travels else 1.0

        obs = np.array(
            [
                *[cap / max(max_capacity, 1) for cap in capacities],
                *[w / max(max_wait, 1.0) for w in waits],
                *[t / max(max_travel, 1.0) for t in travels],
                0.0,  # step_ratio at inference time
            ],
            dtype=np.float32,
        )

        action, _ = model.predict(obs, deterministic=True)
        action_idx = int(action)
        if action_idx < 0 or action_idx >= len(scored):
            raise RuntimeError("RL model produced invalid action index")
        return scored[action_idx]

    def recommend(self, payload: RecommandationRequest) -> RecommandationResponse:
        self.graph_service.reload()
        if self.graph_service.is_empty():
            raise ValueError("Referral network is empty. Initialize DB and seed demo data first.")

        scored = self._build_scored_candidates(payload)
        if not scored:
            raise ValueError("No reachable destination found from current centre")

        requested_policy = payload.routing_policy
        if requested_policy == "auto":
            requested_policy = get_recommendation_policy_default()
            if requested_policy not in {"auto", "heuristic", "rl"}:
                requested_policy = "auto"

        policy_used = "heuristic"
        fallback_reason: str | None = None

        if requested_policy == "rl":
            try:
                best = self._rl_best(scored)
                policy_used = "rl"
            except Exception as exc:
                best = self._heuristic_best(scored)
                fallback_reason = f"RL unavailable, fallback to heuristic: {exc}"
        elif requested_policy == "auto":
            try:
                best = self._rl_best(scored)
                policy_used = "rl"
            except Exception as exc:
                best = self._heuristic_best(scored)
                fallback_reason = f"Auto policy fallback to heuristic: {exc}"
        else:
            best = self._heuristic_best(scored)

        dest_attrs = self.graph_service.node(best.node_id)
        steps = [
            PathStep(
                centre_id=node_id,
                centre_name=self.graph_service.node(node_id)["name"],
                level=self.graph_service.node(node_id)["level"],
            )
            for node_id in best.path
        ]

        explanation = (
            f"Destination {dest_attrs['name']} selected because it matches speciality "
            f"{payload.needed_speciality}, has capacity {best.capacity}, and gives the best "
            f"tradeoff between travel ({best.travel_minutes:.0f} min) and wait "
            f"({best.wait_minutes:.0f} min) under severity '{payload.severity}' "
            f"(weight {best.severity_weight:.1f})."
        )
        rationale = (
            f"For a {payload.severity} case, CarePath prioritizes low combined travel+wait while "
            f"accounting for current capacity. {dest_attrs['name']} has the selected score."
        )

        return RecommandationResponse(
            patient_id=payload.patient_id,
            destination_centre_id=best.node_id,
            destination_name=dest_attrs["name"],
            path=steps,
            estimated_travel_minutes=best.travel_minutes,
            estimated_wait_minutes=best.wait_minutes,
            score=best.score,
            explanation=explanation,
            rationale=rationale,
            score_breakdown=ScoreBreakdown(
                travel_minutes=best.travel_minutes,
                wait_minutes=best.wait_minutes,
                capacity_available=best.capacity,
                capacity_factor_used=best.capacity_factor_used,
                severity=payload.severity,
                severity_weight=best.severity_weight,
                raw_cost_travel_plus_wait=best.raw_cost,
                final_score=best.score,
            ),
            policy_used=policy_used,
            fallback_reason=fallback_reason,
        )
