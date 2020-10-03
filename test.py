import unittest
from ja_helper import *


class TestStringMethods(unittest.TestCase):
    def test_verb_progressive_parse(self):
        self.assertEqual([m.surface() for m in parse("思っている")], ["思っ", "て", "いる"])

    def test_verb_progressive_composition(self):
        self.assertTrue(MultiMorpheme(parse("思っている")).composition_check())

    def test_verb_progressive_post_parse(self):
        morphs = parse("思っている")
        self.assertEqual(post_parse(morphs), [MultiMorpheme(morphs)])


if __name__ == "__main__":
    unittest.main()
