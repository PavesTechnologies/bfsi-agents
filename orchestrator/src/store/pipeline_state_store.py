"""In-memory store for paused pipeline state."""

from typing import Any, Dict

_store: Dict[str, Dict[str, Any]] = {}


def save_state(application_id: str, state: Dict[str, Any]) -> None:
    _store[application_id] = state


def get_state(application_id: str) -> Dict[str, Any] | None:
    return _store.get(application_id)


def clear_state(application_id: str) -> None:
    _store.pop(application_id, None)
