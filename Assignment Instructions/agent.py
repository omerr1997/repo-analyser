from __future__ import annotations

from langchain.agents import create_agent
from langchain_openrouter import ChatOpenRouter

from config import Settings
from memory_store import MemoryStore
from tools import build_tools


SYSTEM_PROMPT = """
You are a repository-analysis agent scaffold.

Behavior rules:
- Be honest about current limitations.
- Do not claim repository knowledge you do not actually have.
- Use tools only when they materially help.
- Do not invent side effects, file changes, or external calls.
- Keep answers concise and professional.

Current scope:
- The agent is intentionally bootstrapped with placeholder behavior only.
- If the user asks for repository analysis, explain that the analysis tools are not wired yet.
""".strip()


def build_agent(settings: Settings, memory_store: MemoryStore):
    model = ChatOpenRouter(
        model=settings.model_name,
        api_key=settings.openrouter_api_key,
        temperature=0,
        max_tokens=settings.max_output_tokens,
        openrouter_provider={"data_collection": "deny"},
    )

    return create_agent(
        model=model,
        tools=build_tools(memory_store),
        system_prompt=SYSTEM_PROMPT,
        name="repo_analyser_agent",
    )
