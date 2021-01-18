from PyQt5.QtCore import QObject, pyqtSignal
from anki.hooks import addHook
from aqt import mw

from .deps.spacy import init_spacy
from .morphemizer import SpaceMorphemizer, MecabMorphemizer, JiebaMorphemizer, CjkCharMorphemizer


class MorphemizerRegistry(QObject):
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


def createMorphemizerRegistry():
    morphemizerRegistry = MorphemizerRegistry()
    morphemizerRegistry.addMorphemizer(SpaceMorphemizer())
    morphemizerRegistry.addMorphemizer(MecabMorphemizer())
    morphemizerRegistry.addMorphemizer(JiebaMorphemizer())
    morphemizerRegistry.addMorphemizer(CjkCharMorphemizer())

    init_spacy(morphemizerRegistry)

    return morphemizerRegistry


def _initializeMorphemizerRegistry():
    mw.morphemizerRegistry = createMorphemizerRegistry()


addHook('profileLoaded', _initializeMorphemizerRegistry)
