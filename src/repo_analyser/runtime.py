from __future__ import annotations

from typing import Any

from .agent import build_agent
from .config import Settings
from .memory_store import MemoryStore


def run_agent_turn(user_message: str) -> dict[str, Any]:
    settings = Settings.from_env()
    memory_store = MemoryStore(settings.memory_path)
    agent = build_agent(settings, memory_store)

    result = agent.invoke({"messages": [{"role": "user", "content": user_message.strip()}]})
    messages = result["messages"]

    return {
        "answer": _extract_text(messages[-1]),
        "trace": _build_trace(messages),
        "toolsUsed": _get_tools_used(messages),
    }


def _build_trace(messages: list[Any]) -> list[dict[str, Any]]:
    tool_calls: dict[str, dict[str, Any]] = {}
    trace: list[dict[str, Any]] = []

    for message in messages:
        for tool_call in getattr(message, "tool_calls", []) or []:
            tool_calls[tool_call["id"]] = {
                "id": tool_call["id"],
                "tool": tool_call["name"],
                "input": tool_call.get("args", {}),
            }

        tool_call_id = getattr(message, "tool_call_id", None)
        if not tool_call_id:
            continue

        call = tool_calls.get(
            tool_call_id,
            {"id": tool_call_id, "tool": "unknown", "input": {}},
        )
        output = _extract_text(message)
        trace.append(
            {
                "id": call["id"],
                "tool": call["tool"],
                "input": call["input"],
                "output": output,
                "kind": "thought" if call["tool"] == "think" else "tool",
                "label": _build_trace_label(call["tool"], call["input"]),
            }
        )

    return trace


def _get_tools_used(messages: list[Any]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for message in messages:
        for tool_call in getattr(message, "tool_calls", []) or []:
            tool_name = str(tool_call.get("name", "")).strip()
            if tool_name and tool_name not in seen:
                seen.add(tool_name)
                ordered.append(tool_name)
    return ordered


def _build_trace_label(tool_name: str, tool_input: Any) -> str:
    if tool_name == "think":
        note = ""
        if isinstance(tool_input, dict):
            note = str(tool_input.get("note", "")).strip()
        if note:
            return f"Reasoning note: {note[:80]}"
        return "Reasoning note"

    if isinstance(tool_input, dict) and tool_input:
        first_key = next(iter(tool_input))
        value = str(tool_input[first_key]).strip()
        return f"{tool_name}: {value[:80]}"

    return tool_name


def _extract_text(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = str(item.get("text", "")).strip()
                if text:
                    parts.append(text)
        return "\n".join(parts).strip()
    return str(content).strip()
