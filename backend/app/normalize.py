"""Normalization layer — maps each scanner's native output to `RawFinding`.

This is the heart of the "normalizer" called out in docs/DATA_MODEL.md: severity
mapping and CWE/OWASP extraction live here, in one module, per tool.

Severity normalization (our 5-level scale):

| our level | semgrep                          | gitleaks       | trivy     |
|-----------|----------------------------------|----------------|-----------|
| critical  | ERROR + security high-confidence | (n/a)          | CRITICAL  |
| high      | ERROR                             | every secret   | HIGH      |
| medium    | WARNING                           | --             | MEDIUM    |
| low       | INFO                              | --             | LOW       |
| info      | (everything else)                | --             | UNKNOWN   |
"""

from __future__ import annotations

import re
from typing import Any

from app.models import Severity, Tool
from app.schemas import RawFinding

# Static metadata for gitleaks findings (docs/DATA_MODEL.md).
GITLEAKS_CWE = "CWE-798"  # Use of Hard-coded Credentials
GITLEAKS_OWASP = "A07:2021-Identification and Authentication Failures"


def _first_or_none(values: Any) -> str | None:
    """Return the first element of a list-like value as a string, else None."""
    if not values:
        return None
    if isinstance(values, (list, tuple)):
        if not values:
            return None
        return str(values[0])
    return str(values)


_CWE_NUMBER_RE = re.compile(r"CWE-(\d+)", re.IGNORECASE)


def _cwe_to_str(value: Any) -> str | None:
    """Normalize a CWE value to bare `CWE-<n>`.

    Accepts `CWE-89`, `89`, `["CWE-89"]`, or semgrep's verbose
    `"CWE-89: Improper Neutralization of ... ('SQL Injection')"`.
    """
    raw = _first_or_none(value) if isinstance(value, list) else value
    if raw is None:
        return None
    raw_str = str(raw).strip()
    if not raw_str:
        return None

    match = _CWE_NUMBER_RE.search(raw_str)
    if match:
        return f"CWE-{match.group(1)}"

    if raw_str.isdigit():
        return f"CWE-{raw_str}"

    return raw_str


# ---------------------------------------------------------------------------
# gitleaks
# ---------------------------------------------------------------------------


def normalize_gitleaks(raw_results: list[dict[str, Any]], scan_root: str) -> list[RawFinding]:
    """Normalize `gitleaks detect --report-format json` output.

    Each element looks roughly like:
    {
      "Description": "AWS Access Key", "StartLine": 14, "EndLine": 14,
      "File": "app.py", "RuleID": "aws-access-token", "Match": "...", ...
    }
    """
    findings: list[RawFinding] = []
    for item in raw_results:
        file_path = _strip_scan_root(str(item.get("File", "")), scan_root)
        start_line = item.get("StartLine")
        end_line = item.get("EndLine")
        rule_id = str(item.get("RuleID", "unknown"))
        description = str(item.get("Description") or rule_id)

        findings.append(
            RawFinding(
                tool=Tool.gitleaks,
                rule_id=rule_id,
                severity=Severity.high,  # every secret = high
                title=description,
                message=(
                    f"Hard-coded secret detected: {description} "
                    f"(rule `{rule_id}`)."
                ),
                file_path=file_path,
                line_start=int(start_line) if start_line is not None else None,
                line_end=int(end_line) if end_line is not None else None,
                cwe=GITLEAKS_CWE,
                owasp=GITLEAKS_OWASP,
                raw=item,
            )
        )
    return findings


# ---------------------------------------------------------------------------
# semgrep
# ---------------------------------------------------------------------------

_SEMGREP_SEVERITY_MAP = {
    "ERROR": Severity.high,
    "WARNING": Severity.medium,
    "INFO": Severity.low,
}


def _semgrep_severity(result: dict[str, Any]) -> Severity:
    extra = result.get("extra", {}) or {}
    severity_str = str(extra.get("severity", "")).upper()
    metadata = extra.get("metadata", {}) or {}

    if severity_str == "ERROR":
        # Promote to critical for high-confidence security findings.
        confidence = str(metadata.get("confidence", "")).upper()
        categories = metadata.get("category")
        is_security = categories == "security" or "security" in (
            metadata.get("vulnerability_class") or []
        )
        if is_security and confidence == "HIGH":
            return Severity.critical
        return Severity.high

    return _SEMGREP_SEVERITY_MAP.get(severity_str, Severity.info)


def normalize_semgrep(raw_results: list[dict[str, Any]], scan_root: str) -> list[RawFinding]:
    """Normalize `semgrep scan --json` `results[]` entries.

    Each element looks roughly like:
    {
      "check_id": "python.lang.security.audit...",
      "path": "app.py",
      "start": {"line": 24, "col": ...}, "end": {"line": 24, "col": ...},
      "extra": {
        "message": "...", "severity": "ERROR",
        "metadata": {"cwe": [...], "owasp": [...], ...}
      }
    }
    """
    findings: list[RawFinding] = []
    for item in raw_results:
        extra = item.get("extra", {}) or {}
        metadata = extra.get("metadata", {}) or {}

        rule_id = str(item.get("check_id", "unknown"))
        file_path = _strip_scan_root(str(item.get("path", "")), scan_root)
        start = item.get("start", {}) or {}
        end = item.get("end", {}) or {}
        message = str(extra.get("message", "")).strip() or rule_id

        # Title: short label. Use the last path component of the check_id,
        # falling back to the rule id itself.
        title = rule_id.rsplit(".", 1)[-1].replace("-", " ").replace("_", " ")
        if not title:
            title = rule_id

        cwe = _cwe_to_str(metadata.get("cwe"))
        owasp = _first_or_none(metadata.get("owasp"))

        findings.append(
            RawFinding(
                tool=Tool.semgrep,
                rule_id=rule_id,
                severity=_semgrep_severity(item),
                title=title,
                message=message,
                file_path=file_path,
                line_start=start.get("line"),
                line_end=end.get("line"),
                cwe=cwe,
                owasp=owasp,
                raw=item,
            )
        )
    return findings


# ---------------------------------------------------------------------------
# trivy
# ---------------------------------------------------------------------------

_TRIVY_SEVERITY_MAP = {
    "CRITICAL": Severity.critical,
    "HIGH": Severity.high,
    "MEDIUM": Severity.medium,
    "LOW": Severity.low,
    "UNKNOWN": Severity.info,
}


def normalize_trivy(raw_report: dict[str, Any], scan_root: str) -> list[RawFinding]:
    """Normalize a `trivy fs --format json --scanners vuln` report.

    Top-level shape: {"Results": [{"Target": "...", "Vulnerabilities": [...]}]}
    Each vulnerability looks roughly like:
    {
      "VulnerabilityID": "CVE-2018-...", "PkgName": "flask", "InstalledVersion": "0.12.2",
      "FixedVersion": "...", "Title": "...", "Description": "...", "Severity": "HIGH",
      "CweIDs": ["CWE-79"], ...
    }
    """
    findings: list[RawFinding] = []
    for result in raw_report.get("Results", []) or []:
        target = _strip_scan_root(str(result.get("Target", "")), scan_root)
        for vuln in result.get("Vulnerabilities", []) or []:
            severity_str = str(vuln.get("Severity", "")).upper()
            severity = _TRIVY_SEVERITY_MAP.get(severity_str, Severity.info)

            vuln_id = str(vuln.get("VulnerabilityID", "unknown"))
            pkg_name = vuln.get("PkgName", "")
            installed = vuln.get("InstalledVersion", "")
            fixed = vuln.get("FixedVersion")

            title = vuln.get("Title") or f"{vuln_id} in {pkg_name}"

            message_parts = [vuln.get("Description") or title]
            if pkg_name:
                detail = f"Package `{pkg_name}` version `{installed}` is affected by {vuln_id}."
                if fixed:
                    detail += f" Fixed in `{fixed}`."
                message_parts.append(detail)
            message = "\n\n".join(p for p in message_parts if p)

            cwe_ids = vuln.get("CweIDs") or []
            cwe = _cwe_to_str(cwe_ids[0]) if cwe_ids else None

            findings.append(
                RawFinding(
                    tool=Tool.trivy,
                    rule_id=vuln_id,
                    severity=severity,
                    title=str(title),
                    message=message,
                    file_path=target,
                    line_start=None,
                    line_end=None,
                    cwe=cwe,
                    owasp=None,  # not provided by trivy
                    raw=vuln,
                )
            )
    return findings


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _strip_scan_root(path: str, scan_root: str) -> str:
    """Make a scanner-reported path relative to the scanned root.

    Scanners report paths like `/src/<scan_id>/app.py`. We want `app.py`
    (or `subdir/app.py`) — relative to the scanned root.
    """
    if not path:
        return path
    normalized_root = scan_root.rstrip("/")
    if path.startswith(normalized_root + "/"):
        return path[len(normalized_root) + 1 :]
    if path == normalized_root:
        return ""
    # Some tools emit paths already relative (e.g. "./app.py" or "app.py").
    return path.lstrip("./")
