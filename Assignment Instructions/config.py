from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


DEFAULT_MODEL = "openai/gpt-4.1-mini"
DEFAULT_MAX_PROMPT_CHARS = 4_000
DEFAULT_MAX_ITERATIONS = 4
DEFAULT_MAX_OUTPUT_TOKENS = 600


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str
    model_name: str
    memory_path: Path
    max_prompt_chars: int
    max_iterations: int
    max_output_tokens: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(override=False)

        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required in the environment.")
        if not api_key.startswith("sk-or-v1-"):
            raise ValueError("OPENROUTER_API_KEY does not look like a valid OpenRouter key.")

        model_name = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        memory_path = Path(
            os.getenv(
                "AGENT_MEMORY_PATH",
                Path(__file__).with_name("agent-memory-store.json"),
            )
        )

        return cls(
            openrouter_api_key=api_key,
            model_name=model_name,
            memory_path=memory_path,
            max_prompt_chars=int(
                os.getenv("AGENT_MAX_PROMPT_CHARS", str(DEFAULT_MAX_PROMPT_CHARS))
            ),
            max_iterations=int(
                os.getenv("AGENT_MAX_ITERATIONS", str(DEFAULT_MAX_ITERATIONS))
            ),
            max_output_tokens=int(
                os.getenv("AGENT_MAX_OUTPUT_TOKENS", str(DEFAULT_MAX_OUTPUT_TOKENS))
            ),
        )
