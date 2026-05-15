import unittest
from types import SimpleNamespace
from unittest.mock import patch

import ui.pages as pages


class UiRegressionTests(unittest.TestCase):
    def test_generated_title_contains_producer_theme_and_timestamp(self):
        title = pages._build_generated_title("Nujabes", "Lo-Fi Chill", 0)
        self.assertIn("Nujabes", title)
        self.assertIn("Lo-Fi Chill", title)
        self.assertIn("| 1", title)
        self.assertRegex(title, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")

    def test_dataset_generate_works_without_producer_or_theme_selection(self):
        fake_notes = [
            [0.0, 60, 0.5, 90],
            [0.5, 64, 0.5, 95],
            [1.0, 67, 0.5, 92],
            [1.5, 55, 1.0, 88],
        ]
        fake_session = {
            "current_theme_string": "",
            "dataset_theme_influence": 20,
            "dataset_output_mode": "Melodie + akordy",
            "chord_voicing_mode": "Tight",
        }
        fake_st = SimpleNamespace(session_state=fake_session)

        with patch.object(pages, "st", fake_st):
            with patch.object(pages, "_dataset_midi_paths", return_value=[__file__]):
                with patch.object(pages.sound, "import_midi_bytes", return_value=(fake_notes, 90, "Piano")):
                    result = pages._generate_from_dataset(4)

        self.assertIsInstance(result, dict)
        self.assertIn("melody", result)
        self.assertIn("layers", result)
        self.assertIsInstance(result["melody"], list)
        self.assertGreater(len(result["melody"]), 0)
        for note in result["melody"]:
            self.assertIsInstance(note, (list, tuple))
            self.assertGreaterEqual(len(note), 4)


if __name__ == "__main__":
    unittest.main()
