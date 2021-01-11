from morph.morphemizer import MecabMorphemizer
import unittest


class TestMecabMorphemizer(unittest.TestCase):
    def setUp(self):
        self.morphemizer = MecabMorphemizer()

    def test_morpheme_generation(self):
        sentence_1 = "こんにちは。私の名前はシャンです。"
        case_1 = ["こんにちは", "私", "の", "名前", "は", "シャン", "です"]
        for idx, m in enumerate(self.morphemizer.getMorphemesFromExpr(sentence_1)):
            self.assertEqual(m.base, case_1[idx])


if __name__ == '__main__':
    unittest.main()
