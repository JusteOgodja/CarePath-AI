import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize CarePath scenario benchmark")
    parser.add_argument("--input", type=str, default="docs/scenario_report.json")
    parser.add_argument("--output", type=str, default="docs/scenario_summary.md")
    parser.add_argument("--weight-score", type=float, default=1.0)
    parser.add_argument("--weight-fallback", type=float, default=2.0)
    parser.add_argument("--weight-failure", type=float, default=5.0)
    parser.add_argument("--weight-hhi", type=float, default=0.0)
    parser.add_argument("--weight-entropy-gap", type=float, default=0.0)
    return parser.parse_args()


def composite_rank(
    *,
    avg_score: float,
    fallbacks: int,
    failures: int,
    patients: int,
    w_score: float,
    w_fallback: float,
    w_failure: float,
    w_hhi: float,
    w_entropy_gap: float,
    hhi: float,
    entropy_norm: float,
) -> float:
    fallback_rate = (fallbacks / patients) if patients else 0.0
    failure_rate = (failures / patients) if patients else 0.0
    entropy_gap = 1.0 - entropy_norm
    return (
        (w_score * avg_score)
        + (w_fallback * 100.0 * fallback_rate)
        + (w_failure * 100.0 * failure_rate)
        + (w_hhi * 100.0 * hhi)
        + (w_entropy_gap * 100.0 * entropy_gap)
    )


def to_row(idx: int, scenario: dict, args: argparse.Namespace, patients: int) -> dict:
    metrics = scenario["metrics"]
    rank_value = composite_rank(
        avg_score=float(metrics["avg_score"]),
        fallbacks=int(metrics["fallbacks_used"]),
        failures=int(metrics["patients_failed"]),
        patients=patients,
        w_score=args.weight_score,
        w_fallback=args.weight_fallback,
        w_failure=args.weight_failure,
        w_hhi=args.weight_hhi,
        w_entropy_gap=args.weight_entropy_gap,
        hhi=float(metrics.get("hhi", metrics["concentration_hhi"])),
        entropy_norm=float(metrics.get("entropy_norm", metrics["balance_entropy"])),
    )
    return {
        "rank": idx,
        "name": scenario["scenario"],
        "avg_score": float(metrics["avg_score"]),
        "avg_wait": float(metrics["avg_wait_minutes"]),
        "avg_travel": float(metrics["avg_travel_minutes"]),
        "fallbacks": int(metrics["fallbacks_used"]),
        "failures": int(metrics["patients_failed"]),
        "hhi": float(metrics.get("hhi", metrics["concentration_hhi"])),
        "entropy": float(metrics.get("entropy_norm", metrics["balance_entropy"])),
        "composite": rank_value,
    }


def recommendation(rows: list[dict]) -> str:
    best = rows[0]
    worst = rows[-1]
    lines = []
    lines.append(f"- Recommended primary setup: `{best['name']}` (lowest composite score `{best['composite']:.2f}`).")
    lines.append(f"- Keep `{worst['name']}` as stress-test baseline.")
    lines.append("- Use scenarios with shocks for resilience validation before clinical demo.")
    if best["fallbacks"] == 0:
        lines.append("- Best setup requires no fallback usage in this benchmark window.")
    return "\n".join(lines)


def render_markdown(rows: list[dict], report: dict, args: argparse.Namespace) -> str:
    lines = []
    lines.append("# CarePath Scenario Summary")
    lines.append("")
    lines.append(f"Patients per scenario: **{report['patients']}**")
    lines.append("")
    lines.append("## Ranking")
    lines.append("")
    lines.append("| Rank | Scenario | Composite | Avg Score | Avg Wait | Avg Travel | Fallbacks | Failures | HHI | Entropy |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['rank']} | {row['name']} | {row['composite']:.2f} | {row['avg_score']:.2f} | {row['avg_wait']:.2f} | {row['avg_travel']:.2f} | {row['fallbacks']} | {row['failures']} | {row['hhi']:.4f} | {row['entropy']:.4f} |"
        )

    lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    lines.append(recommendation(rows))
    lines.append("")
    lines.append("## Fairness")
    lines.append("")
    lines.append("- Higher normalized entropy indicates a more balanced referral distribution.")
    lines.append("- Lower HHI indicates lower concentration on a small subset of centers.")
    lines.append("")
    lines.append("## Scoring Weights")
    lines.append("")
    lines.append(
        f"- composite = {args.weight_score}*avg_score + {args.weight_fallback}*100*fallback_rate + {args.weight_failure}*100*failure_rate + {args.weight_hhi}*100*hhi + {args.weight_entropy_gap}*100*(1-entropy_norm)"
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Scenario report not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as handle:
        report = json.load(handle)

    scenarios = report.get("scenarios", [])
    patients = int(report.get("patients", 0))
    if not scenarios:
        raise ValueError("No scenarios found in report")

    sortable = []
    for scenario in scenarios:
        metrics = scenario["metrics"]
        score = composite_rank(
            avg_score=float(metrics["avg_score"]),
            fallbacks=int(metrics["fallbacks_used"]),
            failures=int(metrics["patients_failed"]),
            patients=patients,
            w_score=args.weight_score,
            w_fallback=args.weight_fallback,
            w_failure=args.weight_failure,
            w_hhi=args.weight_hhi,
            w_entropy_gap=args.weight_entropy_gap,
            hhi=float(metrics.get("hhi", metrics["concentration_hhi"])),
            entropy_norm=float(metrics.get("entropy_norm", metrics["balance_entropy"])),
        )
        sortable.append((score, scenario))

    sortable.sort(key=lambda x: x[0])
    rows = [to_row(i + 1, scenario, args, patients) for i, (_, scenario) in enumerate(sortable)]

    markdown = render_markdown(rows, report, args)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(markdown)

    print(markdown)


if __name__ == "__main__":
    main()
