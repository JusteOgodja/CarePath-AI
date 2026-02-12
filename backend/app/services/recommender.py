from dataclasses import dataclass

import networkx as nx

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

    def recommend(self, payload: RecommandationRequest) -> RecommandationResponse:
        self.graph_service.reload()
        if self.graph_service.is_empty():
            raise ValueError("Referral network is empty. Initialize DB and seed demo data first.")

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

        if not scored:
            raise ValueError("No reachable destination found from current centre")

        best = min(scored, key=lambda c: c.score)
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
            f"accounting for current capacity. {dest_attrs['name']} has the lowest final score."
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
        )
