import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
DB_PATH = BACKEND_DIR / "carepath.db"


def run_cmd(cmd: list[str], cwd: Path) -> None:
    print(f"[run] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="One-command local demo runner")
    parser.add_argument("--skip-reset", action="store_true", help="Do not remove existing SQLite file")
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--ui-port", type=int, default=8501)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.skip_reset and DB_PATH.exists():
        print(f"[info] deleting DB: {DB_PATH}")
        DB_PATH.unlink()

    run_cmd([sys.executable, "scripts/init_db.py"], BACKEND_DIR)
    run_cmd([sys.executable, "scripts/seed_complex_data.py"], BACKEND_DIR)
    run_cmd([sys.executable, "scripts/run_primary_demo.py", "--patients", "120", "--output", "docs/primary_demo_report.json"], BACKEND_DIR)
    run_cmd([sys.executable, "scripts/run_complex_scenarios.py", "--patients", "120", "--output", "docs/scenario_report.json"], BACKEND_DIR)
    run_cmd([sys.executable, "scripts/summarize_scenarios.py", "--input", "docs/scenario_report.json", "--output", "docs/scenario_summary.md"], BACKEND_DIR)

    env = os.environ.copy()
    api_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(args.api_port)]
    ui_cmd = [sys.executable, "-m", "streamlit", "run", str(REPO_ROOT / "frontend" / "streamlit_app.py"), "--server.port", str(args.ui_port)]

    print("[info] starting API + Streamlit. Press Ctrl+C to stop both.")
    api_proc = subprocess.Popen(api_cmd, cwd=BACKEND_DIR, env=env)
    time.sleep(1)
    ui_proc = subprocess.Popen(ui_cmd, cwd=REPO_ROOT, env=env)

    try:
        while True:
            if api_proc.poll() is not None:
                raise RuntimeError("API process exited unexpectedly")
            if ui_proc.poll() is not None:
                raise RuntimeError("Streamlit process exited unexpectedly")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[info] stopping services...")
    finally:
        for proc in (ui_proc, api_proc):
            if proc.poll() is None:
                proc.send_signal(signal.SIGINT)
        for proc in (ui_proc, api_proc):
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
