import unittest

import Generator_not as gen


def _is_note_list(notes):
    if not isinstance(notes, list):
        return False
    for n in notes:
        if not isinstance(n, (list, tuple)) or len(n) < 3:
            return False
    return True


class BridgeRuntimeSmokeTests(unittest.TestCase):
    def test_smart_generate_classic_mode_smoke(self):
        notes = gen.smart_generate(4, theme="Freestyle", energy=5, style="Klasicky")
        self.assertTrue(_is_note_list(notes))
        self.assertGreater(len(notes), 0)

    def test_smart_generate_solo_mode_smoke(self):
        notes = gen.smart_generate(4, theme="Freestyle", energy=5, style="Sax")
        self.assertTrue(_is_note_list(notes))
        self.assertGreater(len(notes), 0)

    def test_smart_generate_loop_mode_smoke(self):
        notes = gen.smart_generate(4, theme="Freestyle", energy=5, style="Boombap Loop")
        self.assertTrue(_is_note_list(notes))
        self.assertGreater(len(notes), 0)

    def test_chord_generate_smoke(self):
        notes = gen.chord_generate(4, theme="Freestyle", energy=5)
        self.assertTrue(_is_note_list(notes))
        self.assertGreater(len(notes), 0)


if __name__ == "__main__":
    unittest.main()

