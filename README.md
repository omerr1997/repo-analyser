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

Another direction worth exploring for a longer version of the project is graph-based repository mapping. The idea is to take a repository and represent it as a graph of functions, calls, and data flow so the system can better explain how code paths connect and how execution moves through the project. One option that appears especially relevant for this kind of deeper exploration is GitNexus.

From my experience using GitNexus in a different repository, it seems capable of significantly improving understanding of repository structure, component relationships, and how one part of the system leads to another. That kind of mapping can make it easier to write a stronger summary of what a project is doing, how it should be used, and where it could be improved. It also seems like a strong candidate to use alongside an agent, since it can handle a meaningful portion of the structural heavy lifting before the agent begins higher-level reasoning and write-up work.

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

For a single local startup command, use:

```bash
./run.sh
```

The React UI supports:

- minimal text chat with the agent
- a terminal-inspired black-and-green workspace
- hoverable agent trace summaries attached to the agent badge
- Enter to submit and Shift+Enter for a new line
- persisted thread context between chat turns through the local memory store

The trace view is intentionally a readable reasoning summary and tool log, not raw hidden chain-of-thought.

If your editor says it cannot find modules like `repo_analyser.config`, install the project in editable mode from the repository root:

```bash
pip install -e .
```

That registers `src/repo_analyser` as a proper local package and usually fixes import resolution in IDEs and terminals.

If OpenRouter reports a credit or token-budget issue, reduce the response cap with:

```bash
OPENROUTER_MAX_OUTPUT_TOKENS=800
```

The app now defaults to a conservative output cap to avoid oversized requests on limited credits.
When this happens during runtime, the app will return a readable assistant message instead of a backend crash, including guidance to lower the token cap or replace the API key.
