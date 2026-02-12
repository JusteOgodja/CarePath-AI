from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import httpx
import networkx as nx
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CentreModel, ReferenceModel, get_session, init_db
from app.services.graph_service import GraphService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repair isolated centres by adding nearest fallback referral edges")
    parser.add_argument("--specialities", type=str, default="maternal,pediatric,general")
    parser.add_argument("--targets-per-centre", type=int, default=2)
    parser.add_argument("--speed-kmh", type=float, default=40.0)
    parser.add_argument("--osrm-server", type=str, default=None, help="Optional local OSRM base URL")
    parser.add_argument(
        "--include-partially-isolated",
        action="store_true",
        default=False,
        help="Also repair centres isolated for only a subset of requested specialities",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=str, default="docs/isolated_repair_report.json")
    return parser.parse_args()


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2) + math.cos(p1) * math.cos(p2) * (math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def estimate_travel_minutes(distance_km: float, speed_kmh: float) -> int:
    if speed_kmh <= 0:
        raise ValueError("speed_kmh must be > 0")
    return max(1, int(round((distance_km / speed_kmh) * 60.0)))


def estimate_travel_minutes_osrm(
    *,
    source: CentreModel,
    target: CentreModel,
    osrm_server: str | None,
    speed_kmh: float,
) -> int:
    if osrm_server and source.lat is not None and source.lon is not None and target.lat is not None and target.lon is not None:
        try:
            coords = f"{source.lon},{source.lat};{target.lon},{target.lat}"
            url = f"{osrm_server.rstrip('/')}/route/v1/driving/{coords}"
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, params={"overview": "false"})
                resp.raise_for_status()
                payload = resp.json()
            routes = payload.get("routes", [])
            if routes:
                duration_s = float(routes[0].get("duration", 0.0))
                if duration_s > 0:
                    return max(1, int(round(duration_s / 60.0)))
        except Exception:
            pass

    if source.lat is None or source.lon is None or target.lat is None or target.lon is None:
        return 1
    dist = haversine_km(source.lat, source.lon, target.lat, target.lon)
    return estimate_travel_minutes(dist, speed_kmh)


def parse_specialities(raw: str) -> list[str]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("At least one speciality is required")
    return values


def is_isolated_for_speciality(
    *,
    graph_service: GraphService,
    source_id: str,
    speciality: str,
) -> bool:
    graph = graph_service.graph
    candidates = set(graph_service.candidate_destinations(speciality))
    candidates.discard(source_id)
    if not candidates:
        return True
    reachable = nx.descendants(graph, source_id)
    return len(candidates.intersection(reachable)) == 0


def level_rank(level: str | None) -> int:
    return {"primary": 1, "secondary": 2, "tertiary": 3}.get((level or "").lower(), 1)


def level_distance(src_level: str | None, dst_level: str | None) -> int:
    return abs(level_rank(src_level) - level_rank(dst_level))


def main() -> None:
    args = parse_args()
    init_db()
    specialities = parse_specialities(args.specialities)

    graph_service = GraphService()
    graph = graph_service.graph

    with get_session() as session:
        centres = session.scalars(select(CentreModel)).all()
        centres_by_id = {c.id: c for c in centres}
        existing_edges = {(r.source_id, r.dest_id) for r in session.scalars(select(ReferenceModel)).all()}

        isolated_ids: list[str] = []
        for centre in centres:
            isolated_for = [
                speciality
                for speciality in specialities
                if is_isolated_for_speciality(
                    graph_service=graph_service,
                    source_id=centre.id,
                    speciality=speciality,
                )
            ]
            if not isolated_for:
                continue
            if not args.include_partially_isolated and len(isolated_for) != len(specialities):
                continue
            isolated_ids.append(centre.id)

        created = 0
        skipped = 0
        repaired_centres: list[dict] = []

        for source_id in isolated_ids:
            source = centres_by_id[source_id]
            if source.lat is None or source.lon is None:
                skipped += 1
                continue

            candidates: list[tuple[CentreModel, float, int]] = []
            for target in centres:
                if target.id == source_id:
                    continue
                if target.lat is None or target.lon is None:
                    continue
                if (source_id, target.id) in existing_edges:
                    continue
                dist = haversine_km(source.lat, source.lon, target.lat, target.lon)
                lvl_dist = level_distance(source.level, target.level)
                candidates.append((target, dist, lvl_dist))

            candidates.sort(key=lambda x: (x[2], x[1], x[0].id))
            chosen = candidates[: max(1, args.targets_per_centre)]

            added_targets: list[str] = []
            for target, _dist, _lvl_dist in chosen:
                if (source_id, target.id) in existing_edges:
                    skipped += 1
                    continue
                travel = estimate_travel_minutes_osrm(
                    source=source,
                    target=target,
                    osrm_server=args.osrm_server,
                    speed_kmh=args.speed_kmh,
                )
                if not args.dry_run:
                    session.add(
                        ReferenceModel(
                            source_id=source_id,
                            dest_id=target.id,
                            travel_minutes=travel,
                        )
                    )
                existing_edges.add((source_id, target.id))
                created += 1
                added_targets.append(target.id)

            repaired_centres.append(
                {
                    "source_id": source_id,
                    "source_name": source.name,
                    "source_level": source.level,
                    "added_targets": added_targets,
                }
            )

        if not args.dry_run:
            session.commit()

    graph_service.reload()
    payload = {
        "dry_run": args.dry_run,
        "specialities": specialities,
        "isolated_centres_before": len(isolated_ids),
        "created_edges": created,
        "skipped_edges": skipped,
        "targets_per_centre": args.targets_per_centre,
        "sample_repairs": repaired_centres[:40],
        "graph_nodes": graph_service.graph.number_of_nodes(),
        "graph_edges": graph_service.graph.number_of_edges(),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
