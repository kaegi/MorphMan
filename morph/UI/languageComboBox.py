
from PyQt6.QtWidgets import QComboBox


class LanguageComboBox(QComboBox):

    def setLanguages(self, languages):
        if type(languages) == list:
            self.languages = languages
        else:
            self.languages = ['Default']

        for language in self.languages:
            self.addItem(language)

        self.setCurrentIndex(0)

    def getCurrent(self):
        try:
            return self.languages[self.currentIndex()]
        except IndexError:
            return None

    def setCurrentByName(self, name):
        active = False
        for i, language in enumerate(self.languages):
            if language == name:
                active = i
        if active:
            self.setCurrentIndex(active)

