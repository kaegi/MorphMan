from morph.morphemes import replaceBracketContents
from morph.morphemes import replaceRoundBracketContents
import unittest

class TestIgnoreBracketsMorphemizer(unittest.TestCase):

    def test_ignore_square_brackets(self):
        sentence_1 = "[こんにちは]私の名前は[シャン]です。"
        case_1 = "私の名前はです。"
        self.assertEqual(replaceBracketContents(sentence_1), case_1)

    def test_ignore_round_brackets(self):
        sentence_1 = "(こんにちは)私の名前は(シャン)です。"
        case_1 = "私の名前はです。"
        self.assertEqual(replaceRoundBracketContents(sentence_1), case_1)

    def test_ignore_round_brackets_japanese(self):
        sentence_1 = "（こんにちは）私の名前は（シャン）です。"
        case_1 = "私の名前はです。"
        self.assertEqual(replaceRoundBracketContents(sentence_1), case_1)

if __name__ == '__main__':
    unittest.main()
