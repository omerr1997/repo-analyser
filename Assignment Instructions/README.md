# Repo Analyser Boilerplate

## Overview

This scaffold uses:

- OpenRouter for LLM access
- LangChain `create_agent` for a ReAct-style agent runtime
- A lightweight local `MemoryStore` for persistence
- A custom `@tracked_tool` decorator that stores each tool docstring centrally

The current agent is intentionally minimal. It is wired correctly, but it does not perform repository analysis yet.

## File Layout

- `main.py`: CLI entrypoint and basic invocation guardrails
- `agent.py`: LangChain agent construction and system prompt
- `tools.py`: tool definitions only
- `tool_docstrings.py`: centralized tool docstrings
- `tooling.py`: custom tool decorator and docstring registry
- `memory_store.py`: local JSON-backed persistence
- `config.py`: environment-backed settings

## Environment

Required:

- `OPENROUTER_API_KEY`

Optional:

- `OPENROUTER_MODEL`
- `AGENT_MEMORY_PATH`
- `AGENT_MAX_PROMPT_CHARS`
- `AGENT_MAX_ITERATIONS`
- `AGENT_MAX_OUTPUT_TOKENS`

## Install

```bash
pip install -r "Assignment Instructions/requirements.txt"
```

## Run

```bash
python "Assignment Instructions/main.py" --show-tools
python "Assignment Instructions/main.py" --prompt "What can you do right now?"
```

## Guardrails

- Empty and oversized prompts are rejected early.
- Thread identifiers are sanitized.
- Tool docstrings must exist before a tool is registered.
- The agent is instructed not to invent capabilities or side effects.
