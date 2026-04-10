from __future__ import annotations

from hashlib import sha1

from memory_store import MemoryStore
from tooling import tracked_tool


def build_tools(memory_store: MemoryStore) -> list:
    @tracked_tool
    def get_bootstrap_status() -> str:
        return (
            "The agent scaffold is initialized. Repository-analysis tools are not "
            "enabled yet."
        )

    @tracked_tool
    def remember_internal_note(note: str) -> str:
        cleaned_note = note.strip()
        if not cleaned_note:
            return "No note was stored because the input was empty."
        if len(cleaned_note) > 280:
            return "No note was stored because the note exceeded 280 characters."

        note_key = sha1(cleaned_note.encode("utf-8")).hexdigest()[:12]
        memory_store.put(
            namespace="internal_notes",
            key=note_key,
            value={"note": cleaned_note},
        )
        return f"Stored note under key '{note_key}'."

    return [get_bootstrap_status, remember_internal_note]
