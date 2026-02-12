import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stable_baselines3 import PPO

from app.rl.env import ReferralEnv
from seed_demo_data import seed_demo_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train PPO for CarePath referral environment")
    parser.add_argument("--seed-demo", action="store_true", help="Reset and seed demo data")
    parser.add_argument("--source", type=str, default="C_LOCAL_A")
    parser.add_argument("--speciality", type=str, default="maternal")
    parser.add_argument("--patients-per-episode", type=int, default=80)
    parser.add_argument("--wait-increment", type=int, default=3)
    parser.add_argument("--recovery-interval", type=int, default=5)
    parser.add_argument("--recovery-amount", type=int, default=2)
    parser.add_argument("--overload-penalty", type=float, default=30.0)
    parser.add_argument("--timesteps", type=int, default=20000)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--model-out", type=str, default="models/ppo_referral")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.seed_demo:
        seed_demo_data()

    env = ReferralEnv(
        source_id=args.source,
        speciality=args.speciality,
        patients_per_episode=args.patients_per_episode,
        wait_increment=args.wait_increment,
        recovery_interval=args.recovery_interval,
        recovery_amount=args.recovery_amount,
        overload_penalty=args.overload_penalty,
    )

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=args.learning_rate,
        n_steps=256,
        batch_size=64,
        gamma=0.99,
    )
    model.learn(total_timesteps=args.timesteps)

    out_path = Path(args.model_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out_path))

    print(f"Model saved to: {out_path}.zip")


if __name__ == "__main__":
    main()
