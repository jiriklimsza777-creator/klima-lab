import unittest

import Generator_not as gen


class GeneratorSmokeTests(unittest.TestCase):
    def _assert_note_list(self, notes, min_len=1):
        self.assertIsInstance(notes, list)
        self.assertGreaterEqual(len(notes), min_len)
        for note in notes:
            self.assertIsInstance(note, (list, tuple))
            self.assertGreaterEqual(len(note), 4)
            t, p, d, v = note[0], note[1], note[2], note[3]
            self.assertIsInstance(t, (int, float))
            self.assertIsInstance(p, (int, float))
            self.assertIsInstance(d, (int, float))
            self.assertIsInstance(v, (int, float))
            self.assertGreaterEqual(float(t), 0.0)
            self.assertGreater(float(d), 0.0)
            self.assertGreaterEqual(int(v), 1)
            self.assertLessEqual(int(v), 127)

    def test_build_theme_profile_exact_match(self):
        profile = gen._build_theme_profile("Lo-Fi Chill")
        self.assertIsInstance(profile, dict)
        for key in ("scale", "density", "durations", "chords"):
            self.assertIn(key, profile)
        self.assertLess(profile["density"], 1.0)

    def test_build_theme_profile_fallback(self):
        profile = gen._build_theme_profile("Totally Unknown Theme")
        self.assertIsInstance(profile, dict)
        self.assertIn("scale", profile)
        self.assertIn("progression", profile)

    def test_smart_generate_classic_smoke(self):
        notes = gen.smart_generate_classic(4, theme="J Dilla|Lo-Fi Chill", energy=6)
        self._assert_note_list(notes)
        max_time = max(float(n[0]) for n in notes)
        self.assertLess(max_time, 16.0)

    def test_generate_sax_solo_smoke(self):
        notes = gen.generate_sax_solo(theme="Nujabes|Soulful", bars=6, energy=5, character="Klidne", story=True)
        self._assert_note_list(notes)
        max_time = max(float(n[0]) for n in notes)
        self.assertLess(max_time, 24.0)

    def test_generate_piano_solo_smoke(self):
        notes = gen.generate_piano_solo(theme="Nujabes|Soulful", bars=6, energy=5, character="Klidne", story=False)
        self._assert_note_list(notes)
        max_time = max(float(n[0]) for n in notes)
        self.assertLess(max_time, 24.0)

    def test_generate_trumpet_solo_smoke(self):
        notes = gen.generate_trumpet_solo(theme="Nujabes|Soulful", bars=6, energy=5, character="Klidne", story=False)
        self._assert_note_list(notes)
        max_time = max(float(n[0]) for n in notes)
        self.assertLess(max_time, 24.0)

    def test_chord_generate_smoke(self):
        notes = gen.chord_generate(4, theme="DJ Premier|Dark", energy=7)
        self._assert_note_list(notes)
        max_time = max(float(n[0]) for n in notes)
        self.assertLess(max_time, 16.0)


if __name__ == "__main__":
    unittest.main()
