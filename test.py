import unittest
from ja_helper import *


class TestStringMethods(unittest.TestCase):
    def test_verb_progressive(self):
        morphs = parse("思っている")
        self.assertEqual([m.surface() for m in morphs], ["思っ", "て", "いる"])
        M = MultiMorpheme(morphs)
        self.assertTrue(M.composition_check())
        self.assertEqual(post_parse(morphs), [M])

    def test_nss(self):
        morphs = parse("大学院生")
        self.assertEqual([m.surface() for m in morphs], ["大学", "院", "生"])
        M = MultiMorpheme(morphs)
        self.assertTrue(M.composition_check())
        self.assertEqual(post_parse(morphs), [M])

    def test_av(self):
        morphs = parse("そういう")
        self.assertEqual([m.surface() for m in morphs], ["そう", "いう"])
        M = MultiMorpheme(morphs)
        self.assertTrue(M.composition_check())
        self.assertEqual(post_parse(morphs), [M])

if __name__ == "__main__":
    unittest.main()
