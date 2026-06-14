# Data Model (MVP) — FROZEN

Two tables. Postgres. SQLAlchemy 2.0 + Alembic migrations.

## `scans`
| column | type | notes |
|--------|------|-------|
| id | UUID PK | |
| source_type | enum(`zip`,`git`) | |
| source_ref | text | original filename or git URL |
| status | enum(`queued`,`running`,`completed`,`failed`) | |
| error | text null | populated when `failed` |
| created_at | timestamptz | default now |
| started_at | timestamptz null | |
| finished_at | timestamptz null | |

## `findings`
| column | type | notes |
|--------|------|-------|
| id | UUID PK | |
| scan_id | UUID FK → scans.id (cascade delete) | indexed |
| tool | enum(`gitleaks`,`semgrep`,`trivy`) | |
| rule_id | text | tool's native rule/check id |
| severity | enum(`critical`,`high`,`medium`,`low`,`info`) | **normalized**, see below |
| title | text | short human label |
| message | text | full description |
| file_path | text | relative to scanned root |
| line_start | int null | |
| line_end | int null | |
| cwe | text null | e.g. `CWE-89` |
| owasp | text null | e.g. `A03:2021-Injection` |
| raw | JSONB | the tool's original finding object, untouched |

One scan → many findings (cascade delete).

## Severity normalization (the heart of the "normalizer")
Each tool speaks a different dialect. Map to our 5-level scale:

| our level | semgrep | gitleaks | trivy |
|-----------|---------|----------|-------|
| critical | ERROR + `security` high-confidence | (n/a) | CRITICAL |
| high | ERROR | every secret = high | HIGH |
| medium | WARNING | — | MEDIUM |
| low | INFO | — | LOW |
| info | (everything else) | — | UNKNOWN |

CWE/OWASP extraction:
- **semgrep:** `extra.metadata.cwe[]` and `extra.metadata.owasp[]` (already provided by most rules).
- **trivy:** map the vuln's `CWE-IDs[]`; OWASP left null unless present.
- **gitleaks:** static — `CWE-798` (Use of Hard-coded Credentials), OWASP `A07:2021` style as a constant.

Keep the mapping in one module (`app/normalize.py`) — it is itself a report section.
