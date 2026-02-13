# CarePath AI

CarePath AI is a platform for optimizing patient referral pathways in healthcare networks.
It combines:
- a FastAPI backend for business orchestration,
- a recommendation engine (heuristic + RL/PPO),
- public data import and quality tooling,
- a React/Vite frontend for operations,
- simulation and policy benchmark scripts.

## 1. Project goals

### Main goal
Improve quality, speed, and fairness of patient transfers between health facilities.

### Technical goals
- Recommend the best destination according to specialty, severity, capacity, and travel time.
- Compare routing policies (`ppo`, `heuristic`, `random`) with consistent KPIs.
- Provide robust, secure, and observable APIs.
- Deliver an operational frontend with interactive 3D network visualization.

## 2. Global architecture

### Backend (`backend/`)
- Framework: FastAPI
- Validation: Pydantic
- Persistence: SQLite by default (PostgreSQL migration possible)
- Migrations: Alembic
- AI engine:
  - explainable heuristic routing
  - RL/PPO (Stable-Baselines3) via training/evaluation scripts

### Frontend (`frontend/`)
- Stack: React + Vite + TypeScript + TanStack Query + shadcn/ui
- Features:
  - triage/recommendation
  - network admin (centres/references)
  - patient referral workflow
  - indicators dashboard
  - interactive 3D graph
  - FR/EN language toggle

### Data and benchmarking
- Public data imports (facilities, indicators, population/catchment)
- Patient cohort simulation and policy comparison

## 3. Repository structure

```text
CarePath AI/
  backend/
    app/                # API, services, schemas, core, db
    scripts/            # data pipeline, simulation, RL train/eval
    tests/              # backend tests
    docs/               # JSON/MD benchmark and simulation reports
    models/             # trained models (.zip)
    requirements/       # split dependency sets
  frontend/
    src/
      components/
      pages/
      lib/
    package.json
  notebooks/
    model_benchmark_report.ipynb
  docs/
    release_checklist.md
  scripts/
    check.ps1
  README.md
```

## 4. Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+
- Optional: Jupyter for benchmark notebook

## 5. Quick start

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Minimal API install (without full RL/data stack):
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements/base.txt -r requirements/dev.txt
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 6. Configuration

Copy `.env.example` to `.env` and set:
- `DATABASE_URL` (default `sqlite:///./carepath.db`)
- `APP_ENV` (`development`/`production`)
- `AUTH_SECRET_KEY`
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`
- `VIEWER_USERNAME` / `VIEWER_PASSWORD`

## 7. Run services

### Backend API
```bash
cd backend
python scripts/init_db.py
python scripts/seed_demo_data.py
uvicorn app.main:app --reload
```

### Migrations
```bash
cd backend
python scripts/migrate.py
```

### API docs
- Swagger: `http://127.0.0.1:8000/docs`
- Health: `GET /api/v1/health`

## 8. Main business endpoints

### Auth
- `POST /api/v1/auth/login`

### Recommendation
- `POST /api/v1/recommander`
  - `routing_policy`: `heuristic` (default), `auto`, `rl`
  - explainability fields: `rationale`, `score_breakdown`

### Network admin
- `GET/POST/PUT/DELETE /api/v1/centres`
- `GET/POST/PUT/DELETE /api/v1/references`

### Patient referral workflow
- `GET/POST /api/v1/referrals/requests`
- `POST /api/v1/referrals/requests/{id}/accept`
- `POST /api/v1/referrals/requests/{id}/start-transfer`
- `POST /api/v1/referrals/requests/{id}/complete`
- `POST /api/v1/referrals/requests/{id}/reject`
- `POST /api/v1/referrals/requests/{id}/cancel`

### Indicators
- `GET /api/v1/indicators`
- `GET /api/v1/indicators/latest`

## 9. Frontend features

- Triage form + policy selector + explainable result panel
- Referral workflow page with filters/search/pagination
- Network admin CRUD for centres/references
- 3D graph with zoom/rotate/hover/focus/click-to-focus
- Indicators exploration and export
- System monitoring page
- Global FR/EN switch

## 10. Simulation and RL benchmark

### Batch simulation
```bash
cd backend
python scripts/simulate_batch.py --seed-complex --patients 120 --source C_LOCAL_A --speciality maternal --severity medium --policy heuristic --wait-increment 3 --recovery-interval 5 --recovery-amount 2 --fallback-policy force_least_loaded --fallback-overload-penalty 30
```

### PPO training
```bash
cd backend
python scripts/train_rl.py --seed-complex --source C_LOCAL_A --speciality maternal --patients-per-episode 80 --wait-increment 3 --recovery-interval 5 --recovery-amount 2 --overload-penalty 30 --timesteps 20000 --learning-rate 3e-4 --seed 42 --model-out models/ppo_referral
```

### PPO vs Heuristic vs Random evaluation
```bash
cd backend
python scripts/evaluate_rl.py --seed-complex --model-path models/ppo_referral.zip --episodes 30 --source C_LOCAL_A --speciality maternal --patients-per-episode 80 --wait-increment 3 --recovery-interval 5 --recovery-amount 2 --overload-penalty 30 --seed 42
```

### Kenya full pipeline
```bash
cd backend
python scripts/pipeline_kenya.py --reset-db
```

### Final Kenya benchmark
```bash
cd backend
python scripts/benchmark_policies_kenya.py --train-if-missing --timesteps 120000 --episodes 40 --model-path models/ppo_referral_kenya_mapped_v3.zip --travel-weight 1.1 --wait-weight 1.0 --fairness-penalty 6 --ent-coef 0.015 --output-json docs/final_benchmark_kenya_mapped_v3.json --output-md docs/final_benchmark_kenya_mapped_v3.md
```

## 11. Reference benchmark snapshot

Based on `backend/docs/final_benchmark_kenya_mapped_v3.json`:
- Composite winner: `ppo`
- Best reward: `ppo`
- Fairness trade-off: `random` spreads load better (high entropy / low hhi) but has much worse travel time.

## 12. Added notebook: model test results

Notebook path:
- `notebooks/model_benchmark_report.ipynb`

Notebook content:
- automatic loading of `backend/docs/*benchmark*.json`
- benchmark consolidation into DataFrame
- policy comparison (`ppo`, `heuristic`, `random`)
- charts for reward, travel, wait, fairness, composite score
- automatic winner summary by scenario
- destination distribution inspection per policy

Run notebook:
```bash
pip install jupyter pandas matplotlib
jupyter notebook notebooks/model_benchmark_report.ipynb
```

## 13. Quality, tests, CI

### Backend tests
```bash
cd backend
pytest -q
```

### Frontend checks
```bash
cd frontend
npm run typecheck
npm run lint
npm run test -- --run
```

### Local one-shot check
```powershell
.\scripts\check.ps1
```

### CI workflows
- `.github/workflows/ci.yml`
- `.github/workflows/secret-scan.yml`

## 14. Security and observability

- Bearer token auth
- RBAC (`admin`, `viewer`)
- `X-Request-ID` in responses
- structured JSON logs
- standardized error payloads
- in-memory rate limiting (auth + admin writes)

## 15. Data privacy

Default workflow uses aggregated public data (facilities, gridded population, indicators).
No patient-identifiable data is required by default.

## 16. Known limitations

- Calibration quality depends on source geospatial data quality.
- RL behavior is sensitive to hyperparameters and simulation settings.
- Benchmarks should be re-run after major scoring/weight changes.

## 17. Suggested roadmap

- Experiment tracking for RL runs (MLflow or equivalent)
- Centralized observability metrics (Prometheus/Grafana)
- Multi-country robustness campaign
- Deployment packaging (Docker Compose/Kubernetes)

## 18. Operational runbook (short)

1. Init DB + seed
2. Start API
3. Start frontend
4. Check `/api/v1/health`
5. Validate auth + referral workflow
6. Validate benchmark/notebook before release

For detailed pre-release controls, see `docs/release_checklist.md`.
