from __future__ import annotations

from typing import Any


MAX_RESULTS = 5
MAX_CONTENT_CHARS = 400


def search_web(query: str, api_key: str) -> str:
    try:
        from tavily import TavilyClient
    except ImportError as exc:
        raise RuntimeError(
            "Tavily search requires the 'tavily-python' package to be installed."
        ) from exc

    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        max_results=MAX_RESULTS,
        search_depth="basic",
        include_answer=True,
        include_raw_content=False,
    )
    return _format_search_response(response)


def _format_search_response(response: dict[str, Any]) -> str:
    lines: list[str] = []

    answer = str(response.get("answer", "")).strip()
    if answer:
        lines.append(f"Answer: {answer}")

    results = response.get("results", [])
    if not isinstance(results, list) or not results:
        if not lines:
            return "No web results were found."
        return "\n".join(lines)

    lines.append("Sources:")
    for index, result in enumerate(results[:MAX_RESULTS], start=1):
        if not isinstance(result, dict):
            continue

        title = str(result.get("title", "Untitled")).strip() or "Untitled"
        url = str(result.get("url", "")).strip()
        content = str(result.get("content", "")).strip().replace("\n", " ")
        snippet = content[:MAX_CONTENT_CHARS]
        if len(content) > MAX_CONTENT_CHARS:
            snippet = f"{snippet}..."

        lines.append(f"{index}. {title}")
        if url:
            lines.append(f"   URL: {url}")
        if snippet:
            lines.append(f"   Snippet: {snippet}")

    return "\n".join(lines)
