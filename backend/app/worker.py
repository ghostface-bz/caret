"""RQ worker entrypoint + the `run_scan` job.

Run with `python -m app.worker` (see docker-compose.yml `worker` service).

`run_scan(scan_id)`:
1. mark the scan `running` (set `started_at`)
2. materialize the source into `$SCAN_DATA_DIR/<scan_id>/`:
   - zip: unzip the uploaded archive (written by the API to `uploads/<scan_id>.zip`)
   - git: `git clone --depth 1 <source_ref> <scan_id>/`
3. run gitleaks, semgrep, trivy as sibling containers and normalize their output
4. persist `Finding` rows
5. mark the scan `completed` (or `failed` + `error`)
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from rq import Worker

from app.config import settings
from app.db import SessionLocal
from app.models import Finding, Scan, ScanStatus, SourceType
from app.queue import redis_conn, scan_queue
from app.scanners import gitleaks, semgrep, trivy
from app.scanners.base import ScannerError
from app.schemas import RawFinding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Each entry: (tool module, human name) — run in this order so gitleaks
# (zero network/DB) proves the pipeline first.
SCANNERS = [
    (gitleaks, "gitleaks"),
    (semgrep, "semgrep"),
    (trivy, "trivy"),
]


def _scan_data_dir(scan_id: str) -> Path:
    return Path(settings.SCAN_DATA_DIR) / scan_id


def _materialize_zip(scan_id: str, dest: Path) -> None:
    zip_path = Path(settings.SCAN_DATA_DIR) / "uploads" / f"{scan_id}.zip"
    if not zip_path.exists():
        raise RuntimeError(f"uploaded archive not found: {zip_path}")

    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        _safe_extract(zf, dest)

    _flatten_single_root(dest)


def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    """Extract a zip, guarding against path traversal (`..`, absolute paths)."""
    dest_resolved = dest.resolve()
    for member in zf.infolist():
        member_path = (dest / member.filename).resolve()
        if not str(member_path).startswith(str(dest_resolved)):
            raise RuntimeError(f"unsafe path in zip archive: {member.filename!r}")
    zf.extractall(dest)


def _flatten_single_root(dest: Path) -> None:
    """If the zip contained a single top-level directory, hoist its contents up.

    Many zip exports (e.g. GitHub "Download ZIP") wrap everything in a single
    `<repo>-<branch>/` directory. Flattening keeps reported file paths
    relative to the project root rather than `<repo>-<branch>/...`.
    """
    entries = list(dest.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        sole_dir = entries[0]
        for child in sole_dir.iterdir():
            shutil.move(str(child), str(dest / child.name))
        sole_dir.rmdir()


def _materialize_git(source_ref: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", source_ref, str(dest)],
            check=True,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"git clone failed: {exc.stderr.strip()[:1000]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("git clone timed out after 600s") from exc

    # Scanners don't need the .git history; drop it to save space / avoid
    # gitleaks scanning git history (we pass --no-git anyway, but be tidy).
    git_dir = dest / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir, ignore_errors=True)


def _run_all_scanners(scan_id: str) -> tuple[list[RawFinding], list[str]]:
    """Run each scanner against `<SCAN_DATA_DIR>/<scan_id>`, collecting findings + errors."""
    all_findings: list[RawFinding] = []
    errors: list[str] = []

    for module, name in SCANNERS:
        try:
            logger.info("scan %s: running %s", scan_id, name)
            findings = module.run(scan_id, scan_id)
            logger.info("scan %s: %s produced %d findings", scan_id, name, len(findings))
            all_findings.extend(findings)
        except ScannerError as exc:
            logger.exception("scan %s: %s failed", scan_id, name)
            errors.append(str(exc))
        except Exception as exc:  # noqa: BLE001 - isolate scanner failures
            logger.exception("scan %s: %s failed unexpectedly", scan_id, name)
            errors.append(f"{name} scanner failed: {exc}")

    return all_findings, errors


def run_scan(scan_id: str) -> None:
    """RQ job: run the full scan pipeline for `scan_id`."""
    db = SessionLocal()
    try:
        scan = db.get(Scan, uuid.UUID(scan_id))
        if scan is None:
            logger.error("scan %s not found", scan_id)
            return

        scan.status = ScanStatus.running
        scan.started_at = datetime.now(timezone.utc)
        db.commit()

        dest = _scan_data_dir(scan_id)
        try:
            if scan.source_type == SourceType.zip:
                _materialize_zip(scan_id, dest)
            elif scan.source_type == SourceType.git:
                _materialize_git(scan.source_ref, dest)
            else:
                raise RuntimeError(f"unknown source_type: {scan.source_type}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("scan %s: failed to materialize source", scan_id)
            scan.status = ScanStatus.failed
            scan.error = f"failed to prepare source: {exc}"
            scan.finished_at = datetime.now(timezone.utc)
            db.commit()
            return

        findings, errors = _run_all_scanners(scan_id)

        for rf in findings:
            db.add(
                Finding(
                    scan_id=scan.id,
                    tool=rf.tool,
                    rule_id=rf.rule_id,
                    severity=rf.severity,
                    title=rf.title,
                    message=rf.message,
                    file_path=rf.file_path,
                    line_start=rf.line_start,
                    line_end=rf.line_end,
                    cwe=rf.cwe,
                    owasp=rf.owasp,
                    raw=rf.raw,
                )
            )

        if errors and not findings:
            # All scanners failed and produced nothing useful — mark failed.
            scan.status = ScanStatus.failed
            scan.error = "; ".join(errors)[:4000]
        else:
            scan.status = ScanStatus.completed
            if errors:
                # Partial success: keep findings, but record what failed.
                scan.error = "; ".join(errors)[:4000]

        scan.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(
            "scan %s: completed with status=%s, %d findings, %d scanner errors",
            scan_id,
            scan.status,
            len(findings),
            len(errors),
        )
    finally:
        db.close()


def main() -> None:
    """Entrypoint for `python -m app.worker` — start an RQ worker on the scans queue."""
    worker = Worker([scan_queue], connection=redis_conn)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
