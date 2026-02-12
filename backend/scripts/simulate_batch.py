import argparse
import math
import random
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CentreModel, get_session, init_db
from app.services.graph_service import GraphService
from app.services.recommender import Recommender
from app.services.schemas import RecommandationRequest


@dataclass
class FallbackDecision:
    destination_id: str
    travel_minutes: float
    wait_minutes: float
    score: float
    reason: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch simulation for CarePath referral strategy")
    parser.add_argument("--patients", type=int, default=50, help="Number of simulated patients")
    parser.add_argument("--source", type=str, default="C_LOCAL_A", help="Source centre ID")
    parser.add_argument("--speciality", type=str, default="maternal", help="Requested speciality")
    parser.add_argument("--severity", type=str, default="medium", help="Patient severity (low|medium|high)")
    parser.add_argument(
        "--wait-increment",
        type=int,
        default=5,
        help="Minutes added to destination waiting time after each referral",
    )
    parser.add_argument(
        "--recovery-interval",
        type=int,
        default=10,
        help="Apply capacity recovery every N patients (0 disables recovery)",
    )
    parser.add_argument(
        "--recovery-amount",
        type=int,
        default=1,
        help="Recovered capacity units per interval for each centre",
    )
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="Reset and seed demo network before simulation",
    )
    parser.add_argument(
        "--seed-complex",
        action="store_true",
        help="Reset and seed complex network before simulation",
    )
    parser.add_argument(
        "--fallback-policy",
        type=str,
        choices=["none", "force_least_loaded"],
        default="none",
        help="Fallback when no standard recommendation is available",
    )
    parser.add_argument(
        "--fallback-overload-penalty",
        type=float,
        default=30.0,
        help="Penalty added in fallback score when destination capacity is zero",
    )
    parser.add_argument("--shock-every", type=int, default=0, help="Apply random shock every N patients")
    parser.add_argument("--shock-wait-add", type=int, default=0, help="Wait minutes added during shock")
    parser.add_argument(
        "--shock-capacity-drop",
        type=int,
        default=0,
        help="Capacity units removed during shock",
    )
    parser.add_argument("--random-seed", type=int, default=42, help="Random seed for shocks")
    return parser.parse_args()


def seed_demo_data() -> None:
    from app.db.models import ReferenceModel

    init_db()
    with get_session() as session:
        session.query(ReferenceModel).delete()
        session.query(CentreModel).delete()

        centres = [
            CentreModel(
                id="C_LOCAL_A",
                name="Centre Local A",
                level="primary",
                specialities="general,maternal",
                capacity_available=3,
                estimated_wait_minutes=30,
            ),
            CentreModel(
                id="C_LOCAL_B",
                name="Centre Local B",
                level="primary",
                specialities="general",
                capacity_available=2,
                estimated_wait_minutes=20,
            ),
            CentreModel(
                id="H_DISTRICT_1",
                name="Hopital District 1",
                level="secondary",
                specialities="general,maternal,pediatric",
                capacity_available=4,
                estimated_wait_minutes=45,
            ),
            CentreModel(
                id="H_REGIONAL_1",
                name="Hopital Regional 1",
                level="tertiary",
                specialities="maternal,pediatric",
                capacity_available=6,
                estimated_wait_minutes=35,
            ),
        ]

        refs = [
            ReferenceModel(source_id="C_LOCAL_A", dest_id="H_DISTRICT_1", travel_minutes=20),
            ReferenceModel(source_id="C_LOCAL_B", dest_id="H_DISTRICT_1", travel_minutes=15),
            ReferenceModel(source_id="H_DISTRICT_1", dest_id="H_REGIONAL_1", travel_minutes=35),
            ReferenceModel(source_id="C_LOCAL_A", dest_id="H_REGIONAL_1", travel_minutes=60),
            ReferenceModel(source_id="C_LOCAL_B", dest_id="H_REGIONAL_1", travel_minutes=70),
        ]

        session.add_all(centres)
        session.add_all(refs)
        session.commit()


def seed_complex_data() -> None:
    from app.db.models import ReferenceModel

    init_db()
    with get_session() as session:
        session.query(ReferenceModel).delete()
        session.query(CentreModel).delete()

        centres = [
            CentreModel(id="C_LOCAL_A", name="Centre Local A", level="primary", specialities="general,maternal", capacity_available=4, estimated_wait_minutes=20),
            CentreModel(id="C_LOCAL_B", name="Centre Local B", level="primary", specialities="general,pediatric", capacity_available=4, estimated_wait_minutes=18),
            CentreModel(id="C_LOCAL_C", name="Centre Local C", level="primary", specialities="general,maternal,pediatric", capacity_available=3, estimated_wait_minutes=22),
            CentreModel(id="H_DISTRICT_1", name="Hopital District 1", level="secondary", specialities="general,maternal", capacity_available=6, estimated_wait_minutes=30),
            CentreModel(id="H_DISTRICT_2", name="Hopital District 2", level="secondary", specialities="general,pediatric", capacity_available=6, estimated_wait_minutes=28),
            CentreModel(id="H_MATERNAL_1", name="Hopital Maternal 1", level="secondary", specialities="maternal", capacity_available=5, estimated_wait_minutes=35),
            CentreModel(id="H_PEDIATRIC_1", name="Hopital Pediatric 1", level="secondary", specialities="pediatric", capacity_available=5, estimated_wait_minutes=35),
            CentreModel(id="H_REGIONAL_1", name="Hopital Regional 1", level="tertiary", specialities="general,maternal,pediatric", capacity_available=8, estimated_wait_minutes=40),
            CentreModel(id="H_REGIONAL_2", name="Hopital Regional 2", level="tertiary", specialities="general,maternal,pediatric", capacity_available=8, estimated_wait_minutes=38),
        ]

        refs = [
            ("C_LOCAL_A", "H_DISTRICT_1", 15), ("C_LOCAL_A", "H_MATERNAL_1", 25), ("C_LOCAL_A", "H_REGIONAL_1", 45),
            ("C_LOCAL_B", "H_DISTRICT_2", 14), ("C_LOCAL_B", "H_PEDIATRIC_1", 24), ("C_LOCAL_B", "H_REGIONAL_2", 44),
            ("C_LOCAL_C", "H_DISTRICT_1", 18), ("C_LOCAL_C", "H_DISTRICT_2", 20), ("C_LOCAL_C", "H_REGIONAL_1", 40),
            ("H_DISTRICT_1", "H_REGIONAL_1", 22), ("H_DISTRICT_1", "H_REGIONAL_2", 30),
            ("H_DISTRICT_2", "H_REGIONAL_2", 22), ("H_DISTRICT_2", "H_REGIONAL_1", 30),
            ("H_MATERNAL_1", "H_REGIONAL_1", 20), ("H_PEDIATRIC_1", "H_REGIONAL_2", 20),
            ("H_REGIONAL_1", "H_REGIONAL_2", 18), ("H_REGIONAL_2", "H_REGIONAL_1", 18),
        ]
        from app.db.models import ReferenceModel
        session.add_all(centres)
        session.add_all([ReferenceModel(source_id=s, dest_id=d, travel_minutes=t) for s, d, t in refs])
        session.commit()


def get_initial_capacities() -> dict[str, int]:
    with get_session() as session:
        centres = session.scalars(select(CentreModel)).all()
    return {centre.id: centre.capacity_available for centre in centres}


def apply_referral_impact(destination_id: str, wait_increment: int) -> None:
    with get_session() as session:
        centre = session.get(CentreModel, destination_id)
        if centre is None:
            return
        if centre.capacity_available > 0:
            centre.capacity_available -= 1
        centre.estimated_wait_minutes += wait_increment
        session.commit()


def apply_recovery(initial_caps: dict[str, int], recovery_amount: int) -> None:
    with get_session() as session:
        for centre_id, max_capacity in initial_caps.items():
            centre = session.get(CentreModel, centre_id)
            if centre is None:
                continue
            centre.capacity_available = min(max_capacity, centre.capacity_available + recovery_amount)
            centre.estimated_wait_minutes = max(0, centre.estimated_wait_minutes - (2 * recovery_amount))
        session.commit()


def apply_random_shock(
    *,
    source_id: str,
    speciality: str,
    capacity_drop: int,
    wait_add: int,
    rng: random.Random,
) -> None:
    with get_session() as session:
        centres = session.scalars(select(CentreModel)).all()
        candidates = []
        for centre in centres:
            if centre.id == source_id:
                continue
            specialities = [s.strip() for s in centre.specialities.split(",") if s.strip()]
            if speciality in specialities:
                candidates.append(centre)
        if not candidates:
            return
        target = rng.choice(candidates)
        target.capacity_available = max(0, target.capacity_available - max(capacity_drop, 0))
        target.estimated_wait_minutes = max(0, target.estimated_wait_minutes + max(wait_add, 0))
        session.commit()


def normalized_entropy(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total == 0 or len(counts) <= 1:
        return 0.0
    probs = [value / total for value in counts.values()]
    entropy = -sum(p * math.log(p) for p in probs)
    return entropy / math.log(len(counts))


def preflight_snapshot(source_id: str, speciality: str) -> dict:
    with get_session() as session:
        centres = session.scalars(select(CentreModel)).all()

    source_exists = any(c.id == source_id for c in centres)
    eligible = 0
    for centre in centres:
        specialities = [s.strip() for s in centre.specialities.split(",") if s.strip()]
        if speciality in specialities and centre.capacity_available > 0:
            eligible += 1

    return {
        "centres_total": len(centres),
        "source_exists": source_exists,
        "eligible_destinations": eligible,
    }


def fallback_recommendation(
    *,
    source_id: str,
    speciality: str,
    overload_penalty: float,
) -> FallbackDecision | None:
    graph_service = GraphService()
    graph_service.reload()
    if graph_service.is_empty():
        return None

    # In fallback mode we allow overloaded destinations (capacity can be zero),
    # but we still require speciality compatibility and connectivity.
    candidates: list[FallbackDecision] = []
    for node_id, attrs in graph_service.graph.nodes(data=True):
        if node_id == source_id:
            continue
        if speciality not in attrs.get("specialities", ()):
            continue

        try:
            _, travel_minutes = graph_service.shortest_path(source_id, node_id)
        except Exception:
            continue

        wait_minutes = float(attrs["estimated_wait_minutes"])
        capacity = int(attrs["capacity_available"])
        score = (travel_minutes + wait_minutes) / max(capacity, 1)
        if capacity <= 0:
            score += overload_penalty

        candidates.append(
            FallbackDecision(
                destination_id=node_id,
                travel_minutes=travel_minutes,
                wait_minutes=wait_minutes,
                score=score,
                reason="fallback_force_least_loaded",
            )
        )

    if not candidates:
        return None
    return min(candidates, key=lambda item: item.score)


def run_simulation(args: argparse.Namespace) -> dict:
    init_db()
    if args.seed_demo:
        seed_demo_data()
    if getattr(args, "seed_complex", False):
        seed_complex_data()

    snapshot = preflight_snapshot(args.source, args.speciality)
    initial_caps = get_initial_capacities()
    recommender = Recommender()
    rng = random.Random(args.random_seed)

    destination_counts: Counter[str] = Counter()
    fallback_destination_counts: Counter[str] = Counter()
    failure_reasons: Counter[str] = Counter()
    failures = 0
    fallbacks_used = 0
    total_travel = 0.0
    total_wait = 0.0
    total_score = 0.0

    for idx in range(1, args.patients + 1):
        payload = RecommandationRequest(
            patient_id=f"SIM_{idx:04d}",
            current_centre_id=args.source,
            needed_speciality=args.speciality,
            severity=args.severity,
        )

        try:
            recommendation = recommender.recommend(payload)
        except ValueError as exc:
            if args.fallback_policy == "force_least_loaded":
                fallback = fallback_recommendation(
                    source_id=args.source,
                    speciality=args.speciality,
                    overload_penalty=args.fallback_overload_penalty,
                )
                if fallback is not None:
                    fallbacks_used += 1
                    destination_counts[fallback.destination_id] += 1
                    fallback_destination_counts[fallback.destination_id] += 1
                    total_travel += fallback.travel_minutes
                    total_wait += fallback.wait_minutes
                    total_score += fallback.score
                    apply_referral_impact(fallback.destination_id, args.wait_increment)
                else:
                    failures += 1
                    failure_reasons[str(exc)] += 1
            else:
                failures += 1
                failure_reasons[str(exc)] += 1
        else:
            destination_counts[recommendation.destination_centre_id] += 1
            total_travel += recommendation.estimated_travel_minutes
            total_wait += recommendation.estimated_wait_minutes
            total_score += recommendation.score
            apply_referral_impact(recommendation.destination_centre_id, args.wait_increment)

        if args.recovery_interval > 0 and idx % args.recovery_interval == 0:
            apply_recovery(initial_caps, args.recovery_amount)
        if args.shock_every > 0 and idx % args.shock_every == 0:
            apply_random_shock(
                source_id=args.source,
                speciality=args.speciality,
                capacity_drop=args.shock_capacity_drop,
                wait_add=args.shock_wait_add,
                rng=rng,
            )

    success_count = args.patients - failures
    avg_travel = total_travel / success_count if success_count else 0.0
    avg_wait = total_wait / success_count if success_count else 0.0
    avg_score = total_score / success_count if success_count else 0.0

    proportions = [count / success_count for count in destination_counts.values()] if success_count else []
    concentration_hhi = sum(p * p for p in proportions)

    return {
        "patients_total": args.patients,
        "patients_success": success_count,
        "patients_failed": failures,
        "fallbacks_used": fallbacks_used,
        "failure_rate": failures / args.patients if args.patients else 0.0,
        "avg_travel_minutes": avg_travel,
        "avg_wait_minutes": avg_wait,
        "avg_score": avg_score,
        "destination_counts": dict(destination_counts),
        "fallback_destination_counts": dict(fallback_destination_counts),
        "failure_reasons": dict(failure_reasons),
        "concentration_hhi": concentration_hhi,
        "balance_entropy": normalized_entropy(destination_counts),
        "preflight": snapshot,
        "fallback_policy": args.fallback_policy,
        "shock_config": {
            "shock_every": args.shock_every,
            "shock_wait_add": args.shock_wait_add,
            "shock_capacity_drop": args.shock_capacity_drop,
            "random_seed": args.random_seed,
        },
    }


def print_report(report: dict) -> None:
    print("=== CarePath Batch Simulation ===")
    print("Preflight checks   :")
    print(f"  - centres total      : {report['preflight']['centres_total']}")
    print(f"  - source exists      : {report['preflight']['source_exists']}")
    print(f"  - eligible destinations: {report['preflight']['eligible_destinations']}")
    print(f"Patients total     : {report['patients_total']}")
    print(f"Patients success   : {report['patients_success']}")
    print(f"Patients failed    : {report['patients_failed']}")
    print(f"Fallbacks used     : {report['fallbacks_used']}")
    print(f"Fallback policy    : {report['fallback_policy']}")
    print("Shock config       :")
    print(f"  - every            : {report['shock_config']['shock_every']}")
    print(f"  - wait_add         : {report['shock_config']['shock_wait_add']}")
    print(f"  - capacity_drop    : {report['shock_config']['shock_capacity_drop']}")
    print(f"  - random_seed      : {report['shock_config']['random_seed']}")
    print(f"Failure rate       : {report['failure_rate']:.2%}")
    print(f"Avg travel (min)   : {report['avg_travel_minutes']:.2f}")
    print(f"Avg wait (min)     : {report['avg_wait_minutes']:.2f}")
    print(f"Avg score          : {report['avg_score']:.2f}")
    print(f"Concentration HHI  : {report['concentration_hhi']:.4f}")
    print(f"Balance entropy    : {report['balance_entropy']:.4f}")
    print("Destination counts :")
    if report["destination_counts"]:
        for destination, count in sorted(report["destination_counts"].items()):
            print(f"  - {destination}: {count}")
    else:
        print("  - none")
    if report["failure_reasons"]:
        print("Failure reasons    :")
        for reason, count in sorted(report["failure_reasons"].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {reason}: {count}")
    if report["fallback_destination_counts"]:
        print("Fallback routing   :")
        for destination, count in sorted(report["fallback_destination_counts"].items()):
            print(f"  - {destination}: {count}")


def main() -> None:
    args = parse_args()
    report = run_simulation(args)
    print_report(report)


if __name__ == "__main__":
    main()
