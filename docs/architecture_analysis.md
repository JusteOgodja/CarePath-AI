# CarePath AI - Analyse architecture et plan d'execution

## Objectif produit
Fournir une recommandation de reference patient qui optimise delai, disponibilite et adequation clinique,
avec une explication lisible par un clinicien.

## Analyse de la proposition

### Points solides
- Bonne decomposition: API, moteur decisionnel, donnees, interface.
- Bon choix MVP: commencer heuristique graphe avant RL.
- Focus explicabilite pertinent pour un contexte clinique.

### Risques majeurs a traiter tot
- Qualite de donnees: capacite et temps d'attente sont souvent incomplets ou obsoletes.
- Instabilite RL: sans simulateur credible, l'agent apprend des politiques inutilisables.
- Objectif unique trop reducteur: minimiser seulement le temps peut nuire a l'equite.
- Integration clinique: une reco doit rester contraignable (override humain obligatoire).

### Decisions d'architecture recommandees
- Garder FastAPI + SQLite pour MVP, puis migrer vers PostgreSQL si besoin multi-utilisateur.
- Isoler le moteur de reco dans un service pur Python (deja fait) pour tester facilement.
- Commencer par un score transparent (distance + attente + capacite), puis RL en parallele.
- Journaliser chaque decision et ses facteurs pour auditabilite.

## KPI de succes (phase prototype)
- Delai moyen de prise en charge (minutes).
- Taux de references evitables.
- Taux de saturation par centre.
- Ecart d'acces entre zones (proxy d'equite).
- Taux d'acceptation clinique des recommandations.

## Plan incremental
1. MVP heuristique sur graphe (en cours)
2. Passage donnees en SQLite (table centres/references/patients)
3. Simulateur patient-flux credible
4. Baselines (plus court chemin, score heuristique)
5. RL compare aux baselines
6. Explication locale et dashboard simple

## Exigences produit minimales
- Reponse API < 500 ms en mode inference heuristique
- Explication textuelle a chaque recommandation
- Tra?abilite de la decision (inputs + score + option retenue)
- Endpoint healthcheck + docs OpenAPI

## Ethique et securite clinique
- IA en assistance seulement, jamais autonome.
- Regles de garde-fou: exclusion des destinations incompatibles cliniquement.
- Transparence: afficher limites de la recommandation et incertitudes.

## Etat actuel du code
- API FastAPI operationnelle (`/health`, `/recommander`)
- Graphe en memoire avec centres/liens de demo
- Recommandation multi-critere simple + explication textuelle
- Schema SQLite initialise (`centres`, `references`, `patients`, `episodes`)

## Prochaine iteration technique
- Lire le graphe depuis SQLite au lieu des donnees hard-codees.
- Ajouter endpoint d'administration pour charger/mettre a jour les centres.
- Ajouter tests unitaires sur le moteur de recommandation.
