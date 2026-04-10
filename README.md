# Repo Analyser

This repository keeps the provided assignment materials in `Assignment Instructions/` unchanged.

The project scaffold lives under `src/repo_analyser/` and currently includes:

- OpenRouter for LLM usage
- LangChain agent wiring for a ReAct-style scaffold
- A lightweight local `MemoryStore`
- Separate files for tools, tool docstrings, and the custom `@tracked_tool` decorator

Run the scaffold with:

```bash
pip install -r requirements.txt
python main.py --show-tools
```
