from __future__ import annotations

from typing import Any

from .agent import build_agent
from .config import Settings
from .memory_store import MemoryStore

CHAT_HISTORY_NAMESPACE = "chat_threads"
MAX_HISTORY_MESSAGES = 12


def run_agent_turn(user_message: str, thread_id: str) -> dict[str, Any]:
    settings = Settings.from_env()
    memory_store = MemoryStore(settings.memory_path)
    agent = build_agent(settings, memory_store)
    conversation = _get_conversation_history(memory_store, thread_id)
    conversation.append({"role": "user", "content": user_message.strip()})

    try:
        result = agent.invoke({"messages": conversation})
    except Exception as exc:
        return _build_runtime_error_response(exc, settings.max_output_tokens)

    messages = result["messages"]
    answer = _extract_text(messages[-1])
    _store_conversation_history(
        memory_store=memory_store,
        thread_id=thread_id,
        messages=conversation + [{"role": "assistant", "content": answer}],
    )

    return {
        "answer": answer,
        "trace": _build_trace(messages),
        "toolsUsed": _get_tools_used(messages),
    }


def _build_runtime_error_response(error: Exception, max_output_tokens: int) -> dict[str, Any]:
    message = _build_runtime_error_message(error, max_output_tokens)
    return {
        "answer": message,
        "trace": [],
        "toolsUsed": [],
    }


def _build_runtime_error_message(error: Exception, max_output_tokens: int) -> str:
    error_text = str(error).strip()
    lowered = error_text.lower()
    token_failure_signals = (
        "requires more credits",
        "fewer max_tokens",
        "paymentrequiredresponseerror",
        "insufficient credits",
        "run out of token",
        "out of token",
    )

    if any(signal in lowered for signal in token_failure_signals):
        return (
            "OpenRouter could not complete the request because the account appears to be "
            "out of credits or the token budget is too high for the current balance.\n\n"
            "What you can do:\n"
            "1. Replace the API key with another OpenRouter key that has available credits.\n"
            "2. Lower OPENROUTER_MAX_OUTPUT_TOKENS and retry.\n"
            f"Current configured output cap: {max_output_tokens} tokens."
        )

    return (
        "The agent hit a runtime error while processing the request.\n\n"
        f"Details: {error_text or error.__class__.__name__}"
    )


def _build_trace(messages: list[Any]) -> list[dict[str, Any]]:
    tool_calls: dict[str, dict[str, Any]] = {}
    trace: list[dict[str, Any]] = []

    for message in messages:
        # LangChain returns tool calls and tool outputs as separate message objects.
        # We collect calls first, then pair each tool result back to its originating call.
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


def _get_conversation_history(
    memory_store: MemoryStore,
    thread_id: str,
) -> list[dict[str, str]]:
    raw_history = memory_store.get(CHAT_HISTORY_NAMESPACE, thread_id)
    if not isinstance(raw_history, list):
        return []

    history: list[dict[str, str]] = []
    for item in raw_history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip()
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            history.append({"role": role, "content": content})
    return history


def _store_conversation_history(
    memory_store: MemoryStore,
    thread_id: str,
    messages: list[dict[str, str]],
) -> None:
    trimmed_messages = messages[-MAX_HISTORY_MESSAGES:]
    memory_store.put(CHAT_HISTORY_NAMESPACE, thread_id, trimmed_messages)
