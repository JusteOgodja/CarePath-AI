# CarePath AI - Dossier Technique Complet (Deep Dive)

## 1) Objectif du projet

CarePath AI est une plateforme d'aide a la decision pour orienter des patients dans un reseau de soins (centres primaires, secondaires, tertiaires) en minimisant les delais et en tenant compte de la capacite reelle des etablissements.

Le systeme combine:
- un moteur de recommandation base sur un graphe de references,
- une logique heuristique interpretable,
- un agent d'apprentissage par renforcement (RL, PPO) pour des politiques adaptatives,
- une interface frontend pour les utilisateurs metier (triage, supervision, administration),
- un pipeline de donnees reel (Kenya) pour calibrer le reseau.

En pratique, le projet vise a repondre a ces questions:
- Vers quel hopital faut-il transferer ce patient maintenant?
- Quel est le compromis entre temps de trajet, attente et saturation?
- Le systeme de references est-il equitable, robuste et scalable?

---

## 2) Vue d'ensemble architecture

### 2.1 Couches principales

- Backend API: FastAPI (`backend/app/main.py`) expose les routes metier sous `/api/v1`.
- Moteur decisionnel: service de recommandation (`backend/app/services/recommender.py`) appuye par un graphe (`graph_service.py`).
- RL: environnement Gymnasium (`backend/app/rl/env.py`) + entrainement/evaluation via scripts (`backend/scripts/train_rl.py`, `evaluate_rl.py`).
- Data pipeline: ingestion/normalisation/capacite/edges a partir de donnees geospatiales et indicateurs (`backend/scripts/pipeline_kenya.py` et scripts associes).
- Frontend: React + Vite + TypeScript (`frontend/`) avec pages de triage, admin reseau, referrals, graphe, indicateurs, systeme.
- Persistance: SQLite par defaut (`backend/carepath.db`), modele SQLAlchemy + migrations Alembic.

### 2.2 Style architectural

Architecture modulaire "monorepo":
- separation claire UI/API/services/scripts,
- logique metier concentree dans les services backend,
- scripts de data engineering decouples des routes runtime,
- frontend consomme exclusivement les endpoints backend via un client API central.

---

## 3) Structure de fichiers (lecture guidee)

### 3.1 Backend

- `backend/app/main.py`: creation app FastAPI, CORS, middleware, erreurs, init DB.
- `backend/app/api/v1/router.py`: assemblage des routeurs.
- `backend/app/api/v1/routers/`:
  - `health.py`: statut systeme.
  - `recommendation.py`: endpoint de recommandation.
  - `centres.py`, `references.py`: CRUD reseau.
  - `auth.py`: login JWT/roles.
  - `referral_workflow.py`: workflow des demandes de transfert.
  - `indicators.py`: lecture indicateurs pays.
- `backend/app/services/`:
  - `graph_service.py`: charge le reseau depuis DB vers NetworkX.
  - `recommender.py`: coeur de scoring/recommandation.
  - `schemas.py`: schemas Pydantic (requests/responses).
- `backend/app/rl/`:
  - `env.py`: environnement RL.
  - `heuristic_policy.py`, `random_policy.py`: baselines.
  - `evaluation.py`: metriques comparatives.
- `backend/app/db/models.py`: modeles SQLAlchemy, moteur, sessions.
- `backend/app/core/`: config, auth, rate limiting, middleware, logging.
- `backend/scripts/`: pipelines data, simulations, benchmarks, entrainement RL.
- `backend/docs/`: rapports JSON/MD generes (benchmarks, qualite, isolements).
- `backend/models/`: modeles PPO entraines (`*.zip`).

### 3.2 Frontend

- `frontend/src/App.tsx`: routing + providers (auth, i18n, react-query).
- `frontend/src/lib/api/client.ts`: client HTTP central, timeout, gestion erreurs, token bearer.
- `frontend/src/lib/api/endpoints.ts`: catalogue des appels API metier.
- `frontend/src/pages/`: ecrans fonctionnels (`Triage`, `AdminNetwork`, `Referrals`, `NetworkGraph`, `Indicators`, `System`, `Login`).
- `frontend/src/components/`: composants UI + metier (triage, admin, indicateurs, shell).
- `frontend/index.html`: metadonnees page (titre `CarePath AI`, favicon).

---

## 4) Modele de donnees (backend)

Definition principale dans `backend/app/db/models.py`.

### 4.1 Entites coeur reseau

- `centres`
  - `id` (PK)
  - `name`
  - `lat`, `lon`
  - `level` (primary/secondary/tertiary)
  - `specialities` (liste serialisee)
  - `capacity_max`, `capacity_available`
  - `estimated_wait_minutes`
  - `catchment_population`
  - `osm_type`, `osm_id`, `raw_tags_json` pour tracabilite geodata

- `references`
  - `id` (PK)
  - `source_id` -> `centres.id`
  - `dest_id` -> `centres.id`
  - `travel_minutes`

### 4.2 Workflow de transfert

- `referral_requests`
  - identite patient/source/specialite/severite
  - destination proposee puis acceptee
  - statut (`pending`, `accepted`, `in_transit`, `completed`, etc.)
  - notes et feedback clinique (`diagnosis`, `treatment`, `followup`)
  - horodatage complet (`created_at`, `updated_at`, `closed_at`)

### 4.3 Autres tables

- `country_indicators`: indicateurs sanitaires imports (WDI/WHO) par pays/annee.
- `patients`, `episodes`: artefacts historisation/simulation.

---

## 5) Logique metier de recommandation

Fichier cle: `backend/app/services/recommender.py`.

### 5.1 Etapes de calcul

1. Charger le graphe en memoire (`GraphService.reload()`).
2. Lister destinations candidates compatibles specialite.
3. Exclure le centre source lui-meme.
4. Calculer le plus court chemin (Dijkstra/NetworkX) vers chaque destination atteignable, poids = `travel_minutes`.
5. Evaluer un score par destination.
6. Selectionner la meilleure selon politique (`heuristic`, `rl`, `auto`).
7. Retourner une reponse explicable (path, score breakdown, rationale, policy used).

### 5.2 Formule de score heuristique

Poids severite:
- low = 1.0
- medium = 1.3
- high = 1.7

Formule exacte:

```text
capacity_factor = max(capacity_available, 1)
raw_cost = travel_minutes + wait_minutes
final_score = severity_weight * raw_cost / capacity_factor
```

Interpretation:
- Plus `travel` et `wait` sont eleves, plus le score augmente (moins bon).
- Plus la capacite dispo est elevee, plus le score baisse (meilleur).
- Les cas severes amplifient le cout via `severity_weight`.

### 5.3 Politique de routage

- `heuristic`: prend `min(score)`.
- `rl`: charge un modele PPO (`RL_MODEL_PATH` ou default `backend/models/ppo_referral.zip`) et predit une action.
- `auto`: tente RL puis bascule en heuristique si modele indisponible/erreur, avec `fallback_reason`.

---

## 6) Graphe de references

Fichier cle: `backend/app/services/graph_service.py`.

Representation:
- Noeuds = centres de sante avec attributs de capacite, niveau, specialites, attente.
- Aretes orientees = routes de reference avec cout `travel_minutes`.

Operations critiques:
- `candidate_destinations(speciality)`: destinations admissibles.
- `shortest_path(source, target)`: meilleur trajet en temps de voyage.
- `node(id)`: lecture des attributs centre.

Cette couche assure que la recommandation exploite un reseau structure et non une simple liste plate d'hopitaux.

---

## 7) Apprentissage par renforcement (RL)

### 7.1 Environnement

Fichier: `backend/app/rl/env.py`.

- Type: `gymnasium.Env`
- Action: destination index (`Discrete(n_destinations)`).
- Observation (normalisee):

```text
[capacities..., waits..., travel_times..., step_ratio]
```

avec taille `3*n_dest + 1`.

### 7.2 Dynamique de l'etat

A chaque patient (step):
- choix destination,
- si capacite > 0: capacite diminue de 1,
- attente destination augmente (`wait_increment`),
- recuperation periodique optionnelle:
  - capacite + `recovery_amount` (bornee a initiale),
  - attente diminue.

### 7.3 Fonction de recompense (formules)

Variables:
- `travel`, `wait`, `cap`
- `travel_weight`, `wait_weight`
- `overload_penalty`
- `fairness_penalty`
- `reward_scale`

Formule:

```text
base_cost = travel_weight*travel + wait_weight*wait
reward = -(base_cost / reward_scale)

if cap <= 0:
    reward -= overload_penalty / reward_scale

if fairness_penalty > 0:
    share = destination_counts[action] / max(total_before, 1)
    reward -= (fairness_penalty * share) / reward_scale
```

Objectif implicite:
- minimiser cout trajet+attente,
- eviter surcharge,
- encourager une distribution plus equilibree (equite) si penalite fairness activee.

### 7.4 Entrainement

Script: `backend/scripts/train_rl.py`.

Hyperparametres PPO (par defaut):
- `learning_rate = 3e-4`
- `gamma = 0.99`
- `n_steps = 256`
- `batch_size = 64`
- `ent_coef = 0.01`
- `timesteps` configurable

Sortie: modele zip dans `backend/models/`.

### 7.5 Evaluation

Scripts/fichiers:
- `backend/scripts/evaluate_rl.py`
- `backend/app/rl/evaluation.py`

Metriques principales:
- `avg_reward_per_episode`
- `avg_overloads_per_episode`
- `avg_travel`
- `avg_wait`
- `fallback_rate` (ici surcharge/overload rate)
- `entropy_norm` (equilibre distribution)
- `hhi` (concentration, plus bas = mieux)
- distribution par destination

---

## 8) Pipeline de donnees reelles (Kenya)

Orchestration: `backend/scripts/pipeline_kenya.py`.

Sequence standard:
1. Initialiser DB (`init_db.py`).
2. Importer etablissements depuis Geofabrik OSM (`import_geofabrik_pois.py`).
3. Calculer population de catchment depuis raster WorldPop (`calc_catchment_population.py`).
4. Importer indicateurs WDI (`import_wdi_indicators.py`).
5. Construire profil indicateurs (`build_indicator_profile.py`).
6. Calibrer capacites (`calibrate_capacity.py`).
7. Construire edges geographiques (`build_edges_from_geo.py`).
8. Reparer centres isoles (`repair_isolated_edges.py`) et verifier (`find_isolated_centres.py`).
9. Lancer une simulation sanity-check (`simulate_batch.py`).

### 8.1 Sources et nature des donnees

- Geofabrik / OSM POIs: localisation et typologie etablissements.
- WorldPop: population geospatiale pour catchment.
- WDI/WHO: indicateurs macro pour calibration scenario (case mix, severity mix, capacite).

### 8.2 Donnees "reelles" vs "demo"

Le code contient des seeders demo (utile pour test local), mais le pipeline Kenya permet de construire un reseau a partir de donnees externes importees et transformees.

Quand la DB est alimentee par `pipeline_kenya.py`, les calculs de recommandation utilisent ces donnees chargees dans `centres` et `references` (pas uniquement les seeders demo).

---

## 9) Benchmarking et rapports

### 9.1 Benchmark politiques

Script: `backend/scripts/benchmark_policies_kenya.py`

Compare typiquement:
- PPO (RL)
- Heuristic
- Random

Calcule un score compose (normalise/pondere) integrant:
- reward
- travel
- wait
- hhi
- entropy gap (1 - entropy)
- overloads

Artefacts produits:
- JSON + Markdown dans `backend/docs/`.

### 9.2 Notebook

Le notebook `notebooks/model_benchmark_report.ipynb` sert a presenter et visualiser les resultats des modeles/politiques.

Pour garantir la validite "donnees reelles", il faut verifier la provenance des fichiers charges dans le notebook (ex: rapports `*_kenya*.json` issus pipeline/benchmark reelles) et pas uniquement des artefacts de test demo.

---

## 10) API backend (contrat fonctionnel)

Prefix global: `/api/v1`.

Endpoints majeurs:
- `POST /auth/login`
- `GET /health`
- `POST /recommander`
- CRUD `centres`
- CRUD `references`
- `GET /indicators`, `GET /indicators/latest`
- Workflow referrals:
  - `GET /referrals/requests`
  - `POST /referrals/requests`
  - `POST /referrals/requests/{id}/accept`
  - `POST /referrals/requests/{id}/start-transfer`
  - `POST /referrals/requests/{id}/complete`
  - `POST /referrals/requests/{id}/reject`
  - `POST /referrals/requests/{id}/cancel`

Ces routes sont mappees dans `frontend/src/lib/api/endpoints.ts`.

---

## 11) Frontend: logique applicative

### 11.1 Stack

- React + TypeScript + Vite
- React Router pour navigation
- TanStack Query pour data fetching/cache
- UI components + pages metier

### 11.2 Flux technique principal

- `apiFetch()` construit URL (`VITE_API_BASE_URL` ou `http://localhost:8000/api/v1`), ajoute timeout, JSON headers, token bearer.
- Pages utilisent `useQuery` / `useMutation` pour appeler `endpoints.ts`.
- Les erreurs API sont harmonisees via `ApiClientError`.
- Auth stocke/relit token et protege les routes admin via `ProtectedRoute`.
- I18n FR/EN via provider `useI18n` et bascule de langue dans shell.

### 11.3 Parcours utilisateur

- Login -> obtention token.
- Triage -> saisie patient/source/specialite/severite -> appel `POST /recommander` -> affichage destination + explications.
- Admin reseau -> gestion centres/references.
- Referrals -> gestion cycle transfert.
- Network Graph -> visualisation topologie.
- Indicators -> exploration indicateurs pays.
- System -> monitoring health API.

---

## 12) Securite et gouvernance technique

### 12.1 Mecanismes presents

- JWT (auth backend) + roles (`admin`, `viewer`).
- Verification credentials en comparaison constante (`hmac.compare_digest`).
- Rate limit sur login (anti brute-force basique).
- Validation Pydantic sur payloads API.
- Middleware d'erreurs centralise + logging.
- Validation config runtime en production (`validate_runtime_config`):
  - interdit secret par defaut,
  - interdit credentials par defaut.

### 12.2 Points de vigilance

- En dev, credentials par defaut existent (`admin/admin123`, `viewer/viewer123`) -> a surcharger immediatement.
- Rate limiting en memoire (pas distribue) -> limite en scale horizontale.
- SQLite correct pour MVP, mais PostgreSQL recommande pour production concurrente.
- Gouvernance data: etablir procedures de qualite et versionning des datasets importes.

---

## 13) Robustesse, tests, et qualite

Le projet contient des tests backend (`backend/tests/`) couvrant notamment:
- endpoint recommandation,
- regression de score,
- auth/RBAC,
- workflow referrals,
- observabilite,
- logique d'equite/saturation,
- imports externes mockes.

Ce socle est deja professionnel pour un hackathon avance, et sert de filet de securite pour evolutions.

---

## 14) Limites actuelles (lecture critique)

- RL opere sur un environnement simplifie (pas encore toutes contraintes terrain: ambulances reelles, traffic temps reel, files multi-services explicites).
- Heuristique et RL utilisent des proxies de charge (capacity/wait) qui dependent de la qualite de calibration.
- Interoperabilite SIS nationaux (DHIS2/EMR) non finalisee de bout en bout dans ce repo.
- XAI clinique avancee (SHAP/LIME sur modeles plus complexes) encore partielle par rapport a l'ambition cible.
- Gestion offline-first mobile terrain non explicite ici.

---

## 15) Comment lire/resultats rapidement (pour jury)

1. Ouvrir `README.md` pour vision et setup.
2. Verifier que backend tourne (`/api/v1/health`).
3. Lancer frontend et tester page triage.
4. Executer benchmark policies (script Kenya) et ouvrir rapport `backend/docs/*.md`.
5. Ouvrir `notebooks/model_benchmark_report.ipynb` pour storytelling visuel des metriques.

Ce parcours montre:
- valeur metier (decision de transfert),
- rigueur technique (pipeline + tests),
- potentiel d'industrialisation.

---

## 16) Reproductibilite technique (commands type)

Backend:

```bash
cd backend
python scripts/init_db.py
python scripts/pipeline_kenya.py --reset-db
python scripts/train_rl.py --timesteps 50000 --model-out models/ppo_referral_kenya_mapped_v4
python scripts/evaluate_rl.py --model-path models/ppo_referral_kenya_mapped_v4.zip
python scripts/benchmark_policies_kenya.py --model-path models/ppo_referral_kenya_mapped_v4.zip
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Variables critiques:
- `DATABASE_URL`
- `VITE_API_BASE_URL`
- `AUTH_SECRET_KEY`
- `ADMIN_USERNAME`, `ADMIN_PASSWORD`
- `VIEWER_USERNAME`, `VIEWER_PASSWORD`
- `RL_MODEL_PATH`

---

## 17) Glossaire rapide

- Reference patient: transfert d'un patient vers un niveau de soins plus adapte.
- Capacite disponible: slots/lits immediatement mobilisables.
- Wait estimate: attente previsionnelle au centre destination.
- Heuristique: regle explicite de decision.
- RL/PPO: politique apprise par essais/erreurs dans un simulateur.
- Entropy norm: equilibre de distribution des referrals.
- HHI: concentration des referrals (plus haut = plus concentre).

---

## 18) Conclusion

CarePath AI est un projet techniquement coherent, avec une base solide pour passer d'un MVP data-driven a une solution deployable en contexte reel.

Ce qui est deja mature:
- architecture modulaire,
- moteur de recommandation explicable,
- workflow referral complet,
- pipeline de donnees reel,
- cadre RL + benchmarking,
- frontend operable avec auth et i18n.

Ce qui constitue la prochaine marche vers production:
- hardening securite (secrets, IAM, audit),
- observabilite operationnelle avancee,
- interop standards sante,
- calibration continue par donnees terrain,
- industrialisation MLOps du cycle RL.

Ce document peut servir de reference de lecture unique pour comprendre le projet sans contexte prealable.
