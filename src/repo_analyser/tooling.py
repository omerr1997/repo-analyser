from __future__ import annotations

from collections.abc import Callable
import inspect
from typing import Any

from langchain.tools import tool as langchain_tool

from repo_analyser.tool_docstrings import TOOL_DOCSTRINGS


REGISTERED_TOOL_DOCSTRINGS: dict[str, str] = {}


def tracked_tool(
    func: Callable[..., Any] | None = None,
    /,
    **tool_kwargs: Any,
) -> Any:
    def decorator(inner: Callable[..., Any]) -> Any:
        tool_name = tool_kwargs.get("name") or inner.__name__
        docstring = TOOL_DOCSTRINGS.get(tool_name) or inspect.getdoc(inner)
        if not docstring:
            raise ValueError(f"Tool '{tool_name}' is missing a docstring.")

        inner.__doc__ = docstring
        REGISTERED_TOOL_DOCSTRINGS[tool_name] = docstring
        return langchain_tool(**tool_kwargs)(inner)

    if func is not None:
        return decorator(func)
    return decorator
