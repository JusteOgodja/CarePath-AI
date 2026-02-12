# Arborescence du projet CarePath AI et logique de chaque fichier

Ce document decrit la structure actuelle du repository, le role de chaque fichier, et la logique globale du systeme.

## 1) Vue logique du systeme

Le projet est compose de 5 blocs:

1. `backend/app`: coeur applicatif (API FastAPI, modele DB, moteur de recommandation, graphe, RL, integrations externes).
2. `backend/scripts`: operations (seed, import donnees reelles, simulation, benchmark, entrainement/evaluation RL).
3. `backend/tests`: tests unitaires/fonctionnels.
4. `frontend`: UI Streamlit pour demo live.
5. `scripts` (racine): orchestration one-command locale.

Flux principal:
- Donnees centres + references en SQLite.
- `GraphService` construit un graphe dirige NetworkX.
- `Recommender` choisit une destination en minimisant un score (trajet + attente + capacite + severite).
- API expose `/recommander` et CRUD admin.
- Scripts permettent simulation/scenarios, import Healthsites, construction d'edges geo, RL.

---

## 2) Arborescence et role de chaque fichier

## Racine

- `README.md`
  - Guide d'utilisation: installation, API, Streamlit, simulation, RL, import Healthsites, tests.

- `.env.example`
  - Variables d'environnement modele (`DATABASE_URL`, `HEALTHSITES_API_KEY`, `HEALTHSITES_BASE_URL`).

- `docs/architecture_analysis.md`
  - Analyse d'architecture et priorites techniques.

- `docs/technicalite_projet_carepath_ai.md`
  - Documentation technique detaillee de l'etat du projet.

- `scripts/run_local_demo.py`
  - Orchestrateur local: reset/init, seed, generation rapports, lancement API + Streamlit.

## Frontend

- `frontend/streamlit_app.py`
  - Interface demo live:
    - recupere centres/references via API,
    - visualise le graphe,
    - envoie des requetes `/recommander`,
    - affiche chemin, rationale, score_breakdown, KPI scenario.

## Backend (global)

- `backend/requirements.txt`
  - Dependances Python du backend (FastAPI, SQLAlchemy, NetworkX, RL, Streamlit, tests, etc.).

- `backend/carepath.db`
  - Base SQLite locale (runtime).

## Backend / app

- `backend/app/__init__.py`
  - Marqueur package Python.

### app/core

- `backend/app/core/__init__.py`
  - Marqueur package.

- `backend/app/core/config.py`
  - Lecture config par variables d'environnement:
    - `DATABASE_URL`
    - `HEALTHSITES_API_KEY`
    - `HEALTHSITES_BASE_URL`

### app/db

- `backend/app/db/__init__.py`
  - Marqueur package.

- `backend/app/db/models.py`
  - Schema SQLAlchemy + engine/session.
  - Tables:
    - `centres`
    - `references`
    - `patients`
    - `episodes`
  - Champs centres etendus pour donnees reelles:
    - `lat/lon`, `osm_type/osm_id`, `raw_tags_json`, `capacity_max`, etc.
  - `init_db()` + mise a jour schema SQLite safe (ajout colonnes/index si besoin).

### app/integrations

- `backend/app/integrations/__init__.py`
  - Marqueur package.

- `backend/app/integrations/healthsites_client.py`
  - Client API Healthsites v3:
    - appels HTTP,
    - pagination,
    - filtres (`country`, `extent`, `from/to`, etc.),
    - extraction `results/features`.

### app/api

- `backend/app/api/__init__.py`
  - Marqueur package.

- `backend/app/api/routes.py`
  - Endpoints FastAPI:
    - `GET /health`
    - `POST /recommander`
    - CRUD `centres`
    - CRUD `references`
  - Validation metier basique et mapping erreurs -> HTTP.

### app/services

- `backend/app/services/__init__.py`
  - Marqueur package.

- `backend/app/services/schemas.py`
  - Schemas Pydantic request/response API.
  - Inclut `score_breakdown` et `rationale` pour explicabilite.

- `backend/app/services/graph_service.py`
  - Charge centres/references depuis DB.
  - Construit `nx.DiGraph` et expose:
    - destinations candidates,
    - plus court chemin,
    - acces attributs noeud.

- `backend/app/services/recommender.py`
  - Coeur heuristique de recommandation.
  - Logique score (severity + travel + wait + capacity).
  - Produit explication textuelle + decomposition de score.

### app/rl

- `backend/app/rl/__init__.py`
  - Marqueur package.

- `backend/app/rl/env.py`
  - Environnement Gymnasium (`ReferralEnv`) pour RL.
  - Etat/action/reward sur capacites, attentes, surcharge.

- `backend/app/rl/heuristic_policy.py`
  - Policy baseline heuristique (regles deterministes).

- `backend/app/rl/random_policy.py`
  - Policy baseline aleatoire (comparaison scientifique).

- `backend/app/rl/evaluation.py`
  - Evaluation unifiee des policies (PPO/heuristic/random) avec memes metriques.

### app/main

- `backend/app/main.py`
  - Point d'entree FastAPI (`app` + router).

## Backend / scripts

- `backend/scripts/init_db.py`
  - Initialisation DB.

- `backend/scripts/seed_demo_data.py`
  - Seed reseau demo (petit graphe).

- `backend/scripts/seed_complex_data.py`
  - Seed reseau complexe (plus realiste).

- `backend/scripts/import_healthsites.py`
  - Import Healthsites v3 -> `centres` (upsert par `(osm_type, osm_id)`).
  - Mapping deterministic level/specialities/capacites/attente.

- `backend/scripts/build_edges_from_geo.py`
  - Construction `references` a partir de coords geo:
    - primary->secondary,
    - secondary->tertiary,
    - alternatives optionnelles,
    - `travel_minutes` via haversine + vitesse moyenne.

- `backend/scripts/simulate_batch.py`
  - Simulation multi-patients (heuristic/random + fallback + shock).
  - KPI: success/failure/fallback, avg travel/wait/score, entropy_norm, HHI.

- `backend/scripts/run_complex_scenarios.py`
  - Execute plusieurs scenarios standardises et sort un rapport JSON consolide.

- `backend/scripts/summarize_scenarios.py`
  - Lit le rapport scenarios et genere un resume Markdown classe (avec fairness).

- `backend/scripts/run_primary_demo.py`
  - Lance le scenario principal de demo et exporte un rapport JSON.

- `backend/scripts/train_rl.py`
  - Entrainement PPO sur `ReferralEnv`.

- `backend/scripts/evaluate_rl.py`
  - Comparaison PPO vs Heuristic vs Random sur memes seeds/config.

## Backend / tests

- `backend/tests/conftest.py`
  - Fixtures pytest (DB test, nettoyage, client FastAPI).

- `backend/tests/test_admin_endpoints.py`
  - Tests CRUD centres/references.

- `backend/tests/test_recommender_endpoint.py`
  - Tests endpoint `/recommander` + payload explicable.

- `backend/tests/test_scoring_regression.py`
  - Non-regression formule score et choix destination.

- `backend/tests/test_equity_saturation.py`
  - Scenarios saturation/equilibre sur flux patients.

- `backend/tests/test_random_baseline.py`
  - Validation baseline random en simulation.

- `backend/tests/test_healthsites_import.py`
  - Test import Healthsites mocke (parse + upsert).

- `backend/tests/test_build_edges_from_geo.py`
  - Test creation d'edges geo + travel time.

## Backend / artefacts runtime

- `backend/models/ppo_referral.zip`
- `backend/models/ppo_referral_v2.zip`
- `backend/models/ppo_referral_v3.zip`
  - Modeles PPO entraines.

- `backend/docs/scenario_report.json`
  - Rapport brut multi-scenarios.

- `backend/docs/scenario_summary.md`
  - Synthese lisible du benchmark scenarios.

- `backend/docs/primary_demo_report.json`
  - Resultat scenario principal demo.

---

## 3) Logique globale (du point de vue execution)

1. Initialiser DB (`init_db.py`) et charger des donnees (seed ou import Healthsites).
2. Construire les edges (`build_edges_from_geo.py`) si donnees reelles importees.
3. Lancer API (`uvicorn app.main:app --reload`).
4. Recommandation:
   - API recoit `current_centre_id + speciality + severity`.
   - `GraphService` charge le graphe depuis DB.
   - `Recommender` calcule les candidats, score, chemin optimal.
   - Retourne destination + explication + score_breakdown.
5. Simulation/benchmark:
   - `simulate_batch.py` et `run_complex_scenarios.py` mesurent robustesse/equite.
6. RL:
   - `train_rl.py` entraine PPO.
   - `evaluate_rl.py` compare PPO/heuristic/random.
7. Demo live:
   - `frontend/streamlit_app.py` visualise graphe + parcours + KPI.
   - `scripts/run_local_demo.py` automatise toute la chaine.

---

## 4) Pourquoi cette architecture est maintenable

- Separation claire entre:
  - logique metier (`services`),
  - transport API (`api`),
  - persistance (`db`),
  - experimentations (`scripts`),
  - presentation (`frontend`).
- Scripts autonomes pour operations hackathon/reproductibles.
- Tests couvrant endpoints, scoring, scenarios et nouveaux imports data reelles.
- Config centralisee par env vars (pas de secrets hardcodes).
