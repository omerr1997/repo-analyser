from __future__ import annotations

from hashlib import sha1
from pathlib import Path
from time import time
import requests

from .github_repos import (
    download_repository_archive,
    get_downloaded_repository_path,
    list_downloaded_repositories as list_local_repositories,
    list_downloaded_repository_files,
    parse_repository_reference,
    read_downloaded_repository_file,
    read_downloaded_repository_text_files,
)
from .memory_store import MemoryStore
from .osv_client import (
    format_vulnerability_results,
    parse_dependency_specs,
    query_dependency_vulnerabilities,
)
from .repo_dependencies import (
    discover_repository_dependencies,
    format_discovered_dependencies,
)
from .tavily_search import search_web
from .tooling import tracked_tool


def build_tools(
    memory_store: MemoryStore,
    downloaded_repos_path: Path,
    tavily_api_key: str,
) -> list:
    @tracked_tool
    def list_downloaded_repositories() -> str:
        repositories = list_local_repositories(downloaded_repos_path)
        if not repositories:
            return "No repositories are currently downloaded."
        return "Downloaded repositories:\n" + "\n".join(repositories)

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
    def get_downloaded_repo_files(
        repository: str,
        get_file_names: bool = True,
        get_file_contents: bool = False,
        specific_file: str = "",
    ) -> str:
        owner, repo = parse_repository_reference(repository)
        local_path = get_downloaded_repository_path(
            owner=owner,
            repo=repo,
            base_dir=downloaded_repos_path,
        )
        if not local_path.exists():
            return f"'{owner}/{repo}' has not been downloaded yet."

        requested_file = specific_file.strip()
        if requested_file:
            content = read_downloaded_repository_file(
                owner=owner,
                repo=repo,
                base_dir=downloaded_repos_path,
                relative_file_path=requested_file,
            )
            if content is None:
                return (
                    f"'{owner}/{repo}' is downloaded, but the file '{requested_file}' "
                    "was not found as readable text."
                )
            return f"--- {requested_file} ---\n{content}"

        responses: list[str] = []

        if get_file_names:
            file_names = list_downloaded_repository_files(
                owner=owner,
                repo=repo,
                base_dir=downloaded_repos_path,
            )
            if not file_names:
                responses.append(f"'{owner}/{repo}' is downloaded, but no files were found.")
            else:
                responses.append("Files:\n" + "\n".join(file_names))

        if get_file_contents:
            all_text = read_downloaded_repository_text_files(
                owner=owner,
                repo=repo,
                base_dir=downloaded_repos_path,
            )
            if not all_text:
                responses.append("No readable text files were found.")
            else:
                responses.append("Contents:\n" + all_text)

        if not responses:
            return (
                "Nothing was requested. Set get_file_names, get_file_contents, "
                "or provide specific_file."
            )

        return "\n\n".join(responses)

    @tracked_tool
    def get_repository_dependencies(repository: str) -> str:
        owner, repo = parse_repository_reference(repository)
        local_path = get_downloaded_repository_path(
            owner=owner,
            repo=repo,
            base_dir=downloaded_repos_path,
        )
        if not local_path.exists():
            return f"'{owner}/{repo}' has not been downloaded yet."

        specs, sources, skipped = discover_repository_dependencies(local_path)
        return format_discovered_dependencies(specs, sources, skipped)

    @tracked_tool
    def check_dependency_vulnerabilities(
        dependencies: str,
        ecosystem: str = "PyPI",
    ) -> str:
        parsed_specs, rejected = parse_dependency_specs(dependencies, ecosystem)
        if not parsed_specs and rejected:
            return format_vulnerability_results([], [], rejected)

        try:
            results = query_dependency_vulnerabilities(parsed_specs)
        except requests.RequestException as exc:
            return f"Dependency vulnerability check failed: {exc}"

        return format_vulnerability_results(parsed_specs, results, rejected)

    @tracked_tool
    def check_repository_dependency_vulnerabilities(repository: str) -> str:
        owner, repo = parse_repository_reference(repository)
        local_path = get_downloaded_repository_path(
            owner=owner,
            repo=repo,
            base_dir=downloaded_repos_path,
        )
        if not local_path.exists():
            return f"'{owner}/{repo}' has not been downloaded yet."

        specs, sources, skipped = discover_repository_dependencies(local_path)
        if not specs:
            return format_discovered_dependencies(specs, sources, skipped)

        try:
            results = query_dependency_vulnerabilities(specs)
        except requests.RequestException as exc:
            return f"Dependency vulnerability check failed: {exc}"

        discovery_section = format_discovered_dependencies(specs, sources, skipped)
        vulnerability_section = format_vulnerability_results(specs, results, [])
        return f"{discovery_section}\n\nVulnerability results:\n{vulnerability_section}"

    @tracked_tool
    def web_search(query: str) -> str:
        query = query.strip()
        if not query:
            return "Search skipped because the query was empty."
        if not tavily_api_key:
            return "Search is unavailable because TAVILY_API_KEY is not configured."
        return search_web(query=query, api_key=tavily_api_key)

    @tracked_tool
    def think(note: str) -> str:
        note = note.strip()
        if not note:
            return "No planning note was recorded."

        key = f"thought-{int(time())}-{sha1(note.encode('utf-8')).hexdigest()[:8]}"
        memory_store.put("thoughts", key, {"note": note})
        return f"Thought recorded under '{key}'."

    return [
        list_downloaded_repositories,
        download_github_repository,
        get_downloaded_repo_files,
        get_repository_dependencies,
        check_dependency_vulnerabilities,
        check_repository_dependency_vulnerabilities,
        web_search,
        think,
    ]
