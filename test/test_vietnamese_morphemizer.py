from morph.morphemizer import getMorphemizerByName
import unittest

class TestVietnameseMorphemizer(unittest.TestCase):
    def setUp(self):
        self.morphemizer = getMorphemizerByName("VietnameseMorphemizer")

    def test_morpheme_generation(self):
        if self.morphemizer is not None:
            sentence_1 = ("Trăm năm trong cõi người ta,"
                          " Chữ tài chữ mệnh khéo là ghét nhau."
                          " Trải qua một cuộc bể dâu,"
                          " Những điều trông thấy mà đau đớn lòng.")

            case_1 = ["trăm năm", "trong", "cõi", "người ta", "chữ", "tài", "chữ", "mệnh",
                      "khéo", "là", "ghét", "nhau", "trải", "qua", "một", "cuộc", "bể dâu",
                      "những", "điều", "trông", "thấy", "mà", "đau đớn", "lòng"]

            sentence_2 = "Mặt Trời"

            case_2 = ["mặt trời"]

            for idx, m in enumerate(self.morphemizer.getMorphemesFromExpr(sentence_1)):
                self.assertEqual(m.base, case_1[idx])

            for idx, m in enumerate(self.morphemizer.getMorphemesFromExpr(sentence_2)):
                self.assertEqual(m.base, case_2[idx])

        else:
            print('\npyvi is not installed, skipping Vietnamese tests')


if __name__ == '__main__':
    unittest.main()
