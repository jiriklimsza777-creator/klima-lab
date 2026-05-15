import unittest
from types import SimpleNamespace
from unittest.mock import patch

import ui.cards as cards


class _SessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


class CardsRegressionTests(unittest.TestCase):
    def test_save_project_to_archive_uses_dataset_source_type(self):
        fake_state = _SessionState({"note_density": "Normál", "note_role": "Lead", "bpm": 90})
        fake_st = SimpleNamespace(session_state=fake_state, toast=lambda _msg: None)
        project = {
            "title": "T",
            "theme": "X",
            "main_instrument": "Rhodes Piano",
            "melody": [[0.0, 60, 0.5, 90]],
            "melody_style": "Dataset Style",
        }

        with patch.object(cards, "st", fake_st):
            with patch.object(cards, "project_to_payload", return_value={"ok": 1}):
                with patch.object(cards.db, "save_to_db") as save_mock:
                    cards.save_project_to_archive(project, rating=5)

        kwargs = save_mock.call_args.kwargs
        self.assertEqual(kwargs.get("source_type"), "dataset")

    def test_sync_project_instrument_from_state_prefers_widget_value(self):
        session_state = {"sel_std_0": "Flute"}
        project = {"main_instrument": "Acoustic Grand Piano"}
        key = cards._sync_project_instrument_from_state(project, 0, cards.ENGINE_STUDIO, session_state)
        self.assertEqual(key, "sel_std_0")
        self.assertEqual(project["main_instrument"], "Flute")

    def test_sync_project_instrument_from_state_seeds_default(self):
        session_state = {}
        project = {}
        key = cards._sync_project_instrument_from_state(project, 1, cards.ENGINE_STUDIO, session_state)
        self.assertEqual(key, "sel_std_1")
        self.assertEqual(session_state["sel_std_1"], "Acoustic Grand Piano")


if __name__ == "__main__":
    unittest.main()
