# -*- coding: utf-8 -*-
import re

from .morphemes import Morpheme
from .deps.zhon.hanzi import characters
from .mecab_wrapper import getMorphemesMecab, getMecabIdentity
from .deps.jieba import posseg
import importlib.util


####################################################################################################
# Base Class
####################################################################################################

class Morphemizer:
    def getMorphemesFromExpr(self, expression):
        # type: (str) -> [Morpheme]
        """
        The heart of this plugin: convert an expression to a list of its morphemes.
        """
        return []

    def getDescription(self):
        # type: () -> str
        """
        Returns a single line, for which languages this Morphemizer is.
        """
        return 'No information available'

    def getName(self):
        # type: () -> str
        return self.__class__.__name__

    def exists(self):
        # type: () -> Boolean
        return True


####################################################################################################
# Morphemizer Helpers
####################################################################################################

def getAllMorphemizers():
    # type: () -> [Morphemizer]
    morphemizers = [SpaceMorphemizer(), MecabMorphemizer(), JiebaMorphemizer(), VietnameseMorphemizer(), CjkCharMorphemizer()]
    for m in morphemizers:
        if not m.exists():
            morphemizers.remove(m)

    return morphemizers


def getMorphemizerByName(name):
    # type: (str) -> Optional(Morphemizer)
    for m in getAllMorphemizers():
        if m.getName() == name:
            return m
    return None


####################################################################################################
# Mecab Morphemizer
####################################################################################################

space_char_regex = re.compile(' ')

class MecabMorphemizer(Morphemizer):
    """
    Because in japanese there are no spaces to differentiate between morphemes,
    a extra tool called 'mecab' has to be used.
    """

    def getMorphemesFromExpr(self, expression):
        # Remove simple spaces that could be added by other add-ons and break the parsing.
        if space_char_regex.search(expression):
            expression = space_char_regex.sub('', expression)

        return getMorphemesMecab(expression)

    def getDescription(self):
        return 'Japanese ' + getMecabIdentity()


####################################################################################################
# Space Morphemizer
####################################################################################################

class SpaceMorphemizer(Morphemizer):
    """
    Morphemizer for languages that use spaces (English, German, Spanish, ...). Because it is
    a general-use-morphemizer, it can't generate the base form from inflection.
    """

    def getMorphemesFromExpr(self, e):
        word_list = [word.lower()
                     for word in re.findall(r"\b[^\s\d]+\b", e, re.UNICODE)]
        return [Morpheme(word, word, word, word, 'UNKNOWN', 'UNKNOWN') for word in word_list]

    def getDescription(self):
        return 'Language w/ Spaces'


####################################################################################################
# Vietnamese Morphemizer
####################################################################################################

class VietnameseMorphemizer(Morphemizer):
    """
    Vietnamese contains many compound words where the polysyllabic morphemes
    are divided by spaces, so an extra tool - pyvi - is used instead.
    """
    def exists(self):
        """
        pyvi has large dependencies. To avoid bundling it or forcing users to
        install it as a dependency, the Vietnamese morphizer only appears if
        pyvi is importable.
        """
        return (importlib.util.find_spec('pyvi') is not None)

    def getMorphemesFromExpr(self, expression):
        from pyvi import ViTokenizer
        tokens = SpaceMorphemizer.getMorphemesFromExpr(self, ViTokenizer.tokenize(expression))
        for word in tokens:
            word.base = word.base.replace('_', ' ')

        return tokens

    def getDescription(self):
        return 'Vietnamese'


####################################################################################################
# CJK Character Morphemizer
####################################################################################################

class CjkCharMorphemizer(Morphemizer):
    """
    Morphemizer that splits sentence into characters and filters for Chinese-Japanese-Korean logographic/idiographic
    characters.
    """

    def getMorphemesFromExpr(self, e):
        return [Morpheme(character, character, character, character, 'CJK_CHAR', 'UNKNOWN') for character in
                re.findall('[%s]' % characters, e)]

    def getDescription(self):
        return 'CJK Characters'


####################################################################################################
# Jieba Morphemizer (Chinese)
####################################################################################################

class JiebaMorphemizer(Morphemizer):
    """
    Jieba Chinese text segmentation: built to be the best Python Chinese word segmentation module.
    https://github.com/fxsjy/jieba
    """

    def getMorphemesFromExpr(self, e):
        # remove all punctuation
        e = u''.join(re.findall('[%s]' % characters, e))
        return [Morpheme(m.word, m.word, m.word, m.word, m.flag, u'UNKNOWN') for m in
                posseg.cut(e)]  # find morphemes using jieba's POS segmenter

    def getDescription(self):
        return 'Chinese'
