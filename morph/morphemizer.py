# -*- coding: utf-8 -*-
import json
import re
import os
import subprocess

from .morphemes import Morpheme
from .deps.zhon.hanzi import characters
from .mecab_wrapper import getMorphemesMecab, getMecabIdentity
from .deps.jieba import posseg
from .util_external import memoize


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

@memoize
def getAllMorphemizers():
    # type: () -> [Morphemizer]

    morphemizers = [SpaceMorphemizer(), MecabMorphemizer(), JiebaMorphemizer(), CjkCharMorphemizer()]

    try:
        my_dir = os.path.dirname(__file__)
        helper_path = os.path.join(my_dir, 'deps', 'python', 'parser_helper.py')
        output = subprocess.check_output(['python', helper_path, 'parsers'])
        parsers = json.loads(output.decode('utf-8'))
        print('found parsers:', parsers)
        for parser in parsers:
            morphemizers.append(PythonMorphemizer(parser[0], parser[1]))
        
    except:
        pass

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
# Python Morphemizer
####################################################################################################

POS_BLACKLIST = [
    '記号',  # "symbol", generally punctuation
    '補助記号',  # "symbol", generally punctuation
    '空白',  # Empty space
    'SPACE',
    'PUNCT',
    'NUM'
]
SUBPOS_BLACKLIST = [
    '数詞',  # Numbers
]

class PythonMorphemizer(Morphemizer):
    """
    Uses morphemizers in the current Python installation, including: SpaCy.
    """

    def __init__(self, parser_name, description):
        self.parser_name = parser_name
        self.description = description
        self.proc = None

    @memoize
    def getMorphemesFromExpr(self, expression):
        if not self.proc:
            my_dir = os.path.dirname(__file__)
            helper_path = os.path.join(my_dir, 'deps', 'python', 'parser_helper.py')
            cmd = ['python', helper_path, 'interact', self.parser_name]
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT)

        expr = expression.encode('utf-8', 'ignore')
        #print("expr", expr)
        self.proc.stdin.write(expr + b'\n')
        self.proc.stdin.flush()
        
        res = []
        for l in expr.split(b'\n'):
            morphs = json.loads(self.proc.stdout.readline())
            res.extend([Morpheme(m[0], m[1], m[2], m[3], m[4], m[5]) \
                for m in morphs if (m[4] not in POS_BLACKLIST) and (m[5] not in SUBPOS_BLACKLIST)])
        #print("res", res)
        return res

    def getName(self):
        return self.parser_name

    def getDescription(self):
        return self.description


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
