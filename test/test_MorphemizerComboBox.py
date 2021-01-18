import unittest

from PyQt5.QtWidgets import QApplication
from morph.UI import MorphemizerComboBox
from morph.morphemizer_registry import MorphemizerRegistry
from morph.morphemizer import SpaceMorphemizer, MecabMorphemizer, JiebaMorphemizer, \
  CjkCharMorphemizer


class TestMorphemizerComboBox(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])
        self.morphemizerManager = MorphemizerRegistry()

    def test_set_and_get_current(self):
        self.morphemizerManager.addMorphemizer(SpaceMorphemizer())
        self.morphemizerManager.addMorphemizer(MecabMorphemizer())
        self.morphemizerManager.addMorphemizer(JiebaMorphemizer())
        self.morphemizerManager.addMorphemizer(CjkCharMorphemizer())

        combobox = MorphemizerComboBox(self.morphemizerManager)
        combobox.setCurrentByName('MecabMorphemizer')
        self.assertEqual(combobox.currentText(), 'Japanese MorphMan')

        current = combobox.getCurrent()
        self.assertEqual(current.getDescription(), 'Japanese MorphMan')

    def test_empty_morphemizer_list(self):
        combobox = MorphemizerComboBox()
        combobox.setCurrentByName('AnyBecauseNothingExists')

        current = combobox.getCurrent()
        self.assertIsNone(current)


if __name__ == '__main__':
    unittest.main()
