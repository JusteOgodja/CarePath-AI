# CarePath AI - Audit Complet Projet et Backend

## 1. Objectif du document
Ce document fournit une cartographie technique exhaustive du projet `CarePath AI` pour:
- comprendre la structure des fichiers,
- documenter la logique métier et les dépendances,
- décrire précisément les APIs et les flux,
- fournir une base exploitable par un générateur frontend (ex: Lovable).

Le focus est mis sur les éléments exécutables (code, scripts, API, tests, artefacts métier).  
Les fichiers de datasets volumineux sont inventoriés et documentés par type/famille.

---

## 2. Arborescence complète du projet (fichiers suivis hors `.git`, `.venv`, caches)

```text
.env.example
.gitignore
README.md
scripts/run_local_demo.py
frontend/streamlit_app.py
backend/requirements.txt
backend/app/__init__.py
backend/app/main.py
backend/app/api/__init__.py
backend/app/api/routes.py
backend/app/core/__init__.py
backend/app/core/config.py
backend/app/db/__init__.py
backend/app/db/models.py
backend/app/integrations/__init__.py
backend/app/integrations/healthsites_client.py
backend/app/integrations/who_gho_client.py
backend/app/rl/__init__.py
backend/app/rl/env.py
backend/app/rl/evaluation.py
backend/app/rl/heuristic_policy.py
backend/app/rl/random_policy.py
backend/app/services/__init__.py
backend/app/services/graph_service.py
backend/app/services/recommender.py
backend/app/services/schemas.py
backend/scripts/benchmark_policies_kenya.py
backend/scripts/build_edges_from_geo.py
backend/scripts/build_indicator_profile.py
backend/scripts/calc_catchment_population.py
backend/scripts/calibrate_capacity.py
backend/scripts/evaluate_rl.py
backend/scripts/fetch_who_gho.py
backend/scripts/find_isolated_centres.py
backend/scripts/import_facilities_from_file.py
backend/scripts/import_geofabrik_pois.py
backend/scripts/import_healthsites.py
backend/scripts/import_wdi_indicators.py
backend/scripts/init_db.py
backend/scripts/pipeline_kenya.py
backend/scripts/repair_isolated_edges.py
backend/scripts/run_complex_scenarios.py
backend/scripts/run_primary_demo.py
backend/scripts/seed_complex_data.py
backend/scripts/seed_demo_data.py
backend/scripts/simulate_batch.py
backend/scripts/summarize_scenarios.py
backend/scripts/train_rl.py
backend/scripts/validate_centres_quality.py
backend/tests/conftest.py
backend/tests/test_admin_endpoints.py
backend/tests/test_build_edges_from_geo.py
backend/tests/test_calc_catchment_population.py
backend/tests/test_calibrate_capacity.py
backend/tests/test_catchment_population_schema.py
backend/tests/test_equity_saturation.py
backend/tests/test_healthsites_import.py
backend/tests/test_import_facilities_from_file.py
backend/tests/test_import_geofabrik_pois.py
backend/tests/test_import_wdi_indicators.py
backend/tests/test_indicator_endpoints.py
backend/tests/test_random_baseline.py
backend/tests/test_recommender_endpoint.py
backend/tests/test_scoring_regression.py
backend/tests/test_who_gho_client.py
backend/models/*.zip (modèles PPO entraînés)
backend/docs/*.json, *.md (rapports de simulation/benchmark)
docs/arborescence_et_logique_projet.md
docs/architecture_analysis.md
docs/technicalite_projet_carepath_ai.md
data/Kenya/** (WorldPop, Geofabrik, WDI CSV ZIP/metadata)
data/WHO GHO/** (indicateurs WHO/WDI exportés)
```

---

## 3. Fiche détaillée par fichier (rôle, contenu, dépendances, interactions)

## 3.1 Racine projet

| Fichier | Rôle | Contenu | Dépendances | Interactions |
|---|---|---|---|---|
| `.env.example` | Exemple de config | Variables d’environnement (`DATABASE_URL`, `HEALTHSITES_API_KEY`, etc.) | Aucune | Référence pour exécution locale |
| `.gitignore` | Hygiène repo | Exclut DB locales, env, caches, artefacts | Git | Protège secrets et binaires |
| `README.md` | Guide opératoire | Installation, commandes pipeline/simulation/RL, workflow data réel | Décrit scripts | Guide utilisateur/dev |
| `scripts/run_local_demo.py` | Orchestrateur local | Init DB, seed, génération rapports, lancement API+Streamlit | `subprocess`, `uvicorn`, `streamlit` | Point d’entrée démo "one command" |

## 3.2 Frontend

| Fichier | Rôle | Contenu | Dépendances | Interactions |
|---|---|---|---|---|
| `frontend/streamlit_app.py` | UI de démonstration | Contrôles patient, visualisation graphe, recommandation locale, affichage KPI benchmark | `streamlit`, `pyvis`, `networkx`, SQLAlchemy models, `Recommender` | Lit DB locale (`centres`,`references`) et appelle directement la logique métier (`Recommender`) sans API HTTP |

## 3.3 Backend app (noyau)

| Fichier | Rôle | Contenu | Dépendances | Interactions |
|---|---|---|---|---|
| `backend/app/main.py` | Entrée FastAPI | `create_app()`, `init_db()`, montage du router | `fastapi`, `app.api.routes`, `app.db.models` | Point d’entrée `uvicorn app.main:app` |
| `backend/app/api/routes.py` | Contrôleurs HTTP | Endpoints santé, recommandation, CRUD centres/références, indicateurs | `fastapi`, `sqlalchemy`, `Recommender`, schémas Pydantic | Pont entre HTTP et services/DB |
| `backend/app/core/config.py` | Configuration | Récupère URL DB et variables API externes | `os`, `pathlib` | Utilisé par `db/models.py` et import Healthsites |
| `backend/app/db/models.py` | Modèle données + session | ORM SQLAlchemy, init schema, patch SQLite (`ALTER TABLE`) | `sqlalchemy`, config | Utilisé partout (API, services, scripts, tests) |
| `backend/app/services/graph_service.py` | Accès graphe | Charge `centres`/`references` en `nx.DiGraph`, shortest path, filtres | `networkx`, SQLAlchemy models | Utilisé par `Recommender`, RL env, scripts analyse graphe |
| `backend/app/services/recommender.py` | Logique métier principale | Scoring severity-aware, sélection destination, explication/rationale, score breakdown | `GraphService`, schémas | Utilisé par endpoint `/recommander`, `simulate_batch`, frontend offline |
| `backend/app/services/schemas.py` | Contrats données | Pydantic request/response API + structures explicabilité | `pydantic`, `typing` | Utilisé par routes, services, frontend local |
| `backend/app/rl/env.py` | Environnement RL (Gymnasium) | Définition état/action/récompense, surcharge, recovery, fairness penalty | `gymnasium`, `numpy`, `networkx`, `GraphService` | Utilisé par `train_rl.py`, `evaluate_rl.py`, benchmark |
| `backend/app/rl/evaluation.py` | Évaluation politiques | Évalue PPO/heuristique/random, calcule KPI (reward, wait, hhi, entropy) | `stable_baselines3`, policies | Utilisé par scripts d’évaluation/benchmark |
| `backend/app/rl/heuristic_policy.py` | Baseline heuristique RL | Choix action selon coût charge/attente | `dataclasses` | Utilisé dans `evaluation.py` |
| `backend/app/rl/random_policy.py` | Baseline aléatoire RL | Choix action aléatoire valide | `random` | Utilisé dans `evaluation.py` |
| `backend/app/integrations/healthsites_client.py` | Client API Healthsites v3 | Pagination `facilities`, extraction `results/features` | `httpx` | Utilisé par `import_healthsites.py` |
| `backend/app/integrations/who_gho_client.py` | Client WHO GHO | Récupération indicateurs, fallback query variants, sélection pays/année | `httpx` | Utilisé par `fetch_who_gho.py`, `calibrate_capacity.py` |

Fichiers `__init__.py` dans `app/*`: marquent les packages Python, sans logique métier.

## 3.4 Scripts backend (ops/data science/benchmark)

| Fichier | Rôle | Contenu | Dépendances | Interactions |
|---|---|---|---|---|
| `backend/scripts/init_db.py` | Init DB | Crée schéma SQLite | `app.db.models` | Prérequis de tous les scripts |
| `backend/scripts/seed_demo_data.py` | Seed minimal | Réseau de démo compact | ORM | Utilisé manuellement / tests |
| `backend/scripts/seed_complex_data.py` | Seed démo étendue | Réseau synthétique plus riche | `simulate_batch.seed_complex_data` | Utilisé démos/tests |
| `backend/scripts/simulate_batch.py` | Simulation principale | Génération patients (mix/severity), policy heuristic/random, fallback, shocks, KPI équité | `Recommender`, `GraphService`, ORM | Cœur des rapports scenario |
| `backend/scripts/run_complex_scenarios.py` | Runner scénarios | Exécute plusieurs configurations `simulate_batch` et agrège JSON | `simulate_batch` | Produit `scenario_report.json` |
| `backend/scripts/summarize_scenarios.py` | Rapport markdown | Classe scénarios (score composite avec fairness), écrit `md` | `json` | Produit `scenario_summary.md` |
| `backend/scripts/run_primary_demo.py` | Rapport primaire | Exécute scénario de référence unique | `simulate_batch` | Produit `primary_demo_report.json` |
| `backend/scripts/train_rl.py` | Entraînement PPO | Crée env RL, entraîne PPO, sauvegarde modèle zip | `stable_baselines3`, `ReferralEnv` | Produit modèles dans `backend/models` |
| `backend/scripts/evaluate_rl.py` | Évaluation RL 3-way | Compare PPO vs heuristic vs random sur même setup | `evaluation.py` | Sortie JSON console |
| `backend/scripts/benchmark_policies_kenya.py` | Benchmark production | Auto-choix source GEO, train if missing, ranking reward+composite, export JSON/MD | PPO + evaluation | Produit benchmark final utilisé UI |
| `backend/scripts/import_healthsites.py` | Import API Healthsites | Fetch paginé, mapping level/speciality, upsert centres (osm_type, osm_id) | client Healthsites + ORM | Ingestion données réelles |
| `backend/scripts/import_facilities_from_file.py` | Import fichier local | Parse CSV/GeoJSON HDX, inférences, upsert | csv/json + ORM | Alternative offline à Healthsites API |
| `backend/scripts/import_geofabrik_pois.py` | Import shapefile OSM | Lecture `.shp`, filtres `fclass`, mapping niveau/spécialités, rapport qualité | `pyshp`, ORM | Pipeline Kenya réel |
| `backend/scripts/build_edges_from_geo.py` | Génération références | K-nearest par niveau + travel time (Haversine/OSRM) | `httpx`, `math`, ORM | Construit table `references` |
| `backend/scripts/find_isolated_centres.py` | Diagnostic connectivité | Détecte centres isolés par spécialité | `networkx`, `GraphService` | Contrôle qualité graphe |
| `backend/scripts/repair_isolated_edges.py` | Réparation connectivité | Ajoute arêtes pour centres isolés (option OSRM/Haversine) | ORM + graph | Stabilise réseau réel |
| `backend/scripts/calc_catchment_population.py` | Population de bassin | Somme raster WorldPop dans rayon autour des centres | `rasterio`, `geopandas` | Alimente `catchment_population` |
| `backend/scripts/import_wdi_indicators.py` | Import indicateurs | Parse fichiers WDI, upsert dans `country_indicators` | csv + ORM | Input calibration |
| `backend/scripts/build_indicator_profile.py` | Profil pays dérivé | Extrait indicateurs latest + ratios recommandés case/severity mix | ORM | Input simulate/calibration |
| `backend/scripts/fetch_who_gho.py` | CLI WHO GHO | Test récupération indicateur WHO pour pays/année | client WHO | Validation source externe |
| `backend/scripts/calibrate_capacity.py` | Calibration capacité | Calcule `capacity_max/available` depuis beds per 10000 (manuel/WHO) | ORM + WHO client | Ajuste charge de soins |
| `backend/scripts/pipeline_kenya.py` | Pipeline E2E Kenya | Orchestre import geofabrik, catchment, indicators, capacity, edges, repair, simulation | subprocess scripts | Exécution reproductible locale |
| `backend/scripts/validate_centres_quality.py` | Audit qualité centres | Comptes par niveau, flags qualité mapping | ORM | Contrôle data quality |

## 3.5 Tests backend

| Fichier | Rôle | Ce qui est vérifié |
|---|---|---|
| `backend/tests/conftest.py` | Fixtures DB/test client | Init DB test, nettoyage tables, `TestClient` |
| `test_recommender_endpoint.py` | API métier | Réponses `/recommander` et structure payload |
| `test_scoring_regression.py` | Score métier | Non-régression formule scoring/severity |
| `test_admin_endpoints.py` | CRUD | Endpoints `/centres` et `/references` |
| `test_equity_saturation.py` | Robustesse routage | Comportement sous saturation/capacité nulle |
| `test_random_baseline.py` | Baseline random | Destination valide + distribution simulation |
| `test_healthsites_import.py` | Import API | Parsing/upsert Healthsites mocké |
| `test_import_facilities_from_file.py` | Import fichiers | Mapping GeoJSON/CSV |
| `test_import_geofabrik_pois.py` | Import shapefile | Filtres/mapping Geofabrik |
| `test_build_edges_from_geo.py` | Edges géographiques | Création références + temps trajet |
| `test_calc_catchment_population.py` | Catchment raster | Calcul population correct sur raster mock |
| `test_calibrate_capacity.py` | Calibration capacité | Formules et persistance DB |
| `test_catchment_population_schema.py` | Schéma DB | Présence/MAJ champ `catchment_population` |
| `test_import_wdi_indicators.py` | Indicateurs WDI | Parsing/upsert indicateurs |
| `test_indicator_endpoints.py` | API indicateurs | `/indicators` et `/indicators/latest` |
| `test_who_gho_client.py` | Client WHO | Robustesse fetch et sélection pays/année |

## 3.6 Artefacts/rapports et modèles

| Chemin | Rôle |
|---|---|
| `backend/models/*.zip` | Modèles PPO entraînés (versions itératives) |
| `backend/docs/final_benchmark_*.json/.md` | Résultats comparatifs PPO/heuristic/random |
| `backend/docs/scenario_report.json`, `scenario_summary.md` | Rapport scénarios batch |
| `backend/docs/primary_demo_report.json` | KPI scénario principal |
| `backend/docs/isolated_*.json` | Diagnostics/repair de connectivité |
| `backend/docs/indicator_profile.json` | Profil pays (ratios recommandés) |

## 3.7 Datasets (data/)

### Dossiers
- `data/Kenya/WorldPop Kenya 100m resolution/`
- `data/Kenya/Geofabrik/`
- `data/Kenya/Hospital Beds/`
- `data/Kenya/Medical Doctors/`
- `data/Kenya/Child Mortality/`
- `data/Kenya/Maternal Mortality/`
- `data/Kenya/Maternal Mortality Kenya/`
- `data/WHO GHO/...` (capacité, workforce, maternal, child, UHC)

### Rôle par type de fichier dataset
- `.tif`: raster population (WorldPop), utilisé par `calc_catchment_population.py`.
- `.shp/.shx/.dbf/.prj/.cpg`: composants shapefile Geofabrik OSM, utilisés par `import_geofabrik_pois.py`.
- `API_*.csv/.zip`: exports WDI/WHO GHO utilisés par `import_wdi_indicators.py` et analyses.
- `Metadata_*.csv`: dictionnaires/metadata indicateurs.

---

## 4. Architecture globale

## 4.1 Organisation backend

- Couche API (controllers): `backend/app/api/routes.py`
- Couche schémas (DTO): `backend/app/services/schemas.py`
- Couche métier:
  - `recommender.py` (choix destination + explicabilité)
  - `graph_service.py` (abstraction graphe)
  - `rl/*` (env RL + évaluation policies)
- Couche data:
  - `db/models.py` (ORM + session + migration légère SQLite)
  - scripts d’ingestion/calibration (sous `backend/scripts/`)
- Couche intégrations externes:
  - `integrations/healthsites_client.py`
  - `integrations/who_gho_client.py`

Il n’y a pas de middleware personnalisé complexe; le comportement repose sur FastAPI standard + validation Pydantic.

## 4.2 Flux d’exécution d’une requête typique (`POST /recommander`)

1. Requête JSON validée par `RecommandationRequest` (spécialité, sévérité, source).
2. `routes.recommander()` appelle `Recommender.recommend()`.
3. `Recommender` recharge le graphe via `GraphService.reload()`:
   - lit `centres` et `references` en DB,
   - construit `nx.DiGraph`.
4. Filtre candidats:
   - spécialité requise présente,
   - capacité > 0,
   - destination différente de la source.
5. Calcule shortest path (`travel_minutes`) pour chaque candidat.
6. Score métier:
   - `score = severity_weight * (travel + wait) / max(capacity,1)`.
7. Sélection du minimum score.
8. Retour `RecommandationResponse`:
   - destination, chemin, temps,
   - `score_breakdown`,
   - `explanation` et `rationale`.

## 4.3 Gestion des données

- Base relationnelle SQLite (`backend/carepath.db`).
- Modèle logique:
  - `centres`: nœuds du réseau (niveau, spécialités, capacité, wait, géo, tags, catchment).
  - `references`: arêtes orientées avec `travel_minutes`.
  - `country_indicators`: indicateurs agrégés par pays/année.
  - `patients`, `episodes`: tables de support prototype.
- Mise à jour schéma:
  - `init_db()` + `_ensure_sqlite_schema_updates()` (ALTER TABLE conditionnel).

## 4.4 Gestion d’erreurs

- Couche API:
  - erreurs métier `ValueError` converties en HTTP 400.
  - conflits CRUD en 404/409/400 selon cas.
- Scripts:
  - exceptions explicites (`FileNotFoundError`, `RuntimeError`, etc.),
  - sorties JSON/console pour diagnostic.
- Clients externes:
  - `raise_for_status()` + fallback de requêtes (WHO).

## 4.5 Authentification / sécurité

- **Aucune authentification active** sur les endpoints.
- Endpoints admin (`/centres`, `/references`) sont ouverts en local.
- Clés externes:
  - Healthsites via variable d’environnement (`HEALTHSITES_API_KEY`).
  - jamais hardcodées.

---

## 5. Endpoints backend (contrat détaillé)

## 5.1 Santé

| Méthode | Route | Description | Réponse |
|---|---|---|---|
| GET | `/health` | Statut API | `{ "status": "ok" }` |

## 5.2 Recommandation

### `POST /recommander`

Entrée:

```json
{
  "patient_id": "P001",
  "current_centre_id": "GEO_node_xxx",
  "needed_speciality": "maternal",
  "severity": "high"
}
```

Sortie (succès):

```json
{
  "patient_id": "P001",
  "destination_centre_id": "GEO_node_...",
  "destination_name": "Facility Name",
  "path": [{"centre_id":"...","centre_name":"...","level":"secondary"}],
  "estimated_travel_minutes": 24.0,
  "estimated_wait_minutes": 35.0,
  "score": 13.6,
  "explanation": "...",
  "rationale": "...",
  "score_breakdown": {
    "travel_minutes": 24.0,
    "wait_minutes": 35.0,
    "capacity_available": 6,
    "capacity_factor_used": 6.0,
    "severity": "high",
    "severity_weight": 1.7,
    "raw_cost_travel_plus_wait": 59.0,
    "final_score": 16.7
  }
}
```

Erreurs typiques (HTTP 400):
- réseau vide,
- aucune destination compatible,
- aucune destination atteignable.

## 5.3 Centres (admin)

| Méthode | Route | Rôle | Notes |
|---|---|---|---|
| GET | `/centres` | Liste centres | retourne subset champs UI |
| POST | `/centres` | Créer centre | 409 si id existe |
| PUT | `/centres/{centre_id}` | Modifier centre | 404 si absent |
| DELETE | `/centres/{centre_id}` | Supprimer centre | 409 si référencé par des liens |

## 5.4 Références (admin)

| Méthode | Route | Rôle | Notes |
|---|---|---|---|
| GET | `/references` | Liste liens | |
| POST | `/references` | Créer lien | source != dest, centres existants |
| PUT | `/references/{id}` | Modifier lien | validations identiques |
| DELETE | `/references/{id}` | Supprimer lien | 404 si absent |

## 5.5 Indicateurs

| Méthode | Route | Paramètres | Réponse |
|---|---|---|---|
| GET | `/indicators` | `country_code?`, `indicator_code?` | liste complète filtrée |
| GET | `/indicators/latest` | `country_code` (default `KEN`) | dernier point par indicateur |

---

## 6. Logique métier centrale

## 6.1 Scoring de recommandation

- Pondération sévérité:
  - `low=1.0`, `medium=1.3`, `high=1.7`.
- Formule:
  - `final_score = severity_weight * (travel + wait) / max(capacity, 1)`.
- Objectif:
  - minimiser score (temps + charge, adapté à criticité clinique).

## 6.2 Équité / concentration

Dans simulation et RL evaluation:
- `entropy_norm`: équilibre de distribution (plus haut = plus réparti).
- `hhi`: concentration des destinations (plus bas = moins concentré).

## 6.3 Simulation batch

- Génération patients:
  - source fixe ou pondérée par `catchment_population`,
  - case mix (`maternal/pediatric/general`) fixe ou mixte,
  - severity mix fixe ou mixte.
- Mécaniques dynamiques:
  - décrément capacité destination,
  - incrément wait,
  - recovery périodique,
  - shocks aléatoires optionnels.
- Fallback:
  - `none` ou `force_least_loaded`.

## 6.4 RL

- Environnement `ReferralEnv`:
  - état normalisé (capacités, waits, travel, progression épisode),
  - action: index destination,
  - récompense: coût (travel/wait) + surcharge + option fairness penalty.
- Évaluation unifiée PPO/heuristic/random:
  - reward, overloads, travel/wait, hhi/entropy, distribution destination.

---

## 7. Structures de données échangées

## 7.1 `centres` (logique)

Champs clés:
- `id`, `name`, `level`, `specialities`,
- `capacity_max`, `capacity_available`, `estimated_wait_minutes`,
- `lat`, `lon`, `osm_type`, `osm_id`, `raw_tags_json`,
- `catchment_population`.

## 7.2 `references`

- `id`,
- `source_id`, `dest_id`,
- `travel_minutes`.

## 7.3 `country_indicators`

- `country_code`, `indicator_code`, `year`, `value`,
- `indicator_name`, `source_file`, `metadata_json`.

---

## 8. Flux utilisateur principaux (pour design frontend)

## 8.1 Parcours Clinicien - Recommandation patient

1. Sélection centre source.
2. Choix spécialité requise.
3. Choix sévérité.
4. Lancement recommandation.
5. Visualisation:
   - destination,
   - chemin graphe,
   - temps travel/wait,
   - score breakdown + rationale.

## 8.2 Parcours Admin réseau

1. Ajouter/modifier/supprimer centres.
2. Ajouter/modifier/supprimer liens de référence.
3. Vérifier connectivité (isolés).

## 8.3 Parcours Data Ops (réel)

1. Import facilities (Geofabrik/Healthsites/CSV/GeoJSON).
2. Calcul catchment population (WorldPop).
3. Import indicateurs (WDI/WHO).
4. Calibration capacités.
5. Build + repair edges.
6. Simulation/benchmark.

---

## 9. Contraintes et règles importantes

- Pas d’auth API en l’état (usage local/hackathon).
- `specialities` stocké en CSV string en DB; conversion list<->string à gérer partout.
- Recommandation dépend de la connectivité graphe; absence de chemin => erreur 400.
- `capacity_available` doit rester >= 0.
- Pour `DELETE /centres`, suppression interdite si liens existants.
- Données réelles et démo peuvent coexister si pipeline n’efface pas explicitement.
- Le frontend offline lit directement SQLite; cohérence DB critique.

---

## 10. Recommandations frontend (alignées backend)

- Écran principal "Triage":
  - formulaire patient (source, spécialité, sévérité),
  - card résultat (destination, score),
  - panneau explicabilité (breakdown + rationale),
  - graphe interactif du parcours.
- Écran "Réseau":
  - table centres + filtres niveau/spécialités/capacité,
  - éditeur de liens.
- Écran "Performance":
  - KPIs simulation/benchmark (`reward`, `wait`, `travel`, `entropy`, `hhi`),
  - comparaison policies.
- Écran "Data Ops":
  - suivi pipeline, qualité mapping, isolés, artefacts générés.

---

## 11. Dépendances principales (backend)

- API/backend: `fastapi`, `pydantic`, `sqlalchemy`, `uvicorn`.
- Graph & simulation: `networkx`.
- RL: `gymnasium`, `stable-baselines3`, `numpy`.
- Geodata: `rasterio`, `geopandas`, `shapely`, `pyshp`.
- HTTP externes: `httpx`.
- Tests: `pytest`.

---

## 12. Synthèse exécutive

Le backend `CarePath AI` est structuré en couches claires:
- API REST + schémas contractuels,
- moteur métier de recommandation explicable severity-aware,
- pipeline data réel reproductible (Kenya),
- moteur simulation/benchmark avec métriques de fairness,
- capacité RL opérationnelle et comparée à des baselines.

Le système est adapté à une interface frontend moderne orientée:
- aide à la décision clinique,
- administration réseau,
- pilotage de performance et équité.

