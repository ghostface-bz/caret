# Secure Code Reviewer — Backend

FastAPI app + RQ worker implementing `docs/API_CONTRACT.md` and `docs/DATA_MODEL.md`.

## Stack
- Python 3.12, FastAPI, SQLAlchemy 2.0 (typed) + Alembic, psycopg3, RQ (Redis), pydantic v2
- `docker` Python SDK — the worker spawns ephemeral, network-disabled sibling
  containers (gitleaks / semgrep / trivy) per `docs/API_CONTRACT.md`'s sandbox contract.
- Deps managed with `uv` (`pyproject.toml`); image is `python:3.12-slim`.

## Run it

From the repo root:

```bash
docker compose up --build
```

This builds the shared `backend` image, used by both the `backend` (uvicorn
`app.main:app`) and `worker` (`python -m app.worker`) services. On container
start, `scripts/entrypoint.sh` runs `alembic upgrade head` (idempotent) before
launching the given command. `app.main` also calls `Base.metadata.create_all`
on startup as a fallback safety net if migrations haven't run.

- API: http://localhost:8000 (docs at `/docs`, health at `/api/health`)
- Postgres: `scr` / `scr` / `scr` on `db:5432`
- Redis: `redis:6379/0`

## One-time offline prefetch (REQUIRED before scans will find anything from semgrep/trivy)

Scanner sibling containers run with `network_disabled=True`, so semgrep rules
and the trivy vulnerability DB must be pre-fetched into the `semgrep_rules`
and `trivy_cache` named volumes **while network access is allowed**:

```bash
docker compose up -d db redis backend worker   # ensures named volumes exist
bash backend/scripts/prefetch.sh
```

This:
- clones a curated subset of `semgrep/semgrep-rules` (python, javascript,
  typescript, generic, security) into the `semgrep_rules` volume, mounted at
  `/rules` for the semgrep sibling container
- runs `trivy ... --download-db-only --cache-dir /trivy-cache` into the
  `trivy_cache` volume, mounted at `/trivy-cache` for the trivy sibling
  container

Re-run any time to refresh rules/DB (both steps are idempotent).

## Submitting a scan

**Zip upload:**
```bash
cd test-fixtures && zip -r /tmp/vulnpy.zip vulnpy && cd ..
curl -s -X POST http://localhost:8000/api/scans -F file=@/tmp/vulnpy.zip
```

**Git URL:**
```bash
curl -s -X POST http://localhost:8000/api/scans \
  -H 'Content-Type: application/json' \
  -d '{"source_type": "git", "source_ref": "https://github.com/owner/repo"}'
```

Poll status:
```bash
curl -s http://localhost:8000/api/scans/<id> | python3 -m json.tool
```

Once `status` is `completed`:
```bash
curl -s http://localhost:8000/api/scans/<id>/findings | python3 -m json.tool
curl -s http://localhost:8000/api/scans/<id>/report.sarif | python3 -m json.tool
```

## Database migrations

```bash
docker compose exec backend alembic upgrade head      # apply
docker compose exec backend alembic revision -m "..." # new revision (manual or --autogenerate)
```

## Project layout

```
app/
  main.py        FastAPI app, CORS, /api/health, routers, create_all fallback
  config.py      env-var settings (DATABASE_URL, REDIS_URL, SCAN_DATA_DIR, ...)
  db.py          SQLAlchemy engine/session
  models.py      Scan, Finding ORM models (docs/DATA_MODEL.md)
  schemas.py     pydantic v2 schemas matching docs/API_CONTRACT.md
  queue.py       RQ queue + enqueue_scan()
  worker.py      RQ worker entrypoint + run_scan(scan_id) job
  normalize.py   per-tool severity/CWE/OWASP normalization -> RawFinding
  sarif.py       SARIF 2.1.0 export (one run per tool)
  api/scans.py   /api/scans routes
  scanners/
    base.py      shared sibling-container runner (sandbox contract)
    gitleaks.py  secrets scanner
    semgrep.py   SAST scanner (uses /rules)
    trivy.py     SCA/dependency scanner (uses /trivy-cache)
alembic/         migrations (0001_initial: scans + findings tables/enums)
scripts/
  entrypoint.sh  runs `alembic upgrade head` then exec's the compose command
  prefetch.sh    populates semgrep_rules + trivy_cache volumes
```

## Known limitations / deferred

- `GET /api/scans/{id}/report.pdf` returns `501 Not Implemented` (Phase 5 stretch).
- No auth (by design, MVP).
- Severity-critical promotion for semgrep (`ERROR` + high-confidence security
  rule -> `critical`) depends on rule metadata (`metadata.confidence`,
  `metadata.category`/`vulnerability_class`); rules without that metadata stay `high`.
