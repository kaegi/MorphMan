
from PyQt6.QtWidgets import QComboBox


class MorphemizerComboBox(QComboBox):

    def setMorphemizers(self, morphemizers):
        if type(morphemizers) == list:
            self.morphemizers = morphemizers
        else:
            self.morphemizers = []

        for morphemizer in self.morphemizers:
            self.addItem(morphemizer.getDescription())

        self.setCurrentIndex(0)

    def getCurrent(self):
        try:
            return self.morphemizers[self.currentIndex()]
        except IndexError:
            return None

    def setCurrentByName(self, name):
        active = False
        for i, morphemizer in enumerate(self.morphemizers):
            if morphemizer.getName() == name:
                active = i
        if active:
            self.setCurrentIndex(active)

