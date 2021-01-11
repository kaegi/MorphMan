from morph.morphemizer import Morphemizer
from morph.morphemizer_registry import MorphemizerRegistry
import unittest

class TestMorphemizerRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = MorphemizerRegistry()

    def test_get_morphemizer_by_name(self):
        morphemizer = TestMorphemizer()
        self.registry.addMorphemizer(morphemizer)
        self.assertEqual(self.registry.getMorphemizer('TestMorphemizer'), morphemizer)

    def test_add_morphemizer_emits_added_event(self):
        morphemizer = TestMorphemizer()
        self.registry.morphemizer_added.connect(lambda m: self.assertEqual(m, morphemizer))
        self.registry.addMorphemizer(morphemizer)

class TestMorphemizer(Morphemizer):
    pass


if __name__ == '__main__':
    unittest.main()
