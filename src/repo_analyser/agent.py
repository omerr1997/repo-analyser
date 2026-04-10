from __future__ import annotations

from langchain.agents import create_agent
from langchain_openrouter import ChatOpenRouter

from repo_analyser.config import Settings
from repo_analyser.memory_store import MemoryStore
from repo_analyser.tools import build_tools


SYSTEM_PROMPT = """
You are a repository-analysis agent scaffold.

Be concise, honest, and professional.
Do not claim to analyze repositories yet.
Use tools only when they help answer directly.
""".strip()


def build_agent(settings: Settings, memory_store: MemoryStore):
    model = ChatOpenRouter(
        model=settings.model_name,
        api_key=settings.openrouter_api_key,
        temperature=0,
    )

    return create_agent(
        model=model,
        tools=build_tools(
            memory_store=memory_store,
            downloaded_repos_path=settings.downloaded_repos_path,
            tavily_api_key=settings.tavily_api_key,
        ),
        system_prompt=SYSTEM_PROMPT,
    )
