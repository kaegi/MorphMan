# -*- coding: utf-8 -*-
import re
import unicodedata
from functools import lru_cache

from .morphemes import Morpheme
from .deps.zhon.hanzi import characters
from .mecab_wrapper import getMorphemesMecab, getMecabIdentity
from .deps.jieba import posseg

####################################################################################################
# Base Class
####################################################################################################

class Morphemizer:
    def __init__(self):
        pass
    
    @lru_cache(maxsize=131072)
    def getMorphemesFromExpr(self, expression):
        # type: (str) -> [Morpheme]
        
        morphs = self._getMorphemesFromExpr(expression)
        return morphs
    
    def _getMorphemesFromExpr(self, expression):
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

morphemizers = None
morphemizers_by_name = {}

def getAllMorphemizers():
    # type: () -> [Morphemizer]
    global morphemizers
    if morphemizers is None:
        morphemizers = [SpaceMorphemizer(), MecabMorphemizer(), JiebaMorphemizer(), CjkCharMorphemizer(), DeaccentMorphemizer()]

        for m in morphemizers:
            morphemizers_by_name[m.getName()] = m

    return morphemizers

def getMorphemizerByName(name):
    # type: (str) -> Optional(Morphemizer)
    getAllMorphemizers()
    return morphemizers_by_name.get(name, None)


####################################################################################################
# Mecab Morphemizer
####################################################################################################

space_char_regex = re.compile(' ')

class MecabMorphemizer(Morphemizer):
    """
    Because in japanese there are no spaces to differentiate between morphemes,
    a extra tool called 'mecab' has to be used.
    """

    def _getMorphemesFromExpr(self, expression):
        # Remove simple spaces that could be added by other add-ons and break the parsing.
        if space_char_regex.search(expression):
            expression = space_char_regex.sub('', expression)

        return getMorphemesMecab(expression)

    def getDescription(self):
        try:
            identity = getMecabIdentity()
        except:
            identity = 'UNAVAILABLE'
        return 'Japanese ' + identity


####################################################################################################
# Space Morphemizer
####################################################################################################

class SpaceMorphemizer(Morphemizer):
    """
    Morphemizer for languages that use spaces (English, German, Spanish, ...). Because it is
    a general-use-morphemizer, it can't generate the base form from inflection.
    """

    def _getMorphemesFromExpr(self, expression):
        word_list = [word.lower()
                     for word in re.findall(r"\b[^\s\d]+\b", expression, re.UNICODE)]
        return [Morpheme(word, word, word, word, 'UNKNOWN', 'UNKNOWN') for word in word_list]

    def getDescription(self):
        return 'Language w/ Spaces'



####################################################################################################
# Morphemizer that removes accents. This can be useful especially for learning russian language. 
# Some of the learning material might use words with accent marks (малако́) for emphasis when usually they 
# are omitted in literature and subtitles (молоко). 
# When using the default SpaceMorphemizer these two words would be regarded as different words so you might
# end up wasting a lot of time.
# With DeaccentMorphimizer all accents are removed, avoiding this annoyance. 
#
# WARNING! There are some words which DO have identical writing but different emphasis (for example
# замо́к = lock and за́мок = castle) but this is a bit rare situtation. If all of your cards have accent
# markings, it's better to use SpaceMorphemizer so you will be forced to learn both meanings for these words:)
####################################################################################################

ACCENT_MAPPING = {
    'а́': 'а',
    'е́': 'е',
    'и́': 'и',
    'о́': 'о',
    'у́': 'у',
    'ы́': 'ы',
    'э́': 'э',
    'ю́': 'ю',
    'я́': 'я',
}
ACCENT_MAPPING = {unicodedata.normalize('NFKC', i): j for i, j in ACCENT_MAPPING.items()}

def deaccentify(s):
    source = unicodedata.normalize('NFKC', s)
    for old, new in ACCENT_MAPPING.items():
        source = source.replace(old, new)
    return source

class DeaccentMorphemizer(Morphemizer):

    def _getMorphemesFromExpr(self, expression):
        word_list = [deaccentify(word.lower())
                     for word in re.findall(r"\b[^\s\d]+\b", expression, re.UNICODE)]
        return [Morpheme(word, word, word, word, 'UNKNOWN', 'UNKNOWN') for word in word_list]

    def getDescription(self):
        return 'Deaccented words w/ spaces'


####################################################################################################
# CJK Character Morphemizer
####################################################################################################

class CjkCharMorphemizer(Morphemizer):
    """
    Morphemizer that splits sentence into characters and filters for Chinese-Japanese-Korean logographic/idiographic
    characters.
    """

    def _getMorphemesFromExpr(self, expression):
        return [Morpheme(character, character, character, character, 'CJK_CHAR', 'UNKNOWN') for character in
                re.findall('[%s]' % characters, expression)]

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

    def _getMorphemesFromExpr(self, expression):
        # remove all punctuation
        expression = ''.join(re.findall('[%s]' % characters, expression))
        return [Morpheme(m.word, m.word, m.word, m.word, m.flag, 'UNKNOWN') for m in
                posseg.cut(expression)]  # find morphemes using jieba's POS segmenter

    def getDescription(self):
        return 'Chinese'
