# CarePath AI

Prototype local (100% gratuit) pour l'optimisation des parcours de reference patient:
- API FastAPI (recommandation + admin reseau)
- Graphe de soins (NetworkX)
- Simulation de scenarios + KPI equite (entropy_norm, HHI)
- Comparaison PPO vs Heuristic vs Random
- Frontend Streamlit de demo live

## Installation

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Config locale (`.env.example`):
- `DATABASE_URL` (defaut: `sqlite:///./carepath.db`)

## API Backend

```bash
cd backend
python scripts/init_db.py
python scripts/seed_demo_data.py
uvicorn app.main:app --reload
```

Docs API: `http://127.0.0.1:8000/docs`

### Endpoint metier
- `POST /recommander`
  - utilise `severity` dans le score
  - renvoie `rationale` + `score_breakdown`

## Streamlit Demo UI

Depuis la racine du projet:

```bash
streamlit run frontend/streamlit_app.py
```

Fonctions:
- charge centres/references via API
- visualise graphe + chemin recommande
- affiche destination, score, score_breakdown, rationale
- bouton pour lancer le scenario principal et afficher KPI

## One-command local demo runner

Depuis la racine du projet:

```bash
python scripts/run_local_demo.py
```

Ce script:
1. reset DB SQLite locale (sauf `--skip-reset`)
2. init DB + seed reseau complexe
3. genere rapports (`primary_demo_report`, `scenario_report`, `scenario_summary`)
4. lance FastAPI et Streamlit

Options:
- `--api-port 8000`
- `--ui-port 8501`
- `--skip-reset`

## Simulation et scenarios

### Batch simulation (heuristic ou random)

```bash
cd backend
python scripts/simulate_batch.py --seed-complex --patients 120 --source C_LOCAL_A --speciality maternal --severity medium --policy heuristic --wait-increment 3 --recovery-interval 5 --recovery-amount 2 --fallback-policy force_least_loaded --fallback-overload-penalty 30
```

Mode random:

```bash
python scripts/simulate_batch.py --seed-complex --patients 120 --source C_LOCAL_A --speciality maternal --severity medium --policy random --wait-increment 3 --recovery-interval 5 --recovery-amount 2 --fallback-policy none
```

KPI inclus:
- `failure_rate`, `fallback_rate`
- `avg_travel_minutes`, `avg_wait_minutes`, `avg_score`
- `entropy_norm` (plus haut = plus equitable)
- `hhi` (plus bas = moins concentre)

### Runner multi-scenarios

```bash
cd backend
python scripts/run_complex_scenarios.py --patients 120 --output docs/scenario_report.json
python scripts/summarize_scenarios.py --input docs/scenario_report.json --output docs/scenario_summary.md --weight-hhi 0.5 --weight-entropy-gap 0.5
```

Le resume Markdown contient une section Fairness et un ranking composite configurable.

## RL: Train + Evaluate (PPO vs Heuristic vs Random)

### Train

```bash
cd backend
python scripts/train_rl.py --seed-complex --source C_LOCAL_A --speciality maternal --patients-per-episode 80 --wait-increment 3 --recovery-interval 5 --recovery-amount 2 --overload-penalty 30 --timesteps 20000 --learning-rate 3e-4 --seed 42 --model-out models/ppo_referral
```

### Evaluate

```bash
cd backend
python scripts/evaluate_rl.py --seed-complex --model-path models/ppo_referral.zip --episodes 30 --source C_LOCAL_A --speciality maternal --patients-per-episode 80 --wait-increment 3 --recovery-interval 5 --recovery-amount 2 --overload-penalty 30 --seed 42
```

Sortie JSON harmonisee pour 3 methodes:
- `ppo`
- `heuristic`
- `random`

Chaque bloc contient:
- `avg_reward_per_episode`
- `avg_overloads_per_episode`
- `avg_travel`, `avg_wait`
- `failure_rate`, `fallback_rate`
- `entropy_norm`, `hhi`
- `destination_distribution`

## Scenario principal de demo

```bash
cd backend
python scripts/run_primary_demo.py --patients 120 --output docs/primary_demo_report.json
```

## Tests

```bash
cd backend
pytest -q
```

Couverture inclut:
- CRUD admin
- `/recommander` + payload explicable
- regression scoring + effet severity
- random baseline valide
- equite/saturation
