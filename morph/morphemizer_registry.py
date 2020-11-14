from PyQt5.QtCore import QObject, pyqtSignal

class MorphemizerManager(QObject):
    morphemizer_added = pyqtSignal(object)
    morphemizer_removed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.morphemizers = {}

    def addMorphemizer(self, morphemizer):
        if morphemizer.getName() not in self.morphemizers:
            self.morphemizers[morphemizer.getName()] = morphemizer
            self.morphemizer_added.emit(morphemizer)

    def addMorphemizers(self, morphemizers):
        for morphemizer in morphemizers:
            self.addMorphemizer(morphemizer)

    def removeMorphemizer(self, name):
        morphemizer = self.morphemizers.pop(name, None)
        if morphemizer:
            self.morphemizer_removed.emit(morphemizer)
        return morphemizer

    def getMorphemizers(self):
        return list(self.morphemizers.values())

    def getMorphemizer(self, name):
        return self.morphemizers.get(name)
