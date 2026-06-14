"""SARIF 2.1.0 export — one `run` per tool (docs/API_CONTRACT.md)."""

from __future__ import annotations

from typing import Any

from app.models import Finding, Tool

SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"

# SARIF `level` per our normalized severity.
_SEVERITY_TO_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}

_TOOL_DRIVER_NAMES = {
    Tool.gitleaks: "gitleaks",
    Tool.semgrep: "semgrep",
    Tool.trivy: "trivy",
}


def build_sarif(findings: list[Finding]) -> dict[str, Any]:
    """Build a SARIF 2.1.0 document with one `run` per tool present."""
    by_tool: dict[Tool, list[Finding]] = {}
    for finding in findings:
        by_tool.setdefault(finding.tool, []).append(finding)

    runs: list[dict[str, Any]] = []
    for tool in Tool:
        tool_findings = by_tool.get(tool)
        if not tool_findings:
            continue
        runs.append(_build_run(tool, tool_findings))

    return {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": runs,
    }


def _build_run(tool: Tool, findings: list[Finding]) -> dict[str, Any]:
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    for finding in findings:
        rule_id = finding.rule_id
        if rule_id not in rules:
            rule_def: dict[str, Any] = {
                "id": rule_id,
                "name": finding.title,
                "shortDescription": {"text": finding.title},
            }
            tags = []
            if finding.cwe:
                tags.append(finding.cwe)
            if finding.owasp:
                tags.append(finding.owasp)
            if tags:
                rule_def["properties"] = {"tags": tags}
            rules[rule_id] = rule_def

        result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": _SEVERITY_TO_LEVEL.get(finding.severity.value, "warning"),
            "message": {"text": finding.message or finding.title},
            "properties": {
                "severity": finding.severity.value,
                "cwe": finding.cwe,
                "owasp": finding.owasp,
            },
        }

        if finding.file_path:
            location: dict[str, Any] = {
                "physicalLocation": {
                    "artifactLocation": {"uri": finding.file_path},
                }
            }
            if finding.line_start is not None:
                region: dict[str, Any] = {"startLine": int(finding.line_start)}
                if finding.line_end is not None:
                    region["endLine"] = int(finding.line_end)
                location["physicalLocation"]["region"] = region
            result["locations"] = [location]

        results.append(result)

    return {
        "tool": {
            "driver": {
                "name": _TOOL_DRIVER_NAMES[tool],
                "informationUri": _driver_info_uri(tool),
                "rules": list(rules.values()),
            }
        },
        "results": results,
    }


def _driver_info_uri(tool: Tool) -> str:
    return {
        Tool.gitleaks: "https://github.com/gitleaks/gitleaks",
        Tool.semgrep: "https://github.com/semgrep/semgrep",
        Tool.trivy: "https://github.com/aquasecurity/trivy",
    }[tool]
