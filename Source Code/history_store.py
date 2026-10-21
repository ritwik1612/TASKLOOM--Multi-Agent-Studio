"""On-device Taskloom conversation history.

The store holds prompts and generated output, never Gemini credentials. Each
conversation is an independent JSON file under the current user's app data.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from paths import application_data_dir


def history_dir() -> Path:
    folder = application_data_dir() / "history"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_run(prompt: str, result: dict, *, run_id: str | None = None,
             approved: bool = False, final_output: str | None = None) -> str:
    """Create or update a run atomically and return its stable ID."""
    run_id = run_id or uuid4().hex
    if not run_id.isalnum():
        raise ValueError("Invalid history ID")
    destination = history_dir() / f"{run_id}.json"
    created_at = datetime.now(timezone.utc).isoformat()
    if destination.exists():
        try:
            created_at = json.loads(destination.read_text(encoding="utf-8")).get("created_at", created_at)
        except (OSError, ValueError, TypeError):
            pass
    record = {
        "id": run_id,
        "created_at": created_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "result": result,
        "approved": approved,
        "final_output": final_output,
    }
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, destination)
    return run_id


def list_runs() -> list[dict]:
    runs: list[dict] = []
    for file in history_dir().glob("*.json"):
        try:
            item = json.loads(file.read_text(encoding="utf-8"))
            if isinstance(item, dict) and item.get("id") == file.stem and "prompt" in item:
                runs.append(item)
        except (OSError, ValueError, TypeError):
            continue
    return sorted(runs, key=lambda item: item.get("updated_at", ""), reverse=True)


def load_run(run_id: str) -> dict:
    if not run_id.isalnum():
        raise ValueError("Invalid history ID")
    record = json.loads((history_dir() / f"{run_id}.json").read_text(encoding="utf-8"))
    if record.get("id") != run_id:
        raise ValueError("Mismatched history ID")
    return record
