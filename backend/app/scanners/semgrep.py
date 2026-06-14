"""semgrep runner — SAST, using pre-fetched offline rules (`/rules`)."""

from __future__ import annotations

import json
import logging

from app.config import get_semgrep_rules_volume
from app.normalize import normalize_semgrep
from app.scanners.base import ExtraMount, ScannerError, run_scanner_container
from app.schemas import RawFinding

logger = logging.getLogger(__name__)

IMAGE = "semgrep/semgrep:latest"


def run(scan_id: str, src_subpath: str) -> list[RawFinding]:
    """Run semgrep against `/src/<scan_id>` using the pre-fetched `/rules` config.

    semgrep's `--json` exits 0 normally even when findings are present; exit
    code 1 can occur for some rule/parse warnings while still emitting a
    valid JSON report, so we accept both.
    """
    scan_root = f"/src/{src_subpath}"

    result = run_scanner_container(
        tool_name="semgrep",
        image=IMAGE,
        command=[
            "semgrep",
            "scan",
            "--json",
            "--quiet",
            "--config",
            "/rules",
            scan_root,
        ],
        extra_mounts=[ExtraMount(volume_name=get_semgrep_rules_volume(), target="/rules")],
        allow_exit_codes=(0, 1),
        # semgrep (uid 1000 -> "semgrep") needs a writable $HOME for its
        # settings/config + metrics cache.
        tmpfs_paths=("/tmp", "/home/semgrep"),
        environment={
            "SEMGREP_SEND_METRICS": "off",
            "SEMGREP_ENABLE_VERSION_CHECK": "0",
        },
    )

    report = _parse_semgrep_output(result.stdout)
    results = report.get("results", []) or []
    return normalize_semgrep(results, scan_root=scan_root)


def _parse_semgrep_output(stdout: str) -> dict:
    stdout = stdout.strip()
    if not stdout:
        return {"results": []}

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        # Fallback: find the outermost JSON object.
        start = stdout.find("{")
        end = stdout.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ScannerError(
                tool="semgrep", detail=f"could not parse JSON output: {stdout[:500]!r}"
            )
        try:
            data = json.loads(stdout[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ScannerError(
                tool="semgrep",
                detail=f"invalid JSON output: {exc}; output={stdout[:500]!r}",
            ) from exc

    if not isinstance(data, dict):
        raise ScannerError(tool="semgrep", detail=f"unexpected JSON shape: {type(data)}")

    return data
