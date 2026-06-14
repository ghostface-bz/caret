"""gitleaks runner — secrets detection (no network/DB needed)."""

from __future__ import annotations

import json
import logging

from app.normalize import normalize_gitleaks
from app.scanners.base import ScannerError, run_scanner_container
from app.schemas import RawFinding

logger = logging.getLogger(__name__)

IMAGE = "zricethezav/gitleaks:latest"


def run(scan_id: str, src_subpath: str) -> list[RawFinding]:
    """Run gitleaks against `/src/<scan_id>` and return normalized findings.

    gitleaks exits 0 when no leaks are found and 1 when leaks ARE found —
    both are "success" for us. Any other exit code is an error.
    """
    scan_root = f"/src/{src_subpath}"

    result = run_scanner_container(
        tool_name="gitleaks",
        image=IMAGE,
        command=[
            "detect",
            "--source",
            scan_root,
            "--report-format",
            "json",
            "--report-path",
            "/dev/stdout",
            "--no-git",
            "--exit-code",
            "1",
        ],
        allow_exit_codes=(0, 1),
    )

    raw_results = _parse_gitleaks_output(result.stdout)
    return normalize_gitleaks(raw_results, scan_root=scan_root)


def _parse_gitleaks_output(stdout: str) -> list[dict]:
    """Extract the JSON array gitleaks writes to stdout.

    gitleaks may emit non-JSON log lines alongside the report; the report
    itself is a JSON array (`[]` when no leaks found). We locate the
    outermost `[...]` block and parse it.
    """
    stdout = stdout.strip()
    if not stdout:
        return []

    # Fast path: the whole output is the JSON array.
    try:
        data = json.loads(stdout)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    # Fallback: find the first '[' and last ']' and parse that slice.
    start = stdout.find("[")
    end = stdout.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ScannerError(tool="gitleaks", detail=f"could not parse JSON output: {stdout[:500]!r}")

    try:
        data = json.loads(stdout[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ScannerError(
            tool="gitleaks", detail=f"invalid JSON output: {exc}; output={stdout[:500]!r}"
        ) from exc

    if not isinstance(data, list):
        raise ScannerError(tool="gitleaks", detail=f"unexpected JSON shape: {type(data)}")

    return data
