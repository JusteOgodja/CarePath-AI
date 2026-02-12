import argparse
import json
import sys
from pathlib import Path

from stable_baselines3 import PPO

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rl.env import ReferralEnv
from app.rl.evaluation import evaluate_heuristic, evaluate_ppo, evaluate_random
from simulate_batch import seed_complex_data, seed_demo_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate PPO vs heuristic vs random baseline")
    parser.add_argument("--seed-demo", action="store_true", help="Reset and seed demo data")
    parser.add_argument("--seed-complex", action="store_true", help="Reset and seed complex data")
    parser.add_argument("--model-path", type=str, default="models/ppo_referral.zip")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--source", type=str, default="C_LOCAL_A")
    parser.add_argument("--speciality", type=str, default="maternal")
    parser.add_argument("--patients-per-episode", type=int, default=80)
    parser.add_argument("--wait-increment", type=int, default=3)
    parser.add_argument("--recovery-interval", type=int, default=5)
    parser.add_argument("--recovery-amount", type=int, default=2)
    parser.add_argument("--overload-penalty", type=float, default=30.0)
    parser.add_argument("--travel-weight", type=float, default=1.0)
    parser.add_argument("--wait-weight", type=float, default=1.0)
    parser.add_argument("--fairness-penalty", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42, help="Base seed for deterministic evaluation")
    return parser.parse_args()


def build_env(args: argparse.Namespace) -> ReferralEnv:
    return ReferralEnv(
        source_id=args.source,
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


def main() -> None:
    args = parse_args()
    if args.seed_demo:
        seed_demo_data()
    if args.seed_complex:
        seed_complex_data()

    model_path = Path(args.model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    env_for_ppo = build_env(args)
    model = PPO.load(str(model_path), env=env_for_ppo)
    ppo_metrics = evaluate_ppo(model, env_for_ppo, args.episodes, seed_base=args.seed)

    env_for_heuristic = build_env(args)
    heuristic_metrics = evaluate_heuristic(
        env_for_heuristic,
        args.episodes,
        args.overload_penalty,
        seed_base=args.seed,
    )

    env_for_random = build_env(args)
    random_metrics = evaluate_random(env_for_random, args.episodes, seed_base=args.seed)

    report = {
        "episodes": args.episodes,
        "config": {
            "source": args.source,
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
        },
        "ppo": ppo_metrics,
        "heuristic": heuristic_metrics,
        "random": random_metrics,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
