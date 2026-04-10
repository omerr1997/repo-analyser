from __future__ import annotations

from pathlib import Path
import json
import re
import tomllib
from urllib.parse import quote

import requests
from .osv_client import DependencySpec


REQUIREMENTS_PATTERN = re.compile(r"^\s*([A-Za-z0-9_.-]+)==([^\s#]+)\s*$")
REQUIREMENT_NAME_PATTERN = re.compile(r"^\s*([A-Za-z0-9_.-]+)")
PACKAGE_VERSION_PREFIXES = ("^", "~", ">", "<", "=", "*")
PYPI_URL_TEMPLATE = "https://pypi.org/pypi/{name}/json"
NPM_URL_TEMPLATE = "https://registry.npmjs.org/{name}"
REQUEST_TIMEOUT_SECONDS = 15


def discover_repository_dependencies(repo_path: Path) -> tuple[list[DependencySpec], list[str], list[str]]:
    specs: list[DependencySpec] = []
    sources: list[str] = []
    skipped: list[str] = []
    version_cache: dict[tuple[str, str], str | None] = {}

    for requirements_file in sorted(repo_path.rglob("requirements*.txt")):
        parsed, rejected = _parse_requirements_file(requirements_file, version_cache)
        specs.extend(parsed)
        if parsed:
            sources.append(requirements_file.relative_to(repo_path).as_posix())
        skipped.extend(f"{requirements_file.name}: {item}" for item in rejected)

    pyproject_file = repo_path / "pyproject.toml"
    if pyproject_file.exists():
        parsed, rejected = _parse_pyproject_file(pyproject_file, version_cache)
        specs.extend(parsed)
        if parsed:
            sources.append(pyproject_file.relative_to(repo_path).as_posix())
        skipped.extend(f"{pyproject_file.name}: {item}" for item in rejected)

    package_json = repo_path / "package.json"
    if package_json.exists():
        parsed, rejected = _parse_package_json(package_json, version_cache)
        specs.extend(parsed)
        if parsed:
            sources.append(package_json.relative_to(repo_path).as_posix())
        skipped.extend(f"{package_json.name}: {item}" for item in rejected)

    return _dedupe_specs(specs), sorted(set(sources)), _dedupe_strings(skipped)


def format_discovered_dependencies(
    specs: list[DependencySpec],
    sources: list[str],
    skipped: list[str],
) -> str:
    lines: list[str] = []

    if sources:
        lines.append("Dependency sources:")
        lines.extend(f"- {source}" for source in sources)
        lines.append("")

    if specs:
        lines.append("Dependencies found:")
        for spec in specs:
            details = f"- {spec.name}=={spec.version} ({spec.ecosystem})"
            if spec.estimated:
                details += f" [estimated from '{spec.source_requirement or 'non-exact spec'}']"
            lines.append(details)
    else:
        lines.append("No dependencies could be resolved from supported manifest files.")

    if skipped:
        lines.append("")
        lines.append("Skipped or unresolved dependency entries:")
        lines.extend(f"- {entry}" for entry in skipped[:30])

    return "\n".join(lines).strip()


def _parse_requirements_file(
    path: Path,
    version_cache: dict[tuple[str, str], str | None],
) -> tuple[list[DependencySpec], list[str]]:
    parsed: list[DependencySpec] = []
    rejected: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = REQUIREMENTS_PATTERN.fullmatch(line)
        if match:
            parsed.append(
                DependencySpec(name=match.group(1), version=match.group(2), ecosystem="PyPI")
            )
            continue

        estimated = _build_estimated_spec(line, "PyPI", version_cache)
        if estimated is None:
            rejected.append(line)
            continue
        parsed.append(estimated)

    return parsed, rejected


def _parse_pyproject_file(
    path: Path,
    version_cache: dict[tuple[str, str], str | None],
) -> tuple[list[DependencySpec], list[str]]:
    parsed: list[DependencySpec] = []
    rejected: list[str] = []

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    groups: list[str] = []
    if isinstance(project, dict):
        groups.extend(project.get("dependencies", []) or [])
        optional = project.get("optional-dependencies", {}) or {}
        if isinstance(optional, dict):
            for values in optional.values():
                groups.extend(values or [])

    for item in groups:
        if not isinstance(item, str):
            continue
        match = REQUIREMENTS_PATTERN.fullmatch(item.strip())
        if match:
            parsed.append(
                DependencySpec(name=match.group(1), version=match.group(2), ecosystem="PyPI")
            )
            continue

        estimated = _build_estimated_spec(item, "PyPI", version_cache)
        if estimated is None:
            rejected.append(item)
            continue
        parsed.append(estimated)

    return parsed, rejected


def _parse_package_json(
    path: Path,
    version_cache: dict[tuple[str, str], str | None],
) -> tuple[list[DependencySpec], list[str]]:
    parsed: list[DependencySpec] = []
    rejected: list[str] = []

    data = json.loads(path.read_text(encoding="utf-8"))
    dependency_maps = []
    if isinstance(data, dict):
        dependency_maps.append(data.get("dependencies", {}) or {})
        dependency_maps.append(data.get("devDependencies", {}) or {})

    for dep_map in dependency_maps:
        if not isinstance(dep_map, dict):
            continue
        for name, version in dep_map.items():
            if not isinstance(name, str) or not isinstance(version, str):
                continue
            cleaned = version.strip()
            if not cleaned:
                rejected.append(f"{name}: {cleaned}")
                continue
            if cleaned.startswith(PACKAGE_VERSION_PREFIXES):
                estimated = _build_estimated_spec(
                    f"{name} {cleaned}",
                    "npm",
                    version_cache,
                    explicit_name=name,
                )
                if estimated is None:
                    rejected.append(f"{name}: {cleaned}")
                    continue
                parsed.append(estimated)
                continue
            parsed.append(DependencySpec(name=name, version=cleaned, ecosystem="npm"))

    return parsed, rejected


def _dedupe_specs(specs: list[DependencySpec]) -> list[DependencySpec]:
    seen: dict[tuple[str, str, str], DependencySpec] = {}
    for spec in specs:
        seen[(spec.name, spec.version, spec.ecosystem)] = spec
    return list(seen.values())


def _dedupe_strings(values: list[str]) -> list[str]:
    return sorted(set(values))


def _build_estimated_spec(
    raw_requirement: str,
    ecosystem: str,
    version_cache: dict[tuple[str, str], str | None],
    *,
    explicit_name: str = "",
) -> DependencySpec | None:
    package_name = explicit_name.strip() or _extract_requirement_name(raw_requirement)
    if not package_name:
        return None

    resolved_version = _resolve_latest_version(package_name, ecosystem, version_cache)
    if not resolved_version:
        return None

    return DependencySpec(
        name=package_name,
        version=resolved_version,
        ecosystem=ecosystem,
        estimated=True,
        source_requirement=raw_requirement.strip(),
    )


def _extract_requirement_name(raw_requirement: str) -> str:
    match = REQUIREMENT_NAME_PATTERN.match(raw_requirement.strip())
    if not match:
        return ""
    return match.group(1)


def _resolve_latest_version(
    package_name: str,
    ecosystem: str,
    version_cache: dict[tuple[str, str], str | None],
) -> str | None:
    cache_key = (ecosystem, package_name.lower())
    if cache_key in version_cache:
        return version_cache[cache_key]

    try:
        if ecosystem == "PyPI":
            url = PYPI_URL_TEMPLATE.format(name=quote(package_name, safe=""))
            response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            body = response.json()
            version = str(body.get("info", {}).get("version", "")).strip() or None
        elif ecosystem == "npm":
            url = NPM_URL_TEMPLATE.format(name=quote(package_name, safe="@"))
            response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            body = response.json()
            version = str(body.get("dist-tags", {}).get("latest", "")).strip() or None
        else:
            version = None
    except (requests.RequestException, ValueError, json.JSONDecodeError):
        version = None

    version_cache[cache_key] = version
    return version
