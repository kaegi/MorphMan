import unittest

from test import fake_aqt
from morph.morphemes import replaceBracketContents
from morph.preferences import init_preferences, get_preference, update_preferences

class TestIgnoreBracketsMorphemizer(unittest.TestCase):

    def setUp(self):
        fake_aqt.init_collection()
        init_preferences()

    def test_ignore_square_brackets(self):
        sentence_1 = "[こんにちは]私の名前は[シャン]です。"
        case_1 = "私の名前はです。"

        self.assertEqual(get_preference('Option_IgnoreBracketContents'), False)
        self.assertEqual(replaceBracketContents(sentence_1), sentence_1)

        update_preferences({'Option_IgnoreBracketContents': True})
        self.assertEqual(replaceBracketContents(sentence_1), case_1)

    def test_ignore_round_brackets_slim(self):
        sentence_1 = "(こんにちは)私の名前は(シャン)です。"
        case_1 = "私の名前はです。"

        self.assertEqual(get_preference('Option_IgnoreSlimRoundBracketContents'), False)
        self.assertEqual(replaceBracketContents(sentence_1), sentence_1)

        update_preferences({'Option_IgnoreSlimRoundBracketContents': True})
        self.assertEqual(replaceBracketContents(sentence_1), case_1)

    def test_ignore_round_brackets_japanese(self):
        sentence_1 = "（こんにちは）私の名前は（シャン）です。"
        case_1 = "私の名前はです。"

        self.assertEqual(get_preference('Option_IgnoreRoundBracketContents'), False)
        self.assertEqual(replaceBracketContents(sentence_1), sentence_1)

        update_preferences({'Option_IgnoreRoundBracketContents': True})
        self.assertEqual(replaceBracketContents(sentence_1), case_1)

if __name__ == '__main__':
    unittest.main()

