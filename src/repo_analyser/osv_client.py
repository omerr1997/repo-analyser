from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import requests


OSV_QUERY_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class DependencySpec:
    name: str
    version: str
    ecosystem: str


def query_dependency_vulnerabilities(specs: list[DependencySpec]) -> list[dict[str, Any]]:
    if not specs:
        return []

    payload = {
        "queries": [
            {
                "version": spec.version,
                "package": {
                    "name": spec.name,
                    "ecosystem": spec.ecosystem,
                },
            }
            for spec in specs
        ]
    }

    response = requests.post(
        OSV_QUERY_BATCH_URL,
        json=payload,
        timeout=OSV_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    body = response.json()
    results = body.get("results", [])
    return results if isinstance(results, list) else []


def format_vulnerability_results(
    specs: list[DependencySpec],
    results: list[dict[str, Any]],
    rejected: list[str],
) -> str:
    lines: list[str] = []

    if rejected:
        lines.append("Skipped entries:")
        lines.extend(f"- {entry}" for entry in rejected)
        lines.append("")

    if not specs:
        lines.append(
            "No valid dependency entries were found. Use lines like 'requests==2.25.0'."
        )
        return "\n".join(lines).strip()

    vulnerable_count = 0
    for spec, result in zip(specs, results, strict=False):
        vulns = result.get("vulns", []) if isinstance(result, dict) else []
        label = f"{spec.name} {spec.version}"

        if not vulns:
            lines.append(f"{label}: no known vulnerabilities found.")
            continue

        vulnerable_count += 1
        vuln_ids = [str(vuln.get("id", "unknown")) for vuln in vulns[:5] if isinstance(vuln, dict)]
        lines.append(f"{label}: {len(vulns)} known vulnerability finding(s).")
        if vuln_ids:
            lines.append("  IDs: " + ", ".join(vuln_ids))

    if vulnerable_count == 0 and specs:
        lines.append("")
        lines.append("Summary: no known vulnerabilities were found for the checked dependencies.")
    elif vulnerable_count > 0:
        lines.append("")
        lines.append(
            f"Summary: {vulnerable_count} out of {len(specs)} checked dependencies had known vulnerability findings."
        )

    return "\n".join(lines).strip()
