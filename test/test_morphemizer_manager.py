from morph.morphemizer import Morphemizer
from morph.morphemizer_registry import MorphemizerManager
import unittest

class TestMorphemizerManager(unittest.TestCase):
    def setUp(self):
        self.registry = MorphemizerManager()

    def test_get_morphemizer_by_name(self):
        morphemizer = TestMorphemizer()
        self.registry.addMorphemizer(morphemizer)
        self.assertEqual(self.registry.getMorphemizer('TestMorphemizer'), morphemizer)

    def test_add_morphemizer_emits_added_event(self):
        morphemizer = TestMorphemizer()
        self.registry.morphemizer_added.connect(lambda m: self.assertEqual(m, morphemizer))
        self.registry.addMorphemizer(morphemizer)

class TestMorphemizer(Morphemizer):
    def __init__(self):
        super(TestMorphemizer, self).__init__()


if __name__ == '__main__':
    unittest.main()
