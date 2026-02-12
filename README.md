# CarePath AI

Prototype pour optimiser les parcours de reference patient via un graphe de soins,
une API FastAPI, puis extension RL + explicabilite.

## 1) Installation rapide

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Initialiser la base et charger les donnees de demo

```bash
cd backend
python scripts/init_db.py
python scripts/seed_demo_data.py
```

## 3) Lancer l'API

```bash
cd backend
uvicorn app.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`

## 4) Tests automatiques

```bash
cd backend
pytest -q
```

## 5) Simulation batch (pre-RL)

Simulation multi-patients pour mesurer delai, saturation et equilibre des orientations.

```bash
cd backend
python scripts/simulate_batch.py --seed-demo --patients 80 --source C_LOCAL_A --speciality maternal --severity medium --wait-increment 5 --recovery-interval 10 --recovery-amount 1
```

Mode triage de secours (evite les echecs durs en saturation):

```bash
cd backend
python scripts/simulate_batch.py --seed-demo --patients 80 --source C_LOCAL_A --speciality maternal --severity medium --wait-increment 5 --recovery-interval 10 --recovery-amount 1 --fallback-policy force_least_loaded --fallback-overload-penalty 30
```

Mode reseau complexe + perturbations aleatoires:

```bash
cd backend
python scripts/simulate_batch.py --seed-complex --patients 120 --source C_LOCAL_B --speciality pediatric --severity medium --wait-increment 3 --recovery-interval 5 --recovery-amount 2 --fallback-policy force_least_loaded --fallback-overload-penalty 30 --shock-every 8 --shock-wait-add 12 --shock-capacity-drop 1 --random-seed 42
```

Runner multi-scenarios (demo + complexe, stable + shock):

```bash
cd backend
python scripts/run_complex_scenarios.py --patients 120 --output docs/scenario_report.json
```

Synthese automatique (tableau classe + recommandation):

```bash
cd backend
python scripts/summarize_scenarios.py --input docs/scenario_report.json --output docs/scenario_summary.md
```

Scenario principal de demo (recommande):

```bash
cd backend
python scripts/run_primary_demo.py --patients 120 --output docs/primary_demo_report.json
```

Metriques affichees:
- `avg_travel_minutes`
- `avg_wait_minutes`
- `failure_rate`
- `fallbacks_used`
- `concentration_hhi` (plus faible = moins de concentration)
- `balance_entropy` (plus eleve = meilleure repartition)
- `failure_reasons` (diagnostic des echecs)

## 6) Entrainement RL (PPO)

```bash
cd backend
python scripts/train_rl.py --seed-demo --source C_LOCAL_A --speciality maternal --patients-per-episode 80 --wait-increment 3 --recovery-interval 5 --recovery-amount 2 --overload-penalty 30 --timesteps 20000 --model-out models/ppo_referral
```

## 7) Evaluation RL vs heuristique

```bash
cd backend
python scripts/evaluate_rl.py --seed-demo --model-path models/ppo_referral.zip --episodes 30 --source C_LOCAL_A --speciality maternal --patients-per-episode 80 --wait-increment 3 --recovery-interval 5 --recovery-amount 2 --overload-penalty 30
```

La sortie est un JSON comparant:
- `rl.avg_reward_per_episode`
- `rl.avg_overloads_per_episode`
- `heuristic.avg_reward_per_episode`
- `heuristic.avg_overloads_per_episode`

## 8) Test rapide recommandation

Requete `POST /recommander`:

```json
{
  "patient_id": "P001",
  "current_centre_id": "C_LOCAL_A",
  "needed_speciality": "maternal",
  "severity": "medium"
}
```

## 9) Endpoints d'administration

### Centres
- `GET /centres`
- `POST /centres`
- `PUT /centres/{centre_id}`
- `DELETE /centres/{centre_id}`

Exemple `POST /centres`:

```json
{
  "id": "H_DISTRICT_2",
  "name": "Hopital District 2",
  "level": "secondary",
  "specialities": ["general", "maternal"],
  "capacity_available": 5,
  "estimated_wait_minutes": 25
}
```

### References
- `GET /references`
- `POST /references`
- `PUT /references/{reference_id}`
- `DELETE /references/{reference_id}`

Exemple `POST /references`:

```json
{
  "source_id": "C_LOCAL_A",
  "dest_id": "H_DISTRICT_2",
  "travel_minutes": 18
}
```

## Structure

- `backend/app/main.py`: entree FastAPI
- `backend/app/api/routes.py`: endpoints metier + administration
- `backend/app/services/graph_service.py`: chargement graphe depuis SQLite
- `backend/app/services/recommender.py`: logique de recommandation
- `backend/app/db/models.py`: schema SQLite
- `backend/app/rl/env.py`: environnement Gymnasium pour RL
- `backend/app/rl/heuristic_policy.py`: baseline heuristique
- `backend/app/rl/evaluation.py`: utilitaires de comparaison RL/heuristique
- `backend/scripts/seed_demo_data.py`: jeu de donnees initial
- `backend/scripts/simulate_batch.py`: simulation CLI multi-patients
- `backend/scripts/run_complex_scenarios.py`: benchmark multi-scenarios complexes
- `backend/scripts/summarize_scenarios.py`: synthese markdown classee pour pitch
- `backend/scripts/run_primary_demo.py`: scenario principal de demo
- `backend/scripts/train_rl.py`: entrainement PPO
- `backend/scripts/evaluate_rl.py`: evaluation PPO vs baseline
- `backend/tests/conftest.py`: fixtures partages pytest
- `backend/tests/test_admin_endpoints.py`: tests endpoints admin
- `backend/tests/test_recommender_endpoint.py`: tests endpoint `/recommander`
- `backend/tests/test_scoring_regression.py`: non-regression logique de score
- `backend/tests/test_equity_saturation.py`: scenarios d'equite/saturation

## Roadmap

1. Ajouter XAI (SHAP/LIME + traces metier lisibles)
2. Ajouter interface clinicien (dashboard parcours + explication)
3. Ajouter pipelines d'evaluation offline sur donnees reelles
