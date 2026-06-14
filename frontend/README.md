# Secure Code Reviewer — Frontend

Vite + React + TypeScript + Tailwind dashboard for the Secure Code Reviewer MVP.
Built against [`docs/API_CONTRACT.md`](../docs/API_CONTRACT.md) (frozen contract).

## Run locally (without Docker)

```bash
npm install
npm run dev
```

Opens on http://localhost:5173 by default (or the next free port).

By default the app talks to `http://localhost:8000/api`. To point at a different
backend, set `VITE_API_BASE` (must include the `/api` suffix):

```bash
VITE_API_BASE=http://localhost:8000/api npm run dev
```

## Run via docker compose

From the repo root:

```bash
docker compose up --build
```

The `frontend` service builds `frontend/Dockerfile`, runs
`vite --host 0.0.0.0 --port 5173`, and is reachable at http://localhost:5173.
`VITE_API_BASE` is set to `http://localhost:8000/api` in `docker-compose.yml`.

## Build

```bash
npm run build   # tsc -b && vite build — must pass with no TS errors
npm run preview # serve the production build locally
```

## What it expects from the API

- `POST /api/scans` — create a scan, either:
  - `multipart/form-data` with `file=<.zip>` (max 50 MB), or
  - `application/json` `{ "source_type": "git", "source_ref": "<url>" }`
- `GET /api/scans` — list of scans (newest first), each with `counts` (severity totals)
- `GET /api/scans/{id}` — scan detail (adds `started_at`, `error`)
- `GET /api/scans/{id}/findings` — findings array, filterable via query params:
  `severity`, `tool`, `cwe`, `file` (substring), `q` (text search)
- `GET /api/scans/{id}/report.sarif` — SARIF 2.1.0 export, used by the "Download SARIF" button
- `GET /api/health` — liveness

## Pages

- **`/`** — Scan list. Polls `GET /api/scans` every ~2s while any scan is
  `queued` or `running`.
- **`/new`** — New scan form: upload a `.zip` or submit a public git URL.
  On success, navigates to the new scan's detail page.
- **`/scans/:id`** — Scan detail: status, timestamps, severity summary, SARIF
  download, and a filterable findings table (severity, tool, file substring,
  text search). Polls scan + findings every ~2s while the scan is
  `queued`/`running`.

## Notes

- If the API is unreachable or returns an error, each page shows an inline
  "API unreachable" / "not found" message instead of crashing — there is no
  global error boundary needed for the MVP because every data-fetching view
  handles its own loading/error/empty states via React Query.
- Severity and status badges use a fixed Tailwind color mapping
  (`src/components/SeverityBadge.tsx`, `StatusBadge.tsx`).
- API types live in `src/api/types.ts` and mirror
  `docs/API_CONTRACT.md` / `docs/DATA_MODEL.md` field-for-field
  (snake_case to match the JSON wire format).
