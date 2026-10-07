from __future__ import annotations
from threading import Lock
from uuid import uuid4

_store = {}
_lock = Lock()

def save_notes(notes) -> str:
    note_id = str(uuid4())
    with _lock:
        _store[note_id] = {"notes": notes, "visual_status": "pending"}
    return note_id

def get_notes(note_id: str):
    with _lock:
        record = _store.get(note_id)
        return record["notes"] if record else None

def update_notes(note_id: str, notes) -> bool:
    with _lock:
        record = _store.get(note_id)
        if not record:
            return False
        record["notes"] = notes
        return True

def set_visual_status(note_id: str, status: str) -> bool:
    with _lock:
        record = _store.get(note_id)
        if not record:
            return False
        record["visual_status"] = status
        return True

def get_visual_status(note_id: str) -> str | None:
    with _lock:
        record = _store.get(note_id)
        return record["visual_status"] if record else None
