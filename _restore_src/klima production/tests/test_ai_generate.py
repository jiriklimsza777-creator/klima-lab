import unittest

from core.generator import ai_generate as ai


class AiGenerateTests(unittest.TestCase):
    def test_extract_note_array_from_wrapped_text(self):
        content = "Neco pred\n[[0, 60, 0.5, 90], [0.5, 62, 0.5, 88]]\nNeco po"
        out = ai._extract_note_array(content)
        self.assertEqual(out, "[[0, 60, 0.5, 90], [0.5, 62, 0.5, 88]]")

    def test_limit_density_keeps_monophonic_for_lead(self):
        notes = [
            [0.0, 60, 0.5, 70],
            [0.0, 64, 0.5, 95],  # same start, higher velocity should win
            [1.0, 62, 0.5, 80],
            [1.0, 65, 0.5, 75],
            [4.0, 67, 0.5, 88],
            [4.0, 69, 0.5, 91],
        ]
        out = ai._limit_density(notes, bars=2, role="Lead", counter_style="Smooth", creativity=50)
        starts = [float(n[0]) for n in out]
        self.assertEqual(len(starts), len(set(starts)))
        by_start = {float(n[0]): n for n in out}
        self.assertEqual(int(by_start[0.0][1]), 64)
        self.assertEqual(int(by_start[4.0][1]), 69)

    def test_normalize_ai_chords_produces_bar_aligned_chords(self):
        raw = [
            [0.0, 60, 0.5, 100], [0.25, 64, 0.5, 90], [0.5, 67, 0.5, 85],
            [4.0, 62, 0.5, 99], [4.25, 65, 0.5, 91], [4.5, 69, 0.5, 86],
            [8.0, 59, 0.5, 98], [8.25, 63, 0.5, 90], [8.5, 67, 0.5, 84],
            [12.0, 57, 0.5, 97], [12.25, 60, 0.5, 89], [12.5, 64, 0.5, 83],
        ]
        out = ai._normalize_ai_chords(raw, "Freestyle", bars=4, energy=5, creativity=50)
        self.assertIsInstance(out, list)
        self.assertGreaterEqual(len(out), 12)  # 4 bars * 3 notes
        starts = sorted({float(n[0]) for n in out})
        self.assertEqual(starts, [0.0, 4.0, 8.0, 12.0])
        for n in out:
            self.assertEqual(float(n[2]), 4.0)
            self.assertGreaterEqual(int(n[3]), 1)
            self.assertLessEqual(int(n[3]), 127)

    def test_normalize_ai_chords_fallback_when_too_sparse(self):
        raw_sparse = [[0.0, 60, 0.5, 100], [4.0, 62, 0.5, 99]]
        out = ai._normalize_ai_chords(raw_sparse, "Freestyle", bars=4, energy=5, creativity=50)
        self.assertIsInstance(out, list)
        self.assertGreaterEqual(len(out), 9)  # fallback loop should return usable chord set


if __name__ == "__main__":
    unittest.main()

