# Build Plan — Secure Code Reviewer MVP

**Principle: functionality before polish.** A scan must run end-to-end and produce real,
normalized findings before anyone touches styling.

## Definition of done (MVP)
`docker compose up --build` →
1. Upload a zip OR submit a public git URL in the UI
2. Scan runs in the background; status flips queued → running → completed
3. Real findings from **gitleaks + semgrep + trivy**, normalized + CWE/OWASP-tagged
4. Dashboard lists scans and shows a filterable findings table
5. SARIF export downloads and validates
6. The bundled `test-fixtures/vulnpy` reliably produces findings

## Phases
- **P0 Foundation** *(orchestrator — DONE on commit)* — repo, compose, contracts, fixtures.
- **P1 Backend skeleton + pipeline** *(Backend agent)* — FastAPI app, models, Alembic,
  `POST/GET /scans`, RQ worker, **gitleaks** runner end-to-end (zip path), normalizer, SARIF.
- **P2 Backend scanners** *(Backend agent)* — add **semgrep** + **trivy** runners, the
  offline prefetch script, git-URL import, findings filters.
- **P3 Frontend** *(Frontend agent, parallel with P1/P2 against the contract)* — upload form,
  scan list with live polling, findings table with filters + severity summary, SARIF download.
- **P4 Integration** *(orchestrator)* — wire up, run the fixture, fix contract drift, verify DoD.
- **P5 Stretch** — minimal auth, PDF report (Typst), trends.

## Agent ground rules
- **Stay in your directory.** Backend owns `backend/`. Frontend owns `frontend/`.
  Nobody edits `docker-compose.yml` or `docs/*` — those are frozen contracts. If the
  contract is wrong, STOP and report it; don't silently diverge.
- Match service names/ports/env/volumes in `docker-compose.yml` exactly.
- Implement the API in `docs/API_CONTRACT.md` field-for-field; data model in `docs/DATA_MODEL.md`.
- Functionality first. Plain UI is fine. No auth in MVP.
- Use `uv` for Python deps (`backend/pyproject.toml`). Python 3.12 base image.
- Leave a short `backend/README.md` / `frontend/README.md` with how to run + test.

## Status log (orchestrator updates)
- [x] P0 Foundation
- [ ] P1 Backend skeleton + gitleaks pipeline
- [ ] P2 Backend semgrep + trivy + git import
- [ ] P3 Frontend dashboard
- [ ] P4 Integration + DoD verified
- [ ] P5 Stretch
