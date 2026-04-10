from __future__ import annotations

import argparse
import re
from typing import Any

from agent import build_agent
from config import Settings
from memory_store import MemoryStore
from tooling import REGISTERED_TOOL_DOCSTRINGS


SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the repository-analysis boilerplate agent."
    )
    parser.add_argument(
        "--prompt",
        default="What can you do right now?",
        help="Prompt to send to the agent.",
    )
    parser.add_argument(
        "--thread-id",
        default="bootstrap-thread",
        help="Lightweight thread identifier used for invocation metadata.",
    )
    parser.add_argument(
        "--show-tools",
        action="store_true",
        help="Print registered tool names and stored docstrings before execution.",
    )
    return parser.parse_args()


def validate_identifier(value: str, label: str) -> str:
    cleaned = value.strip()
    if not SAFE_ID_PATTERN.fullmatch(cleaned):
        raise ValueError(
            f"{label} must contain only letters, numbers, underscores, or hyphens."
        )
    return cleaned


def validate_prompt(prompt: str, max_chars: int) -> str:
    cleaned = prompt.strip()
    if not cleaned:
        raise ValueError("Prompt must not be empty.")
    if len(cleaned) > max_chars:
        raise ValueError(f"Prompt exceeds the limit of {max_chars} characters.")
    return cleaned


def extract_text(message: Any) -> str:
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


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()
    prompt = validate_prompt(args.prompt, settings.max_prompt_chars)
    thread_id = validate_identifier(args.thread_id, "thread_id")

    memory_store = MemoryStore(settings.memory_path)
    agent = build_agent(settings, memory_store)

    if args.show_tools:
        for tool_name, docstring in REGISTERED_TOOL_DOCSTRINGS.items():
            print(f"{tool_name}: {docstring}")
        print()

    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": settings.max_iterations,
        },
    )

    final_message = result["messages"][-1]
    print(extract_text(final_message))


if __name__ == "__main__":
    main()
