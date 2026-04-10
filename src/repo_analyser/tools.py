from __future__ import annotations

from hashlib import sha1

from repo_analyser.memory_store import MemoryStore
from repo_analyser.tooling import tracked_tool


def build_tools(memory_store: MemoryStore) -> list:
    @tracked_tool
    def get_agent_status() -> str:
        return "The agent scaffold is ready, but repository analysis is not implemented yet."

    @tracked_tool
    def save_note(note: str) -> str:
        note = note.strip()
        if not note:
            return "Skipped saving an empty note."

        key = sha1(note.encode("utf-8")).hexdigest()[:12]
        memory_store.put("notes", key, {"note": note})
        return f"Saved note as '{key}'."

    return [get_agent_status, save_note]
