from dataclasses import dataclass

import networkx as nx

from app.services.graph_service import GraphService
from app.services.schemas import PathStep, RecommandationRequest, RecommandationResponse


@dataclass
class CandidateScore:
    node_id: str
    path: list[str]
    travel_minutes: float
    wait_minutes: float
    capacity: int

    @property
    def score(self) -> float:
        # Lower is better: weighted travel + wait, adjusted by available capacity.
        return (self.travel_minutes + self.wait_minutes) / max(self.capacity, 1)


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

        scored: list[CandidateScore] = []
        for node_id in candidates:
            if node_id == payload.current_centre_id:
                continue
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
            f"({best.wait_minutes:.0f} min)."
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
        )
