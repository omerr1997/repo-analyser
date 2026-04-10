from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


DEFAULT_MODEL = "openai/gpt-4.1-mini"


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str
    model_name: str
    memory_path: Path
    downloaded_repos_path: Path
    tavily_api_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required.")

        model_name = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        memory_path = Path(os.getenv("AGENT_MEMORY_PATH", "data/agent-memory.json"))
        downloaded_repos_path = Path(
            os.getenv("DOWNLOADED_REPOS_PATH", "downloaded-repos")
        )
        tavily_api_key = os.getenv("TAVILY_API_KEY", "").strip()

        return cls(
            openrouter_api_key=api_key,
            model_name=model_name,
            memory_path=memory_path,
            downloaded_repos_path=downloaded_repos_path,
            tavily_api_key=tavily_api_key,
        )
