# Release Checklist (CarePath AI)

## 1) Security
- Rotate all API keys and credentials before release.
- Verify `.env` files are not committed.
- Ensure `AUTH_SECRET_KEY` is strong and not default.
- Confirm admin/viewer credentials are not default.

## 2) Database & Migrations
- Backup the production database.
- Run migrations in staging first.
- Validate schema revision with `/api/v1/health`.
- Run migrations in production.

## 3) Backend Validation
- Run `python -m pytest -q` in `backend/`.
- Verify API docs load at `/docs`.
- Smoke test key endpoints:
  - `/api/v1/auth/login`
  - `/api/v1/recommander`
  - `/api/v1/referrals/requests` workflow transitions
  - `/api/v1/health`

## 4) Frontend Validation
- Run `npm run lint` in `frontend/`.
- Run `npm run typecheck` in `frontend/`.
- Run `npm run test` in `frontend/`.
- Run `npm run build` in `frontend/`.
- Validate UI pages:
  - Triage
  - Admin Network
  - Referrals Workflow
  - Indicators
  - System

## 5) Runtime Observability
- Confirm structured logs are emitted (JSON).
- Confirm `X-Request-ID` appears in API responses.
- Verify error payload format is standardized.
- Check rate-limits on auth/admin write paths.

## 6) Deployment
- Deploy backend first, then frontend.
- Validate CORS configuration in deployed environment.
- Run smoke checks after deployment.

## 7) Rollback Plan
- Keep previous backend artifact available.
- Keep previous frontend artifact available.
- If critical issue appears:
  - rollback frontend,
  - rollback backend,
  - restore DB snapshot if migration-related.
