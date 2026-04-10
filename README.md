# Repo Analyser

Repo Analyser is a lightweight repository-analysis assistant built to download GitHub repositories, inspect their structure, follow implementation details, and surface early dependency or security findings through a simple chat interface.

The project combines a small agent backend with a minimal frontend so you can ask questions about downloaded repositories, inspect files, review tool activity, and gradually move toward deeper code-analysis workflows.

This repository keeps the provided assignment materials in `Assignment Instructions/` unchanged.

Project progress is tracked in `steps-ive-taken.txt`, which records the running history of decisions and implementation steps taken during the project.

The current project includes:

- OpenRouter for LLM usage
- LangChain agent wiring for a ReAct-style scaffold
- A lightweight local `MemoryStore`
- Separate files for tools, tool docstrings, and the custom `@tracked_tool` decorator
- A FastAPI API layer for frontend communication
- A React workspace for minimal chat and trace inspection
- Tools for downloading repositories and reading local repository files
- OSV-based dependency vulnerability checking for package versions
- Repository-aware dependency discovery before vulnerability reporting
- Estimated dependency-version fallback when exact package pins are not available
- A constrained web-search tool for repository and code-analysis topics

## Notes on Approaches Considered

In addition to the current LangChain-based scaffold, I also looked into existing approaches that might already solve part of the assignment out of the box.

One option I reviewed was LlamaIndex. From my current understanding, it offers building blocks for ingesting codebases and repositories and is aligned with the kind of assignment we received: understanding a repository, surfacing relevant structure, and helping answer questions about issues, weaknesses, and other repository-level concerns. It is being tracked here as a relevant alternative approach that may be useful to revisit as the implementation evolves.

Another direction worth exploring for a longer version of the project is graph-based repository mapping. The idea is to take a repository and represent it as a graph of functions, calls, and data flow so the system can better explain how code paths connect and how execution moves through the project. One option that appears especially relevant for this kind of deeper exploration is GitNexus.

From my experience using GitNexus in a different repository, it seems capable of significantly improving understanding of repository structure, component relationships, and how one part of the system leads to another. That kind of mapping can make it easier to write a stronger summary of what a project is doing, how it should be used, and where it could be improved. It also seems like a strong candidate to use alongside an agent, since it can handle a meaningful portion of the structural heavy lifting before the agent begins higher-level reasoning and write-up work.

## Findings and Future Uses

At this stage, the project is best understood as a basic LLM agent that can download repositories, inspect them, retain some conversation context, and provide early guidance about what is inside a project. That is useful, but it is still only a first layer of what a stronger repository-analysis system would need.

A more complete version of the project would likely use multiple analysis layers instead of relying on one generic agent step:

- a structure layer that maps files, folders, entrypoints, requirements, and major project components
- a deeper code layer that follows classes, functions, authentication, and data flow across the repository itself
- a dependency and weakness layer that looks for vulnerable packages and known security issues
- a bug and code-flow layer that identifies suspicious logic, risky data movement, and likely implementation problems
- a final synthesis layer where the LLM combines all findings into a write-up of strengths, weaknesses, risks, and recommendations

This suggests a future architecture that is closer to a multi-step workflow, potentially with something like LangGraph, where each node is responsible for a specific kind of repository analysis and the final LLM step produces the explanation and summary for the user.

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
