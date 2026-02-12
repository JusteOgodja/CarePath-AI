import argparse
import json
from argparse import Namespace
from pathlib import Path

from simulate_batch import run_simulation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CarePath primary demo scenario")
    parser.add_argument("--patients", type=int, default=120)
    parser.add_argument("--output", type=str, default="docs/primary_demo_report.json")
    return parser.parse_args()


def build_primary_namespace(patients: int) -> Namespace:
    return Namespace(
        patients=patients,
        source="C_LOCAL_A",
        speciality="maternal",
        severity="medium",
        policy="heuristic",
        sample_source_by_catchment=True,
        case_mix_mode="mixed",
        severity_mode="mixed",
        maternal_ratio=0.35,
        pediatric_ratio=0.25,
        general_ratio=0.40,
        severity_low_ratio=0.60,
        severity_medium_ratio=0.30,
        severity_high_ratio=0.10,
        wait_increment=3,
        recovery_interval=5,
        recovery_amount=2,
        seed_demo=False,
        seed_complex=True,
        fallback_policy="force_least_loaded",
        fallback_overload_penalty=30.0,
        shock_every=0,
        shock_wait_add=0,
        shock_capacity_drop=0,
        random_seed=42,
    )


def main() -> None:
    args = parse_args()
    ns = build_primary_namespace(args.patients)
    report = run_simulation(ns)

    payload = {
        "scenario": "complex_maternal_stable",
        "patients": args.patients,
        "metrics": report,
    }
    rendered = json.dumps(payload, indent=2)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(rendered)

    print(rendered)


if __name__ == "__main__":
    main()
