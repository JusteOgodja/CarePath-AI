# CarePath AI - Etat technique detaille du projet

## 1. Contexte et objectif technique
CarePath AI est un prototype backend en Python centre sur l'optimisation des parcours de reference patient dans un reseau de soins modelise en graphe.

Objectif actuel atteint:
- proposer une recommandation de destination via API (`/recommander`)
- administrer le reseau (CRUD centres/liens)
- simuler des flux multi-patients (stable/shock)
- benchmarker plusieurs scenarios
- entrainer et evaluer une baseline RL (PPO) contre une heuristique
- produire des rapports JSON/Markdown exploitables pour demo/pitch

Le projet est organise autour d'une architecture modulaire backend + scripts + tests.

---

## 2. Stack technique effectivement implementee
### Langage et runtime
- Python 3.x

### Backend/API
- FastAPI
- Pydantic v2 (validation des payloads)
- Uvicorn (serveur ASGI)

### Donnees
- SQLAlchemy ORM 2.x
- SQLite (fichier local `backend/carepath.db`)

### Graphe et logique de decision
- NetworkX (plus court chemin / poids trajet)

### Simulation et RL
- Numpy
- Gymnasium (environnement RL custom)
- Stable-Baselines3 (PPO)

### Qualite
- Pytest
- FastAPI TestClient / httpx

Dependances declarees dans `backend/requirements.txt`.

---

## 3. Structure projet actuelle
Arborescence fonctionnelle principale:

- `backend/app/main.py`: creation app FastAPI
- `backend/app/api/routes.py`: endpoints metier + admin
- `backend/app/services/schemas.py`: schemas Pydantic API
- `backend/app/services/graph_service.py`: chargement graphe depuis DB
- `backend/app/services/recommender.py`: moteur de recommandation
- `backend/app/db/models.py`: schema SQLAlchemy + session
- `backend/app/rl/env.py`: environnement Gymnasium
- `backend/app/rl/heuristic_policy.py`: policy heuristique
- `backend/app/rl/evaluation.py`: utilitaires eval RL vs heuristique

Scripts operationnels:
- `backend/scripts/init_db.py`
- `backend/scripts/seed_demo_data.py`
- `backend/scripts/simulate_batch.py`
- `backend/scripts/train_rl.py`
- `backend/scripts/evaluate_rl.py`
- `backend/scripts/run_complex_scenarios.py`
- `backend/scripts/summarize_scenarios.py`
- `backend/scripts/run_primary_demo.py`

Tests:
- `backend/tests/conftest.py`
- `backend/tests/test_admin_endpoints.py`
- `backend/tests/test_recommender_endpoint.py`
- `backend/tests/test_scoring_regression.py`
- `backend/tests/test_equity_saturation.py`

Artefacts:
- `backend/models/*.zip` (modeles PPO)
- `backend/docs/*.json` (rapports)
- `backend/docs/scenario_summary.md`

---

## 4. Backend API - capacites implementees
## 4.1 Endpoint metier
### `GET /health`
- Retourne `{"status": "ok"}`
- Utilise pour healthcheck basique.

### `POST /recommander`
Entree (`RecommandationRequest`):
- `patient_id: str`
- `current_centre_id: str`
- `needed_speciality: maternal | pediatric | general`
- `severity: low | medium | high`

Sortie (`RecommandationResponse`):
- destination retenue
- chemin (liste de centres)
- `estimated_travel_minutes`
- `estimated_wait_minutes`
- `score`
- explication textuelle

Gestion erreurs:
- 400 avec message explicite si:
  - reseau vide
  - pas de destination dispo
  - pas de destination autre que centre courant
  - destination inatteignable

## 4.2 Endpoints administration reseau
### Centres
- `GET /centres`
- `POST /centres`
- `PUT /centres/{centre_id}`
- `DELETE /centres/{centre_id}`

Regles implementees:
- specialites non vides
- prevention doublon centre (409)
- suppression centre bloquee si references associees (409)

### References
- `GET /references`
- `POST /references`
- `PUT /references/{reference_id}`
- `DELETE /references/{reference_id}`

Regles implementees:
- `source_id != dest_id`
- source/destination doivent exister

---

## 5. Modele de donnees SQL actuel
Defini dans `backend/app/db/models.py`.

Tables:
- `centres`
  - `id` (PK)
  - `name`
  - `level`
  - `specialities` (CSV string)
  - `capacity_available`
  - `estimated_wait_minutes`

- `references`
  - `id` (PK)
  - `source_id` (FK -> centres.id)
  - `dest_id` (FK -> centres.id)
  - `travel_minutes`

- `patients`
  - `id` (PK)
  - `age`
  - `symptoms`

- `episodes`
  - `id` (PK)
  - `patient_id` (FK)
  - `source_id` (FK)
  - `recommended_dest_id` (FK)
  - `reward`

Infra SQLAlchemy:
- engine global
- `SessionLocal`
- `init_db()`
- `get_session()`

---

## 6. Moteur de recommandation (heuristique graphe)
## 6.1 Construction graphe
`GraphService`:
- recharge centres + liens depuis SQLite
- construit `nx.DiGraph`
- expose:
  - `candidate_destinations(needed_speciality)`
  - `shortest_path(source, target)`
  - `node(node_id)`

## 6.2 Scoring
`CandidateScore.score`:
- formule actuelle: `(travel_minutes + wait_minutes) / max(capacity, 1)`
- interpretation: minimiser cout trajet+attente, penaliser faible capacite

## 6.3 Selection finale
`Recommender.recommend`:
1. reload graphe
2. filtre specialite + capacite > 0
3. exclut centre courant
4. calcule chemins atteignables
5. score chaque candidat
6. retient minimum
7. construit explication textuelle

Points deja robustifies:
- distinction explicite "pas de destination autre que centre courant"
- gestion `NetworkXNoPath`/`NodeNotFound`

---

## 7. Simulation batch operationnelle
Script principal: `backend/scripts/simulate_batch.py`

Fonctionnalites clefs:
- simulation N patients
- impact orientation:
  - capacite destination decremente
  - attente destination incrementee
- recuperation periodique:
  - capacite remonte jusqu'au max initial
  - attente diminue

## 7.1 Fallback policy
Modes:
- `none`
- `force_least_loaded`

Lorsque la reco standard echoue:
- fallback peut choisir une destination surchargee (capacite 0) avec penalite
- suit toujours specialite + connectivite

Metriques calculees:
- succes/echecs
- taux d'echec
- fallbacks utilises
- avg travel/wait/score
- distribution destinations
- HHI (concentration)
- entropy normalisee (equilibre)
- raisons d'echec

## 7.2 Reseaux seeds
- `--seed-demo`: petit reseau 4 centres
- `--seed-complex`: reseau 9 centres plus riche

## 7.3 Chocs aleatoires
Parametres:
- `--shock-every`
- `--shock-wait-add`
- `--shock-capacity-drop`
- `--random-seed`

Simule perturbations operationnelles (surcharge inattendue, indisponibilite partielle).

---

## 8. Scenarios, benchmark et synthese
## 8.1 Runner multi-scenarios
`backend/scripts/run_complex_scenarios.py`
- execute un set predefini de scenarios:
  - demo stable
  - demo shock
  - complex stable
  - complex pediatric shock
- produit JSON consolide

## 8.2 Synthese benchmark
`backend/scripts/summarize_scenarios.py`
- lit `scenario_report.json`
- calcule score composite configurable
- classe scenarios
- genere rapport Markdown avec recommandations

Score composite actuel:
- `composite = w_score*avg_score + w_fallback*100*fallback_rate + w_failure*100*failure_rate`

## 8.3 Scenario principal de demo
`backend/scripts/run_primary_demo.py`
- execute automatiquement `complex_maternal_stable`
- exporte `primary_demo_report.json`

---

## 9. RL - implementation actuelle
## 9.1 Environnement custom
`backend/app/rl/env.py` (`ReferralEnv`)

Etat (observation):
- capacites normalisees
- attentes normalisees
- temps de trajet normalises
- ratio progression episode

Action:
- indice destination discrete

Dynamique:
- si capacite > 0: decrement capacite
- sinon overload
- attente destination augmente
- recuperation periodique optionnelle

Reward:
- base: `-(travel + wait)/reward_scale`
- penalite overload additionnelle

## 9.2 Entrainement
`backend/scripts/train_rl.py`
- PPO (`stable_baselines3.PPO`)
- hyperparams initiaux exposes CLI:
  - timesteps
  - learning rate
  - surcharge penalty
  - dynamique episode
- sauvegarde modele zip dans `backend/models/`

## 9.3 Evaluation
`backend/scripts/evaluate_rl.py`
- charge modele PPO
- compare RL vs heuristique sur memes episodes
- sort JSON:
  - `avg_reward_per_episode`
  - `avg_overloads_per_episode`
  - distributions destinations

Etat observe sur vos runs:
- PPO converge vers performance proche/egale de l'heuristique sur scenario simple/medium.

---

## 10. Suite de tests implementee
Framework: pytest.

Couverture actuelle:
- admin CRUD
  - creation/listing centre
  - conflits doublons
  - suppression centre reference
  - CRUD references

- `/recommander`
  - succes nominal
  - reseau vide
  - specialite indisponible
  - destination inatteignable

- non-regression scoring
  - formule score brute
  - effets capacite/attente sur choix
  - exclusion centre courant

- scenarios equite/saturation
  - reroutage quand centre plein
  - repartition dynamique via attente
  - erreur si toutes destinations specialisees a capacite nulle

Fixture commune:
- reset DB avant/apres test
- client FastAPI

---

## 11. Observabilite et livrables produits
Livrables auto-generes deja presents:
- `backend/docs/scenario_report.json`
- `backend/docs/scenario_summary.md`
- `backend/docs/primary_demo_report.json`

Modeles entraines:
- `backend/models/ppo_referral.zip`
- `backend/models/ppo_referral_v2.zip`
- `backend/models/ppo_referral_v3.zip`

Ces artefacts montrent:
- capacite a comparer setups
- capacite a reproduire evaluation
- capacite a presenter resultats quantifies

---

## 12. Robustesse actuellement atteinte
Niveau actuel:
- solide pour prototypage, benchmark, demo technique
- bon niveau de reproductibilite locale
- bonne lisibilite des composants

Robustesse deja en place:
- validations de base API
- messages erreurs explicites
- fallback simulation configurable
- stress tests par scenarios/chocs
- comparatif RL vs baseline

---

## 13. Limites techniques actuelles (faites constatables dans le code)
1. DB locale SQLite unique (`DATABASE_URL` hardcode)
2. pas de migration schema versionnee
3. `specialities` stocke en CSV string (normalisation limitee)
4. pas d'auth/roles sur routes admin
5. pas de verrous transactionnels metier pour reservation de capacite
6. `severity` present mais non integre au score/reward metier
7. scripts de seed destructifs (delete tables)
8. RL simplifie (etat/recompense encore loin de contraintes terrain completes)

---

## 14. Pipeline d'utilisation actuel (end-to-end)
1. Installer deps
2. init DB / seed
3. lancer API
4. tester endpoints admin + recommander
5. lancer simulation batch
6. lancer benchmark multi-scenarios
7. generer synthese Markdown
8. entrainer PPO
9. evaluer PPO vs heuristique
10. utiliser scenario principal pour demo

---

## 15. Evaluation globale de maturite technique
Maturite prototype: avancee.

Ce qui est deja industrialisable a court terme:
- structure modulaire
- strategie de test
- scripts de benchmark
- reporting automatique

Ce qui reste necessaire avant donnees reelles a grande echelle:
- durcissement donnees/transactions/securite
- gouvernance schema + migrations
- observabilite applicative (logs/metrics/audit)
- integration metier clinique plus stricte (severity/contraintes)

---

## 16. Fichier de reference
Ce document decrit l'etat technique reel du projet a l'instant T et peut servir de base:
- pour documentation de sprint
- pour dossier de soutenance hackathon
- pour plan de passage prototype -> preproduction
