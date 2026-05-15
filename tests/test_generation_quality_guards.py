import unittest

import Generator_not as gen
from core.generator.melody_local import smart_generate_classic


def _note_end(note):
    return float(note[0]) + float(note[2])


class GenerationQualityGuardTests(unittest.TestCase):
    def test_melody_local_classic_respects_bar_bounds(self):
        bars = 4
        notes = smart_generate_classic(bars, theme="Freestyle", energy=5)
        self.assertIsInstance(notes, list)
        self.assertGreater(len(notes), 0)

        max_time = float(bars * 4)
        for n in notes:
            self.assertGreaterEqual(float(n[0]), 0.0)
            self.assertGreater(float(n[2]), 0.0)
            self.assertLessEqual(_note_end(n), max_time + 1e-6)

    def test_sax_solo_is_monophonic_and_time_bounded(self):
        bars = 4
        notes = gen.smart_generate(
            bars,
            theme="Freestyle",
            energy=5,
            style="Sax",
        )
        self.assertIsInstance(notes, list)
        self.assertGreater(len(notes), 0)

        max_time = float(bars * 4)
        sorted_notes = sorted(notes, key=lambda n: float(n[0]))
        prev_end = -1.0
        for n in sorted_notes:
            start = float(n[0])
            dur = float(n[2])
            self.assertGreaterEqual(start, 0.0)
            self.assertGreater(dur, 0.0)
            self.assertLessEqual(_note_end(n), max_time + 1e-6)
            self.assertGreaterEqual(start + 1e-6, prev_end)
            prev_end = max(prev_end, _note_end(n))

    def test_boom_bap_loop_respects_bar_bounds(self):
        bars = 4
        notes = gen.smart_generate(
            bars,
            theme="Freestyle",
            energy=5,
            style="Boombap Loop",
            boombap_variation=55,
        )
        self.assertIsInstance(notes, list)
        self.assertGreater(len(notes), 0)

        max_time = float(bars * 4)
        for n in notes:
            self.assertGreaterEqual(float(n[0]), 0.0)
            self.assertGreater(float(n[2]), 0.0)
            self.assertLessEqual(_note_end(n), max_time + 1e-6)

    def test_chords_mode_generates_polyphony(self):
        notes = gen.chord_generate(4, theme="Freestyle", energy=5)
        self.assertIsInstance(notes, list)
        self.assertGreater(len(notes), 0)

        # Expect at least one simultaneous onset with multiple pitches.
        by_start = {}
        for n in notes:
            start = round(float(n[0]), 4)
            by_start.setdefault(start, set()).add(int(n[1]))
        self.assertTrue(any(len(pitches) >= 2 for pitches in by_start.values()))


if __name__ == "__main__":
    unittest.main()
