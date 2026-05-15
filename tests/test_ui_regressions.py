import unittest
from types import SimpleNamespace
from unittest.mock import patch

import ui.pages as pages
from core.generator.theme_profiles import build_theme_profile, get_producer_profile


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

    def test_split_dataset_overlap_only_prefers_higher_as_lead(self):
        notes = [
            [0.0, 48, 1.0, 90],
            [0.0, 60, 1.0, 90],
            [1.0, 50, 1.0, 90],
            [1.0, 62, 1.0, 90],
        ]
        lead, chords = pages._split_dataset_lead_chords(notes)
        self.assertGreater(len(lead), 0)
        self.assertGreater(len(chords), 0)
        self.assertTrue(all(int(n[1]) >= 60 for n in lead))
        self.assertTrue(all(int(n[1]) <= 50 for n in chords))

    def test_split_dataset_isolated_uses_p75_threshold(self):
        notes = [
            [0.0, 40, 0.5, 90],
            [1.0, 50, 0.5, 90],
            [2.0, 60, 0.5, 90],
            [3.0, 70, 0.5, 90],
        ]
        lead, chords = pages._split_dataset_lead_chords(notes)
        lead_p = sorted(int(n[1]) for n in lead)
        chords_p = sorted(int(n[1]) for n in chords)
        # P75 for [40,50,60,70] is 62.5 -> only 70 should be in lead.
        self.assertEqual(lead_p, [70])
        self.assertEqual(chords_p, [40, 50, 60])

    def test_split_dataset_threshold_equal_goes_to_chords(self):
        notes = [
            [0.0, 60, 0.5, 90],
            [1.0, 60, 0.5, 90],
            [2.0, 60, 0.5, 90],
            [3.0, 60, 0.5, 90],
        ]
        lead, chords = pages._split_dataset_lead_chords(notes)
        self.assertEqual(len(lead), 1)  # fallback keeps lead non-empty
        self.assertGreaterEqual(len(chords), 1)
        self.assertTrue(all(int(n[1]) == 60 for n in lead + chords))

    def test_split_dataset_mixed_overlap_and_isolated(self):
        notes = [
            [0.0, 50, 1.0, 90],
            [0.0, 64, 1.0, 90],  # overlap pair
            [2.0, 55, 0.5, 90],  # isolated
            [3.0, 72, 0.5, 90],  # isolated high
        ]
        lead, chords = pages._split_dataset_lead_chords(notes)
        self.assertGreater(len(lead), 0)
        self.assertGreater(len(chords), 0)
        self.assertTrue(any(int(n[1]) >= 64 for n in lead))
        self.assertTrue(any(int(n[1]) <= 55 for n in chords))

    def test_split_dataset_empty(self):
        lead, chords = pages._split_dataset_lead_chords([])
        self.assertEqual(lead, [])
        self.assertEqual(chords, [])

    def test_evaluate_melody_differs_for_daringer_vs_metro(self):
        # Same melody, different producer profiles => different quality score.
        notes = [
            [0.0, 56, 0.5, 90],
            [0.5, 60, 0.5, 92],
            [1.0, 63, 0.5, 94],
            [1.5, 67, 0.5, 96],
            [2.0, 70, 0.5, 94],
            [2.5, 74, 0.5, 92],
            [3.0, 77, 0.5, 90],
            [3.5, 81, 0.5, 88],
        ]
        theme_profile = build_theme_profile("Dark")
        score_daringer = pages._evaluate_melody(
            notes,
            4,
            producer_profile=get_producer_profile("Daringer"),
            theme_profile=theme_profile,
        )
        score_metro = pages._evaluate_melody(
            notes,
            4,
            producer_profile=get_producer_profile("Metro Boomin"),
            theme_profile=theme_profile,
        )
        self.assertNotEqual(float(score_daringer), float(score_metro))


if __name__ == "__main__":
    unittest.main()
