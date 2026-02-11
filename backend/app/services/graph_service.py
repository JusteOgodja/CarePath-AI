import networkx as nx
from sqlalchemy import select

from app.db.models import CentreModel, ReferenceModel, get_session


class GraphService:
    """Graph loaded from SQLite referral network tables."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self.reload()

    def reload(self) -> None:
        self.graph.clear()
        with get_session() as session:
            centres = session.scalars(select(CentreModel)).all()
            links = session.scalars(select(ReferenceModel)).all()

        for centre in centres:
            specialities = tuple(
                speciality.strip()
                for speciality in centre.specialities.split(",")
                if speciality.strip()
            )
            self.graph.add_node(
                centre.id,
                name=centre.name,
                level=centre.level,
                specialities=specialities,
                capacity_available=centre.capacity_available,
                estimated_wait_minutes=centre.estimated_wait_minutes,
            )

        for link in links:
            self.graph.add_edge(
                link.source_id,
                link.dest_id,
                travel_minutes=link.travel_minutes,
            )

    def is_empty(self) -> bool:
        return self.graph.number_of_nodes() == 0

    def candidate_destinations(self, needed_speciality: str) -> list[str]:
        results: list[str] = []
        for node_id, attrs in self.graph.nodes(data=True):
            if needed_speciality in attrs["specialities"] and attrs["capacity_available"] > 0:
                results.append(node_id)
        return results

    def shortest_path(self, source: str, target: str) -> tuple[list[str], float]:
        path = nx.shortest_path(self.graph, source=source, target=target, weight="travel_minutes")
        total_travel = nx.path_weight(self.graph, path, weight="travel_minutes")
        return path, float(total_travel)

    def node(self, node_id: str) -> dict:
        return dict(self.graph.nodes[node_id])
