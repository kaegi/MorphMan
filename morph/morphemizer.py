# -*- coding: utf-8 -*-
import re


from .morphemes import Morpheme
from .deps.zhon.hanzi import characters
from .mecab_wrapper import getMorphemesMecab, getMorphemesKoMecab
from .deps.jieba import posseg


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


####################################################################################################
# Morphemizer Helpers
####################################################################################################

def getAllMorphemizers():
    # type: () -> [Morphemizer]
    return [SpaceMorphemizer(), MecabMorphemizer(), JiebaMorphemizer(), CjkCharMorphemizer(),
            KoreanMorphemizer()]


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
        return 'Japanese'


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


####################################################################################################
# Korean Morphemizer
####################################################################################################

class KoreanMorphemizer(Morphemizer):
    """
    Morphemizer for Korean using the Mecab Morphemizer with Korean Dictionary.
    """

    def getMorphemesFromExpr(self, expression):
        return getMorphemesKoMecab(expression)

    def getDescription(self):
        return 'Korean'
