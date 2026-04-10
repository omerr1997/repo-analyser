from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from repo_analyser.agent import build_agent
from repo_analyser.config import Settings
from repo_analyser.memory_store import MemoryStore
from repo_analyser.tooling import REGISTERED_TOOL_DOCSTRINGS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the repo analyser scaffold.")
    parser.add_argument(
        "--prompt",
        default="What can you do right now?",
        help="Prompt to send to the agent.",
    )
    parser.add_argument(
        "--show-tools",
        action="store_true",
        help="Print tool names and stored docstrings before execution.",
    )
    return parser.parse_args()


def extract_text(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        lines: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = str(item.get("text", "")).strip()
                if text:
                    lines.append(text)
        return "\n".join(lines).strip()
    return str(content).strip()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()
    memory_store = MemoryStore(settings.memory_path)
    agent = build_agent(settings, memory_store)

    if args.show_tools:
        for tool_name, docstring in sorted(REGISTERED_TOOL_DOCSTRINGS.items()):
            print(f"{tool_name}: {docstring}")
        print()

    result = agent.invoke({"messages": [{"role": "user", "content": args.prompt.strip()}]})
    print(extract_text(result["messages"][-1]))


if __name__ == "__main__":
    main()
