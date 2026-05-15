import unittest

import Generator_not as gen


class GeneratorBridgeTests(unittest.TestCase):
    def test_legacy_aliases_exist(self):
        self.assertTrue(callable(getattr(gen, "_smart_generate_legacy", None)))
        self.assertTrue(callable(getattr(gen, "_generate_sax_solo_legacy", None)))
        self.assertTrue(callable(getattr(gen, "_generate_piano_solo_legacy", None)))
        self.assertTrue(callable(getattr(gen, "_generate_trumpet_solo_legacy", None)))
        self.assertTrue(callable(getattr(gen, "_generate_flute_solo_legacy", None)))
        self.assertTrue(callable(getattr(gen, "_generate_marimba_solo_legacy", None)))
        self.assertTrue(callable(getattr(gen, "_generate_vibraphone_solo_legacy", None)))
        self.assertTrue(callable(getattr(gen, "_generate_acoustic_bass_solo_legacy", None)))

    def test_public_entrypoints_exist(self):
        self.assertTrue(callable(getattr(gen, "smart_generate", None)))
        self.assertTrue(callable(getattr(gen, "smart_generate_classic", None)))
        self.assertTrue(callable(getattr(gen, "chord_generate", None)))
        self.assertTrue(callable(getattr(gen, "generate_sax_solo", None)))
        self.assertTrue(callable(getattr(gen, "generate_piano_solo", None)))
        self.assertTrue(callable(getattr(gen, "generate_trumpet_solo", None)))


if __name__ == "__main__":
    unittest.main()
