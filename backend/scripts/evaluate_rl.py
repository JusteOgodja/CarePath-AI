import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stable_baselines3 import PPO

from app.rl.env import ReferralEnv
from app.rl.evaluation import evaluate_heuristic
from seed_demo_data import seed_demo_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate trained PPO vs heuristic baseline")
    parser.add_argument("--seed-demo", action="store_true", help="Reset and seed demo data")
    parser.add_argument("--model-path", type=str, default="models/ppo_referral.zip")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--source", type=str, default="C_LOCAL_A")
    parser.add_argument("--speciality", type=str, default="maternal")
    parser.add_argument("--patients-per-episode", type=int, default=80)
    parser.add_argument("--wait-increment", type=int, default=3)
    parser.add_argument("--recovery-interval", type=int, default=5)
    parser.add_argument("--recovery-amount", type=int, default=2)
    parser.add_argument("--overload-penalty", type=float, default=30.0)
    return parser.parse_args()


def evaluate_rl(model: PPO, env: ReferralEnv, episodes: int) -> dict:
    total_reward = 0.0
    total_overloads = 0
    destination_counts: dict[str, int] = {}

    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(int(action))
            total_reward += float(reward)
            if info["overload"]:
                total_overloads += 1
            dest = info["destination_id"]
            destination_counts[dest] = destination_counts.get(dest, 0) + 1
            done = terminated or truncated

    denom = max(episodes, 1)
    return {
        "avg_reward_per_episode": total_reward / denom,
        "avg_overloads_per_episode": total_overloads / denom,
        "destinations": destination_counts,
    }


def build_env(args: argparse.Namespace) -> ReferralEnv:
    return ReferralEnv(
        source_id=args.source,
        speciality=args.speciality,
        patients_per_episode=args.patients_per_episode,
        wait_increment=args.wait_increment,
        recovery_interval=args.recovery_interval,
        recovery_amount=args.recovery_amount,
        overload_penalty=args.overload_penalty,
    )


def main() -> None:
    args = parse_args()
    if args.seed_demo:
        seed_demo_data()

    model_path = Path(args.model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    env_for_rl = build_env(args)
    model = PPO.load(str(model_path), env=env_for_rl)
    rl_metrics = evaluate_rl(model, env_for_rl, args.episodes)

    env_for_heuristic = build_env(args)
    heuristic_metrics = evaluate_heuristic(env_for_heuristic, args.episodes, args.overload_penalty)

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
        },
        "rl": rl_metrics,
        "heuristic": heuristic_metrics,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
