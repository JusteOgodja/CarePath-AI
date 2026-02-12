import argparse
import json
from argparse import Namespace
from pathlib import Path

from simulate_batch import run_simulation


def build_case(name: str, base: dict, **overrides) -> dict:
    merged = dict(base)
    merged.update(overrides)
    merged["name"] = name
    return merged


def cases() -> list[dict]:
    base = {
        "patients": 80,
        "severity": "medium",
        "fallback_policy": "force_least_loaded",
        "fallback_overload_penalty": 30.0,
        "recovery_interval": 5,
        "recovery_amount": 2,
        "wait_increment": 3,
        "shock_every": 0,
        "shock_wait_add": 0,
        "shock_capacity_drop": 0,
        "random_seed": 42,
    }
    return [
        build_case(
            "demo_maternal_stable",
            base,
            source="C_LOCAL_A",
            speciality="maternal",
            seed_demo=True,
            seed_complex=False,
        ),
        build_case(
            "demo_maternal_shock",
            base,
            source="C_LOCAL_A",
            speciality="maternal",
            seed_demo=True,
            seed_complex=False,
            shock_every=10,
            shock_wait_add=10,
            shock_capacity_drop=1,
        ),
        build_case(
            "complex_maternal_stable",
            base,
            source="C_LOCAL_A",
            speciality="maternal",
            seed_demo=False,
            seed_complex=True,
        ),
        build_case(
            "complex_pediatric_shock",
            base,
            source="C_LOCAL_B",
            speciality="pediatric",
            seed_demo=False,
            seed_complex=True,
            shock_every=8,
            shock_wait_add=12,
            shock_capacity_drop=1,
        ),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run multiple complex simulation scenarios")
    parser.add_argument("--patients", type=int, default=80)
    parser.add_argument("--output", type=str, default="")
    return parser.parse_args()


def scenario_namespace(case: dict, patients: int) -> Namespace:
    merged = dict(case)
    merged["patients"] = patients
    return Namespace(**merged)


def main() -> None:
    args = parse_args()

    results = []
    for case in cases():
        ns = scenario_namespace(case, args.patients)
        report = run_simulation(ns)
        results.append(
            {
                "scenario": case["name"],
                "config": {
                    "source": case["source"],
                    "speciality": case["speciality"],
                    "seed_demo": case["seed_demo"],
                    "seed_complex": case["seed_complex"],
                    "shock_every": case["shock_every"],
                    "shock_wait_add": case["shock_wait_add"],
                    "shock_capacity_drop": case["shock_capacity_drop"],
                },
                "metrics": report,
            }
        )

    summary = {
        "patients": args.patients,
        "scenarios": results,
    }

    rendered = json.dumps(summary, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="ascii") as handle:
            handle.write(rendered)
    print(rendered)


if __name__ == "__main__":
    main()
