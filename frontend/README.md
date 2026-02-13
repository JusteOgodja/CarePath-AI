# CarePath AI Frontend

Frontend web React/Vite pour CarePath AI.

## Stack

- React 18 + TypeScript
- Vite
- TanStack Query
- Tailwind CSS + shadcn/ui
- Framer Motion

## Prerequisites

- Node.js 20+ recommandé
- API backend FastAPI active (par défaut `http://localhost:8000`)

## Installation

```bash
npm install
```

## Configuration

Créer `.env.local` avec:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Lancer en développement

```bash
npm run dev
```

Le serveur démarre sur `http://localhost:8080`.

## Auth RBAC (phase 3)

- Page login: `/login`
- Accès admin réseau: route protégée `/admin/network`
- Credentials par défaut (configurables côté backend):
  - `admin / admin123`
  - `viewer / viewer123` (lecture, sans droits admin)

## Build production

```bash
npm run build
npm run preview
```

## Tests

```bash
npm test
```

## Qualité locale

```bash
npm run check
```

## Structure utile

- `src/pages`: pages applicatives
- `src/components`: UI partagée et composants métier
- `src/lib/api`: client HTTP et endpoints backend
- `src/lib/types`: contrats TypeScript
