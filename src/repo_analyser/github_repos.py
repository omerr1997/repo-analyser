from __future__ import annotations

from pathlib import Path
import io
import re
import shutil
import zipfile

import requests


GITHUB_REPO_PATTERN = re.compile(
    r"^(?:https://github\.com/)?(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
REQUEST_TIMEOUT_SECONDS = 30


def parse_repository_reference(repository: str) -> tuple[str, str]:
    cleaned = repository.strip()
    match = GITHUB_REPO_PATTERN.fullmatch(cleaned)
    if not match:
        raise ValueError(
            "Repository must be in 'owner/repo' format or a GitHub repository URL."
        )

    owner = match.group("owner")
    repo = match.group("repo")
    return owner, repo


def get_downloaded_repository_path(owner: str, repo: str, base_dir: Path) -> Path:
    return Path(base_dir) / owner / repo


def get_default_branch(owner: str, repo: str) -> str:
    repo_api_url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(repo_api_url, timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code != 200:
        raise ValueError(
            f"Could not fetch repository metadata for '{owner}/{repo}' (status {response.status_code})."
        )

    repo_info = response.json()
    default_branch = str(repo_info.get("default_branch", "main")).strip()
    return default_branch or "main"


def download_repository_archive(owner: str, repo: str, base_dir: Path) -> tuple[Path, str]:
    branch_name = get_default_branch(owner, repo)
    archive_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch_name}.zip"

    response = requests.get(archive_url, timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code != 200:
        raise ValueError(
            f"Could not download '{owner}/{repo}' from branch '{branch_name}' (status {response.status_code})."
        )

    destination = get_downloaded_repository_path(owner, repo, base_dir)
    if destination.exists():
        shutil.rmtree(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        top_level_folder = _get_archive_root_folder(archive)
        temp_extract_dir = destination.parent / f".{repo}-tmp"
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)

        archive.extractall(temp_extract_dir)
        shutil.move(str(temp_extract_dir / top_level_folder), str(destination))
        shutil.rmtree(temp_extract_dir, ignore_errors=True)

    return destination, branch_name


def _get_archive_root_folder(archive: zipfile.ZipFile) -> str:
    root_names = []
    for info in archive.infolist():
        parts = Path(info.filename).parts
        if parts:
            root_names.append(parts[0])

    if not root_names:
        raise ValueError("Downloaded repository archive was empty.")

    return root_names[0]
