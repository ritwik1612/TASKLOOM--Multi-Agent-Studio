from __future__ import annotations

from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

import pytest

from history_store import list_runs, load_run, save_run


def test_history_create_update_and_reopen():
    with TemporaryDirectory() as directory, patch("history_store.application_data_dir", return_value=Path(directory)):
        run_id = save_run("Write a short speech", {"final_answer": "First draft"})
        assert len(list_runs()) == 1
        assert load_run(run_id)["approved"] is False

        save_run("Write a short speech", {"final_answer": "First draft"},
                 run_id=run_id, approved=True, final_output="Approved text")
        restored = load_run(run_id)
        assert restored["created_at"]
        assert restored["final_output"] == "Approved text"
        assert restored["approved"] is True
        assert len(list_runs()) == 1


def test_history_rejects_path_traversal():
    with TemporaryDirectory() as directory, patch("history_store.application_data_dir", return_value=Path(directory)):
        with pytest.raises(ValueError):
            load_run("../outside")
