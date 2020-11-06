import unittest

from PyQt5.QtWidgets import QApplication
from morph.UI import MorphemizerComboBox
from morph.morphemizer import getAllMorphemizers


class TestMorphemizerComboBox(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])

    def test_set_and_get_current(self):
        combobox = MorphemizerComboBox()
        combobox.setMorphemizers(getAllMorphemizers())
        combobox.setCurrentByName('MecabMorphemizer')
        self.assertEqual(combobox.currentText(), 'Japanese MorphMan')

        current = combobox.getCurrent()
        self.assertEqual(current.getDescription(), 'Japanese MorphMan')

    def test_empty_morphemizer_list(self):
        combobox = MorphemizerComboBox()
        combobox.setMorphemizers([])
        combobox.setCurrentByName('AnyBecauseNothingExists')

        current = combobox.getCurrent()
        self.assertIsNone(current)


if __name__ == '__main__':
    unittest.main()
