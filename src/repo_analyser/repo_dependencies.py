from __future__ import annotations

from pathlib import Path
import json
import re
import tomllib

from .osv_client import DependencySpec


REQUIREMENTS_PATTERN = re.compile(r"^\s*([A-Za-z0-9_.-]+)==([^\s#]+)\s*$")
PACKAGE_VERSION_PREFIXES = ("^", "~", ">", "<", "=", "*")


def discover_repository_dependencies(repo_path: Path) -> tuple[list[DependencySpec], list[str], list[str]]:
    specs: list[DependencySpec] = []
    sources: list[str] = []
    skipped: list[str] = []

    for requirements_file in sorted(repo_path.rglob("requirements*.txt")):
        parsed, rejected = _parse_requirements_file(requirements_file)
        specs.extend(parsed)
        if parsed:
            sources.append(requirements_file.relative_to(repo_path).as_posix())
        skipped.extend(f"{requirements_file.name}: {item}" for item in rejected)

    pyproject_file = repo_path / "pyproject.toml"
    if pyproject_file.exists():
        parsed, rejected = _parse_pyproject_file(pyproject_file)
        specs.extend(parsed)
        if parsed:
            sources.append(pyproject_file.relative_to(repo_path).as_posix())
        skipped.extend(f"{pyproject_file.name}: {item}" for item in rejected)

    package_json = repo_path / "package.json"
    if package_json.exists():
        parsed, rejected = _parse_package_json(package_json)
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
            lines.append(f"- {spec.name}=={spec.version} ({spec.ecosystem})")
    else:
        lines.append("No exact dependency versions were discovered in supported manifest files.")
        lines.append(
            "Repository-level vulnerability results should not be treated as confirmed until exact versions are found."
        )

    if skipped:
        lines.append("")
        lines.append("Skipped or unsupported dependency entries:")
        lines.extend(f"- {entry}" for entry in skipped[:30])

    return "\n".join(lines).strip()


def _parse_requirements_file(path: Path) -> tuple[list[DependencySpec], list[str]]:
    parsed: list[DependencySpec] = []
    rejected: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = REQUIREMENTS_PATTERN.fullmatch(line)
        if not match:
            rejected.append(line)
            continue
        parsed.append(
            DependencySpec(name=match.group(1), version=match.group(2), ecosystem="PyPI")
        )

    return parsed, rejected


def _parse_pyproject_file(path: Path) -> tuple[list[DependencySpec], list[str]]:
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
        if not match:
            rejected.append(item)
            continue
        parsed.append(
            DependencySpec(name=match.group(1), version=match.group(2), ecosystem="PyPI")
        )

    return parsed, rejected


def _parse_package_json(path: Path) -> tuple[list[DependencySpec], list[str]]:
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
            if not cleaned or cleaned.startswith(PACKAGE_VERSION_PREFIXES):
                rejected.append(f"{name}: {cleaned}")
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
