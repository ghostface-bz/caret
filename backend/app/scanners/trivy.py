"""trivy runner — SCA/dependency vulnerabilities, using pre-fetched DB cache."""

from __future__ import annotations

import json
import logging

from app.config import get_trivy_cache_volume
from app.normalize import normalize_trivy
from app.scanners.base import ExtraMount, ScannerError, run_scanner_container
from app.schemas import RawFinding

logger = logging.getLogger(__name__)

IMAGE = "aquasec/trivy:latest"


def run(scan_id: str, src_subpath: str) -> list[RawFinding]:
    """Run trivy filesystem vulnerability scan against `/src/<scan_id>`.

    Uses the pre-fetched vulnerability DB in `/trivy-cache` (populated by
    `scripts/prefetch.sh`) and `--skip-db-update` to avoid network access.
    Trivy exits 0 normally even when vulnerabilities are found.
    """
    scan_root = f"/src/{src_subpath}"

    result = run_scanner_container(
        tool_name="trivy",
        image=IMAGE,
        command=[
            "fs",
            "--format",
            "json",
            "--scanners",
            "vuln",
            "--skip-db-update",
            "--cache-dir",
            "/trivy-cache",
            scan_root,
        ],
        extra_mounts=[
            ExtraMount(volume_name=get_trivy_cache_volume(), target="/trivy-cache", mode="rw")
        ],
        allow_exit_codes=(0,),
        # trivy needs a writable cache dir + tmp.
        tmpfs_paths=("/tmp",),
    )

    report = _parse_trivy_output(result.stdout)
    return normalize_trivy(report, scan_root=scan_root)


def _parse_trivy_output(stdout: str) -> dict:
    stdout = stdout.strip()
    if not stdout:
        return {"Results": []}

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        start = stdout.find("{")
        end = stdout.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ScannerError(
                tool="trivy", detail=f"could not parse JSON output: {stdout[:500]!r}"
            )
        try:
            data = json.loads(stdout[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ScannerError(
                tool="trivy", detail=f"invalid JSON output: {exc}; output={stdout[:500]!r}"
            ) from exc

    if not isinstance(data, dict):
        raise ScannerError(tool="trivy", detail=f"unexpected JSON shape: {type(data)}")

    return data
