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

## 4) Test rapide recommandation

Requete `POST /recommander`:

```json
{
  "patient_id": "P001",
  "current_centre_id": "C_LOCAL_A",
  "needed_speciality": "maternal",
  "severity": "medium"
}
```

## 5) Endpoints d'administration

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
- `backend/scripts/seed_demo_data.py`: jeu de donnees initial

## Roadmap

1. Ajouter tests unitaires API et moteur de reco
2. Ajouter simulation et environnement RL
3. Ajouter module explicabilite et interface clinicien
