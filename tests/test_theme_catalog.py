import unittest

import Pamet_a_archiv as db


class ThemeCatalogTests(unittest.TestCase):
    def test_base_theme_catalog_is_simplified(self):
        _, themes = db.get_producers_and_themes()
        self.assertIn("Dark", themes)
        self.assertIn("Melancholic", themes)
        self.assertIn("Lo-Fi Chill", themes)
        self.assertIn("Hard Boom Bap", themes)
        self.assertIn("Jazzy", themes)
        self.assertIn("Dreamy", themes)
        self.assertIn("Experimental", themes)

        self.assertNotIn("Aggressive", themes)
        self.assertNotIn("Street", themes)
        self.assertNotIn("Rainy Night", themes)
        self.assertNotIn("Sad Piano", themes)
        self.assertNotIn("Soulful", themes)


if __name__ == "__main__":
    unittest.main()

