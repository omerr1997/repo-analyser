from __future__ import annotations

from hashlib import sha1
from pathlib import Path

from repo_analyser.github_repos import (
    download_repository_archive,
    get_downloaded_repository_path,
    parse_repository_reference,
)
from repo_analyser.memory_store import MemoryStore
from repo_analyser.tooling import tracked_tool


def build_tools(memory_store: MemoryStore, downloaded_repos_path: Path) -> list:
    @tracked_tool
    def get_agent_status() -> str:
        return "The agent scaffold is ready, but repository analysis is not implemented yet."

    @tracked_tool
    def save_note(note: str) -> str:
        note = note.strip()
        if not note:
            return "Skipped saving an empty note."

        key = sha1(note.encode("utf-8")).hexdigest()[:12]
        memory_store.put("notes", key, {"note": note})
        return f"Saved note as '{key}'."

    @tracked_tool
    def download_github_repository(repository: str) -> str:
        owner, repo = parse_repository_reference(repository)
        extracted_path, branch_name = download_repository_archive(
            owner=owner,
            repo=repo,
            base_dir=downloaded_repos_path,
        )
        return (
            f"Downloaded '{owner}/{repo}' from branch '{branch_name}' to "
            f"'{extracted_path.as_posix()}'."
        )

    @tracked_tool
    def is_github_repository_downloaded(repository: str) -> str:
        owner, repo = parse_repository_reference(repository)
        local_path = get_downloaded_repository_path(
            owner=owner,
            repo=repo,
            base_dir=downloaded_repos_path,
        )
        if local_path.exists():
            return f"Yes. '{owner}/{repo}' is already available at '{local_path.as_posix()}'."
        return f"No. '{owner}/{repo}' has not been downloaded yet."

    return [
        get_agent_status,
        save_note,
        download_github_repository,
        is_github_repository_downloaded,
    ]
