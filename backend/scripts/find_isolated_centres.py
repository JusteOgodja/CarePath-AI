from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.graph_service import GraphService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find centres with no reachable referral destination")
    parser.add_argument(
        "--specialities",
        type=str,
        default="maternal,pediatric,general",
        help="Comma-separated specialities to evaluate",
    )
    parser.add_argument(
        "--only-fully-isolated",
        action="store_true",
        help="Only output centres isolated for all requested specialities",
    )
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output", type=str, default=None)
    return parser.parse_args()


def _parse_specialities(raw: str) -> list[str]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("At least one speciality is required")
    return values


def main() -> None:
    args = parse_args()
    specialities = _parse_specialities(args.specialities)

    graph_service = GraphService()
    graph = graph_service.graph
    if graph.number_of_nodes() == 0:
        payload = {"error": "empty_graph"}
        print(json.dumps(payload, indent=2))
        return

    candidates: dict[str, set[str]] = {}
    for speciality in specialities:
        candidates[speciality] = set(graph_service.candidate_destinations(speciality))

    isolated_rows: list[dict] = []
    for node_id in graph.nodes:
        attrs = graph_service.node(node_id)
        reachable = nx.descendants(graph, node_id)
        reachable_with_self = set(reachable)
        reachable_with_self.add(node_id)

        isolated_for: list[str] = []
        detail: dict[str, dict] = {}
        for speciality in specialities:
            eligible = set(candidates[speciality])
            if node_id in eligible:
                eligible.remove(node_id)
            reachable_eligible = eligible.intersection(reachable)
            is_isolated = len(reachable_eligible) == 0
            if is_isolated:
                isolated_for.append(speciality)
            detail[speciality] = {
                "eligible_destinations": len(eligible),
                "reachable_destinations": len(reachable_eligible),
                "isolated": is_isolated,
            }

        if not isolated_for:
            continue
        if args.only_fully_isolated and len(isolated_for) != len(specialities):
            continue

        isolated_rows.append(
            {
                "centre_id": node_id,
                "name": attrs.get("name"),
                "level": attrs.get("level"),
                "out_degree": int(graph.out_degree(node_id)),
                "reachable_nodes_total": len(reachable_with_self),
                "isolated_specialities": isolated_for,
                "detail": detail,
            }
        )

    isolated_rows.sort(
        key=lambda row: (
            -len(row["isolated_specialities"]),
            row["out_degree"],
            row["reachable_nodes_total"],
            row["centre_id"],
        )
    )

    limited_rows = isolated_rows[: max(1, args.limit)]
    payload = {
        "nodes_total": graph.number_of_nodes(),
        "edges_total": graph.number_of_edges(),
        "specialities_checked": specialities,
        "isolated_count": len(isolated_rows),
        "showing": len(limited_rows),
        "rows": limited_rows,
    }

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
