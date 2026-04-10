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
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def get(self, namespace: str, key: str) -> Any | None:
        self._validate_label("namespace", namespace)
        self._validate_label("key", key)
        return self._data.get(namespace, {}).get(key)

    def put(self, namespace: str, key: str, value: Any) -> None:
        self._validate_label("namespace", namespace)
        self._validate_label("key", key)
        self._data.setdefault(namespace, {})[key] = value
        self._flush()

    def list_namespace(self, namespace: str) -> dict[str, Any]:
        self._validate_label("namespace", namespace)
        return dict(self._data.get(namespace, {}))

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}

        try:
            raw_data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Memory store file is not valid JSON: {self.path}"
            ) from exc

        if not isinstance(raw_data, dict):
            raise ValueError("Memory store root must be a JSON object.")

        normalized: dict[str, dict[str, Any]] = {}
        for namespace, values in raw_data.items():
            if not isinstance(namespace, str) or not isinstance(values, dict):
                raise ValueError("Memory store content must be a string-to-object mapping.")
            normalized[namespace] = values
        return normalized

    def _flush(self) -> None:
        self.path.write_text(
            json.dumps(self._data, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _validate_label(label: str, value: str) -> None:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{label} must not be empty.")
        if len(cleaned) > 120:
            raise ValueError(f"{label} is too long.")
