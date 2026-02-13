# CarePath AI

Prototype local (100% gratuit) pour l'optimisation des parcours de reference patient:
- API FastAPI (recommandation + admin reseau)
- Graphe de soins (NetworkX)
- Simulation de scenarios + KPI equite (entropy_norm, HHI)
- Comparaison PPO vs Heuristic vs Random
- Frontend React/Vite dans `frontend`

## Installation

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Installation minimale API (sans stack RL/data):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements/base.txt -r requirements/dev.txt
```

Config locale (`.env.example`):
- `DATABASE_URL` (defaut: `sqlite:///./carepath.db`)
- `APP_ENV` (`development`/`production`)
- `AUTH_SECRET_KEY` (signature des tokens)
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` (RBAC admin)
- `VIEWER_USERNAME` / `VIEWER_PASSWORD` (lecture seule)

## API Backend

```bash
cd backend
python scripts/init_db.py
python scripts/seed_demo_data.py
uvicorn app.main:app --reload
```

Migrations (Alembic):

```bash
cd backend
python scripts/migrate.py
```

Docs API: `http://127.0.0.1:8000/docs`

### Endpoint metier
- `POST /api/v1/auth/login` (retourne un token bearer)
- `POST /api/v1/recommander`
  - utilise `severity` dans le score
  - renvoie `rationale` + `score_breakdown`
- `GET /api/v1/health` (status + database + schema revision + time)
- `GET /api/v1/indicators?country_code=KEN`
- `GET /api/v1/indicators/latest?country_code=KEN`
- `POST/PUT/DELETE /api/v1/centres` et `/api/v1/references` (role `admin` requis)

Observabilité/robustesse runtime:
- `X-Request-ID` injecté sur chaque réponse
- logs backend structurés JSON (requêtes + erreurs)
- payload d’erreur standardisé (`detail` + `error{code,message,request_id,...}`)
- rate limit mémoire:
  - `/api/v1/auth/login`: 10 req / 60s / IP
  - écritures admin: 60 req / 60s / IP

## Frontend React (frontend)

Depuis la racine du projet:

```bash
cd frontend
npm install
npm run dev
```

Fonctions:
- Triage patient + recommandation
- Gestion réseau (centres/références)
- Indicateurs de santé
- Graphe réseau 3D interactif (zoom, rotation, survol)

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

## Real data import (Healthsites API v3)

1. Configure env vars (do not hardcode API key):

```bash
cp .env.example .env
# then set HEALTHSITES_API_KEY in your shell
```

PowerShell example:

```powershell
$env:HEALTHSITES_API_KEY=\"YOUR_KEY\"
$env:HEALTHSITES_BASE_URL=\"https://healthsites.io\"
```

2. Import facilities into `centres` (upsert by `(osm_type, osm_id)`):

```bash
cd backend
python scripts/import_healthsites.py --country=CM --output=json --flat-properties=true --tag-format=osm --max-pages=5
```

Optional filters:
- `--extent=minLng,minLat,maxLng,maxLat`
- `--from=YYYY-MM-DD`
- `--to=YYYY-MM-DD`
- `--output=json|geojson`

3. Build referral references from imported geo coordinates:

```bash
python scripts/build_edges_from_geo.py --k-nearest=2 --speed-kmh=40
```

4. Run API and test recommendation:

```bash
uvicorn app.main:app --reload
```

Healthsites mapping rules implemented:
- Level:
  - hospital / tertiary-like => `tertiary`
  - clinic / health_center => `secondary`
  - dispensary / health_post => `primary`
  - unknown => `primary`
- Specialities:
  - maternity/obstetric-like tags => include `maternal`
  - pediatric/children-like tags => include `pediatric`
  - always fallback to `general` if nothing detected
- Defaults by level:
  - `capacity_max`: primary=10, secondary=30, tertiary=120
  - `capacity_available`: initialized to `capacity_max`
  - `estimated_wait_minutes`: primary=15, secondary=30, tertiary=60

## Tests

```bash
cd backend
pytest -q
```

## Qualité / CI

- CI GitHub Actions:
  - `.github/workflows/ci.yml` (backend + frontend)
  - `.github/workflows/secret-scan.yml` (gitleaks)
- Check local one-shot:

```powershell
.\scripts\check.ps1
```

Couverture inclut:
- CRUD admin
- `/recommander` + payload explicable
- regression scoring + effet severity
- random baseline valide
- equite/saturation
- import Healthsites mocke + upsert
- construction d'edges geo + travel_minutes

## Offline public datasets workflow (HDX + WorldPop + WHO/DHS indicators)

Prerequisites (download locally first):
- HDX / Global Healthsites Mapping Project facilities file (`.geojson` or `.csv`)
- WorldPop population raster (`.tif`)
- WDI/WHO indicator files for hospital beds, physicians, maternal mortality, under-5 mortality
- Optional: DHS-informed ratios for maternal/pediatric demand and severity distribution

All processing runs locally and offline once files are downloaded.

### 1) Import facilities from local file (HDX/Healthsites export)

```bash
cd backend
python scripts/import_facilities_from_file.py --input data/facilities.geojson --format geojson
```

CSV example:

```bash
python scripts/import_facilities_from_file.py --input data/facilities.csv --format csv --lat-column latitude --lon-column longitude --name-column name --facility-type-column facility_type
```

Option Geofabrik (shapefile POI):

```bash
python scripts/import_geofabrik_pois.py --input-shp "data/kenya/Geofabrik/gis_osm_pois_free_1.shp" --include-fclass hospital,clinic,doctors,dentist --exclude-empty-name
```

Optional quality report during import:

```bash
python scripts/import_geofabrik_pois.py --input-shp "data/kenya/Geofabrik/gis_osm_pois_free_1.shp" --include-fclass hospital,clinic,doctors,dentist --exclude-empty-name --quality-report docs/geofabrik_import_quality.json
```

### 2) Compute catchment population from WorldPop raster

```bash
python scripts/calc_catchment_population.py --raster data/worldpop.tif --radius-km 10
```

### 3) Import country indicators (WDI CSV)

```bash
python scripts/import_wdi_indicators.py --input-dir data/kenya --country-code KEN --latest-only
python scripts/build_indicator_profile.py --country-code KEN --output docs/indicator_profile.json
```

### 4) Calibrate capacities from beds/10,000 population

```bash
python scripts/calibrate_capacity.py --beds-per-10000 18 --availability-ratio 0.8
```

Option WHO GHO (API publique):

```bash
python scripts/fetch_who_gho.py --indicator HWF_0000 --country CM
python scripts/calibrate_capacity.py --who-indicator HWF_0000 --who-country CM --availability-ratio 0.8
```

Option annee precise:

```bash
python scripts/calibrate_capacity.py --who-indicator HWF_0000 --who-country CM --who-year 2021
```

### 5) Build referral edges from coordinates

```bash
python scripts/build_edges_from_geo.py --k-nearest 2 --speed-kmh 40 --bidirectional
```

Optional local OSRM:

```bash
python scripts/build_edges_from_geo.py --k-nearest 2 --osrm-server http://127.0.0.1:5000 --bidirectional
```

### 6) Run simulation with population-weighted patient generation

```bash
python scripts/simulate_batch.py --patients 200 --policy heuristic --sample-source-by-catchment --case-mix-mode mixed --maternal-ratio 0.35 --pediatric-ratio 0.25 --general-ratio 0.40 --severity-mode mixed --severity-low-ratio 0.60 --severity-medium-ratio 0.30 --severity-high-ratio 0.10
```

You can reuse the recommended ratios generated in `docs/indicator_profile.json`.

Validate data quality in DB:

```bash
python scripts/validate_centres_quality.py --output docs/centres_quality_report.json
```

### 7) One-command Kenya pipeline

```bash
python scripts/pipeline_kenya.py --reset-db
```

This executes the full local Kenya workflow end-to-end:
- DB init/reset
- Geofabrik POI import
- WorldPop catchment population
- WDI indicators import + indicator profile build
- Capacity calibration
- Edge build + isolated-centre repair
- Final simulation sanity check

### 8) Kenya 3-policy benchmark (Random vs Heuristic vs PPO)

```bash
python scripts/benchmark_policies_kenya.py --train-if-missing --timesteps 6000 --episodes 20 --output-json docs/final_benchmark_kenya.json --output-md docs/final_benchmark_kenya.md
```

This generates a comparable benchmark with the same environment settings for all three methods.

Recommended tuned baseline (v3):

```bash
python scripts/benchmark_policies_kenya.py --train-if-missing --timesteps 120000 --episodes 40 --model-path models/ppo_referral_kenya_mapped_v3.zip --travel-weight 1.1 --wait-weight 1.0 --fairness-penalty 6 --ent-coef 0.015 --output-json docs/final_benchmark_kenya_mapped_v3.json --output-md docs/final_benchmark_kenya_mapped_v3.md
```

Current recommendation for demo:
- model: `models/ppo_referral_kenya_mapped_v3.zip`
- benchmark report: `backend/docs/final_benchmark_kenya_mapped_v3.json`

Privacy note:
- The workflow uses aggregated public datasets (facilities and gridded population).
- No individual-level or identifiable patient data is required.
- Outputs are planning-oriented indicators, not personal medical records.
