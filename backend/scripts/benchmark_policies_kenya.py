from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from stable_baselines3 import PPO

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CentreModel, get_session, init_db
from app.rl.env import ReferralEnv
from app.rl.evaluation import evaluate_heuristic, evaluate_ppo, evaluate_random


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark random vs heuristic vs PPO on Kenya dataset")
    parser.add_argument("--source", type=str, default=None, help="Optional source centre ID. If omitted, auto-pick.")
    parser.add_argument("--speciality", type=str, default="maternal")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--patients-per-episode", type=int, default=80)
    parser.add_argument("--wait-increment", type=int, default=3)
    parser.add_argument("--recovery-interval", type=int, default=5)
    parser.add_argument("--recovery-amount", type=int, default=2)
    parser.add_argument("--overload-penalty", type=float, default=30.0)
    parser.add_argument("--travel-weight", type=float, default=1.0)
    parser.add_argument("--wait-weight", type=float, default=1.0)
    parser.add_argument("--fairness-penalty", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model-path", type=str, default="models/ppo_referral_kenya.zip")
    parser.add_argument("--train-if-missing", action="store_true")
    parser.add_argument("--timesteps", type=int, default=15000)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--ent-coef", type=float, default=0.01)
    parser.add_argument("--weight-reward", type=float, default=1.0)
    parser.add_argument("--weight-travel", type=float, default=0.6)
    parser.add_argument("--weight-wait", type=float, default=0.8)
    parser.add_argument("--weight-hhi", type=float, default=0.4)
    parser.add_argument("--weight-entropy-gap", type=float, default=0.2)
    parser.add_argument("--weight-overloads", type=float, default=0.4)
    parser.add_argument("--output-json", type=str, default="docs/final_benchmark_kenya.json")
    parser.add_argument("--output-md", type=str, default="docs/final_benchmark_kenya.md")
    return parser.parse_args()


def build_env(args: argparse.Namespace, source_id: str) -> ReferralEnv:
    return ReferralEnv(
        source_id=source_id,
        speciality=args.speciality,
        patients_per_episode=args.patients_per_episode,
        wait_increment=args.wait_increment,
        recovery_interval=args.recovery_interval,
        recovery_amount=args.recovery_amount,
        overload_penalty=args.overload_penalty,
        travel_weight=args.travel_weight,
        wait_weight=args.wait_weight,
        fairness_penalty=args.fairness_penalty,
    )


def has_speciality(centre: CentreModel, speciality: str) -> bool:
    values = [s.strip() for s in centre.specialities.split(",") if s.strip()]
    return speciality in values


def pick_source(args: argparse.Namespace) -> str:
    if args.source:
        return args.source

    with get_session() as session:
        centres = session.query(CentreModel).all()

    candidates = [
        centre
        for centre in centres
        if has_speciality(centre, args.speciality)
        and not centre.id.startswith("C_LOCAL_")
        and not centre.id.startswith("H_")
    ]
    candidates.sort(key=lambda c: float(c.catchment_population or 0), reverse=True)

    for centre in candidates:
        try:
            _ = build_env(args, centre.id)
            return centre.id
        except Exception:
            continue
    raise ValueError("No valid source centre found for requested speciality")


def maybe_train_model(args: argparse.Namespace, source_id: str, model_path: Path) -> None:
    if model_path.exists():
        return
    if not args.train_if_missing:
        raise FileNotFoundError(
            f"Model not found: {model_path}. Use --train-if-missing or provide --model-path."
        )

    env = build_env(args, source_id)
    model = PPO(
        "MlpPolicy",
        env,
        verbose=0,
        learning_rate=args.learning_rate,
        ent_coef=args.ent_coef,
        n_steps=256,
        batch_size=64,
        gamma=0.99,
        seed=args.seed,
    )
    model.learn(total_timesteps=args.timesteps)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(model_path.with_suffix("")))


def rank_methods(metrics: dict[str, dict]) -> list[tuple[str, dict]]:
    return sorted(
        metrics.items(),
        key=lambda kv: (
            -float(kv[1]["avg_reward_per_episode"]),
            float(kv[1]["avg_overloads_per_episode"]),
            float(kv[1]["hhi"]),
        ),
    )


def _normalize(values: dict[str, float], *, higher_is_better: bool) -> dict[str, float]:
    min_v = min(values.values())
    max_v = max(values.values())
    if max_v == min_v:
        return {k: 0.0 for k in values.keys()}
    if higher_is_better:
        return {k: (max_v - v) / (max_v - min_v) for k, v in values.items()}
    return {k: (v - min_v) / (max_v - min_v) for k, v in values.items()}


def composite_rank(args: argparse.Namespace, metrics: dict[str, dict]) -> tuple[list[dict], dict]:
    reward_norm = _normalize({k: float(v["avg_reward_per_episode"]) for k, v in metrics.items()}, higher_is_better=True)
    travel_norm = _normalize({k: float(v["avg_travel"]) for k, v in metrics.items()}, higher_is_better=False)
    wait_norm = _normalize({k: float(v["avg_wait"]) for k, v in metrics.items()}, higher_is_better=False)
    hhi_norm = _normalize({k: float(v["hhi"]) for k, v in metrics.items()}, higher_is_better=False)
    entropy_gap_norm = _normalize(
        {k: (1.0 - float(v["entropy_norm"])) for k, v in metrics.items()},
        higher_is_better=False,
    )
    overload_norm = _normalize(
        {k: float(v["avg_overloads_per_episode"]) for k, v in metrics.items()},
        higher_is_better=False,
    )

    scores: dict[str, dict] = {}
    for policy in metrics.keys():
        composite = (
            args.weight_reward * reward_norm[policy]
            + args.weight_travel * travel_norm[policy]
            + args.weight_wait * wait_norm[policy]
            + args.weight_hhi * hhi_norm[policy]
            + args.weight_entropy_gap * entropy_gap_norm[policy]
            + args.weight_overloads * overload_norm[policy]
        )
        scores[policy] = {
            "composite_score": composite,
            "reward_norm": reward_norm[policy],
            "travel_norm": travel_norm[policy],
            "wait_norm": wait_norm[policy],
            "hhi_norm": hhi_norm[policy],
            "entropy_gap_norm": entropy_gap_norm[policy],
            "overload_norm": overload_norm[policy],
        }

    ranked = sorted(
        [{"policy": p, "metrics": metrics[p], "composite": scores[p]} for p in metrics.keys()],
        key=lambda row: row["composite"]["composite_score"],
    )
    return ranked, scores


def render_markdown(report: dict) -> str:
    rows = report["ranking_composite"]
    reward_rows = report["ranking_reward"]
    weights = report["composite_weights"]
    lines = [
        "# Kenya Policy Benchmark",
        "",
        f"Source: `{report['config']['source']}`",
        f"Speciality: `{report['config']['speciality']}`",
        f"Episodes: `{report['episodes']}`",
        "",
        "## Composite Ranking",
        "",
        "| Rank | Policy | Composite | Avg Reward/Episode | Avg Travel | Avg Wait | Entropy | HHI |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for idx, row in enumerate(rows, start=1):
        policy = row["policy"]
        m = row["metrics"]
        c = row["composite"]["composite_score"]
        lines.append(
            f"| {idx} | {policy} | {c:.4f} | {m['avg_reward_per_episode']:.4f} | "
            f"{m['avg_travel']:.4f} | {m['avg_wait']:.4f} | {m['entropy_norm']:.4f} | {m['hhi']:.4f} |"
        )
    lines.append("")
    lines.append("## Reward-Only Ranking")
    lines.append("")
    for idx, row in enumerate(reward_rows, start=1):
        lines.append(f"{idx}. `{row['policy']}` ({row['metrics']['avg_reward_per_episode']:.4f})")
    lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    lines.append(f"- Composite winner: **`{rows[0]['policy']}`**")
    lines.append(f"- Best pure reward: **`{reward_rows[0]['policy']}`**")
    lines.append("- Best equity proxy (highest entropy, lowest HHI): see `random` vs others in table.")
    lines.append("")
    lines.append("## Composite Weights")
    lines.append("")
    lines.append(
        f"- reward={weights['reward']}, travel={weights['travel']}, wait={weights['wait']}, "
        f"hhi={weights['hhi']}, entropy_gap={weights['entropy_gap']}, overloads={weights['overloads']}"
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    init_db()
    source_id = pick_source(args)
    model_path = Path(args.model_path)
    maybe_train_model(args, source_id, model_path)

    env_for_ppo = build_env(args, source_id)
    model = PPO.load(str(model_path), env=env_for_ppo)
    ppo_metrics = evaluate_ppo(model, env_for_ppo, args.episodes, seed_base=args.seed)

    env_for_heuristic = build_env(args, source_id)
    heuristic_metrics = evaluate_heuristic(
        env_for_heuristic,
        args.episodes,
        args.overload_penalty,
        seed_base=args.seed,
    )

    env_for_random = build_env(args, source_id)
    random_metrics = evaluate_random(env_for_random, args.episodes, seed_base=args.seed)

    metrics = {
        "ppo": ppo_metrics,
        "heuristic": heuristic_metrics,
        "random": random_metrics,
    }
    ranked_reward = rank_methods(metrics)
    ranked_composite, _composite_details = composite_rank(args, metrics)

    report = {
        "episodes": args.episodes,
        "config": {
            "source": source_id,
            "speciality": args.speciality,
            "patients_per_episode": args.patients_per_episode,
            "wait_increment": args.wait_increment,
            "recovery_interval": args.recovery_interval,
            "recovery_amount": args.recovery_amount,
            "overload_penalty": args.overload_penalty,
            "travel_weight": args.travel_weight,
            "wait_weight": args.wait_weight,
            "fairness_penalty": args.fairness_penalty,
            "seed": args.seed,
            "model_path": str(model_path),
        },
        "composite_weights": {
            "reward": args.weight_reward,
            "travel": args.weight_travel,
            "wait": args.weight_wait,
            "hhi": args.weight_hhi,
            "entropy_gap": args.weight_entropy_gap,
            "overloads": args.weight_overloads,
        },
        "metrics": metrics,
        "ranking_reward": [{"policy": name, "metrics": values} for name, values in ranked_reward],
        "ranking_composite": ranked_composite,
        "ranking": [{"policy": name, "metrics": values} for name, values in ranked_reward],
    }

    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    out_md = Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(report), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"[saved] {out_json}")
    print(f"[saved] {out_md}")


if __name__ == "__main__":
    main()
