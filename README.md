# Repo Analyser

This repository keeps the provided assignment materials in `Assignment Instructions/` unchanged.

Project progress is tracked in `steps-ive-taken.txt`, which records the running history of decisions and implementation steps taken during the project.

The project scaffold lives under `src/repo_analyser/` and currently includes:

- OpenRouter for LLM usage
- LangChain agent wiring for a ReAct-style scaffold
- A lightweight local `MemoryStore`
- Separate files for tools, tool docstrings, and the custom `@tracked_tool` decorator
- A FastAPI API layer for frontend communication
- A React workspace for voice input, chat, and trace inspection

## Notes on Approaches Considered

In addition to the current LangChain-based scaffold, I also looked into existing approaches that might already solve part of the assignment out of the box.

One option I reviewed was LlamaIndex. From my current understanding, it offers building blocks for ingesting codebases and repositories and is aligned with the kind of assignment we received: understanding a repository, surfacing relevant structure, and helping answer questions about issues, weaknesses, and other repository-level concerns. It is being tracked here as a relevant alternative approach that may be useful to revisit as the implementation evolves.

Run the scaffold with:

```bash
pip install -e .
python main.py --show-tools
```

Run the API locally with:

```bash
uvicorn repo_analyser.server:app --reload
```

Run the React UI locally with:

```bash
cd frontend
npm install
npm run dev
```

The React UI supports:

- text chat with the agent
- browser voice input when speech recognition is available
- answer playback through browser speech synthesis
- a toggleable trace layer that shows tool order and short reasoning summaries
- hover and focus details for individual trace steps

The trace view is intentionally a readable reasoning summary and tool log, not raw hidden chain-of-thought.

If your editor says it cannot find modules like `repo_analyser.config`, install the project in editable mode from the repository root:

```bash
pip install -e .
```

That registers `src/repo_analyser` as a proper local package and usually fixes import resolution in IDEs and terminals.
