from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Any


@dataclass
class MemoryStore:
    path: Path
    _data: dict[str, dict[str, Any]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def get(self, namespace: str, key: str) -> Any | None:
        return self._data.get(namespace, {}).get(key)

    def put(self, namespace: str, key: str, value: Any) -> None:
        self._data.setdefault(namespace, {})[key] = value
        self.path.write_text(
            json.dumps(self._data, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}

        return {
            str(namespace): value
            for namespace, value in raw.items()
            if isinstance(value, dict)
        }
