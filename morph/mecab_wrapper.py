# -*- coding: utf-8 -*-
import importlib
import importlib.util
import re
import subprocess
import sys

from .morphemes import Morpheme
from .util_external import memoize

####################################################################################################
# Mecab Morphemizer
####################################################################################################


MECAB_NODE_UNIDIC_BOS = 'BOS/EOS,*,*,*,*,*,*,*,*,*,*,*,*,*'
MECAB_NODE_UNIDIC_PARTS = ['%f[7]', '%f[12]', '%m', '%f[6]', '%f[0]', '%f[1]']
MECAB_NODE_LENGTH_UNIDIC = len(MECAB_NODE_UNIDIC_PARTS)
MECAB_NODE_IPADIC_BOS = 'BOS/EOS,*,*,*,*,*,*,*,*'
MECAB_NODE_IPADIC_PARTS = ['%f[6]', '%m', '%f[7]', '%f[0]', '%f[1]']
MECAB_NODE_LENGTH_IPADIC = len(MECAB_NODE_IPADIC_PARTS)
MECAB_NODE_READING_INDEX = 2

MECAB_ENCODING = None
MECAB_POS_BLACKLIST = [
    '記号',  # "symbol", generally punctuation
    '補助記号',  # "symbol", generally punctuation
    '空白',  # Empty space
]
MECAB_SUBPOS_BLACKLIST = [
    '数詞',  # Numbers
]

is_unidic = True

kanji = r'[㐀-䶵一-鿋豈-頻]'


def extract_unicode_block(unicode_block, string):
    """ extracts and returns all texts from a unicode block from string argument.
        Note that you must use the unicode blocks defined above, or patterns of similar form """
    return re.findall(unicode_block, string)


def getMorpheme(parts):
    global is_unidic

    if is_unidic:
        if len(parts) != MECAB_NODE_LENGTH_UNIDIC:
            return None

        pos = parts[4] if parts[4] != '' else '*'
        subPos = parts[5] if parts[5] != '' else '*'

        if (pos in MECAB_POS_BLACKLIST) or (subPos in MECAB_SUBPOS_BLACKLIST):
            return None

        norm = parts[0]
        base = parts[1]
        inflected = parts[2]
        reading = parts[3]

        return Morpheme(norm, base, inflected, reading, pos, subPos)
    else:
        if len(parts) != MECAB_NODE_LENGTH_IPADIC:
            return None

        pos = parts[3] if parts[3] != '' else '*'
        subPos = parts[4] if parts[4] != '' else '*'

        if (pos in MECAB_POS_BLACKLIST) or (subPos in MECAB_SUBPOS_BLACKLIST):
            return None

        norm = parts[0]
        base = parts[0]
        inflected = parts[1]
        reading = parts[2]

        m = fixReading(Morpheme(norm, base, inflected, reading, pos, subPos))
        return m


@memoize
def getMorphemesMecab(e):
    ms = [getMorpheme(m.split('\t')) for m in interact(e).split('\r')]
    ms = [m for m in ms if m is not None]
    return ms


# [Str] -> subprocess.STARTUPINFO -> IO MecabProc
def spawnMecab(base_cmd, startupinfo):
    """Try to start a MeCab subprocess in the given way, or fail.

    Raises OSError if the given base_cmd and startupinfo don't work
    for starting up MeCab, or the MeCab they produce has a dictionary
    incompatible with our assumptions.
    """
    global MECAB_ENCODING
    global is_unidic

    # [Str] -> subprocess.STARTUPINFO -> IO subprocess.Popen
    def spawnCmd(cmd, startupinfo):
        return subprocess.Popen(cmd, startupinfo=startupinfo, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)

    config_dump = spawnCmd(base_cmd + ['-P'], startupinfo).stdout.read()
    bos_feature_match = re.search(
        '^bos-feature: (.*)$', str(config_dump, 'utf-8'), flags=re.M)

    if bos_feature_match is not None and bos_feature_match.group(1).strip() == MECAB_NODE_UNIDIC_BOS:
        node_parts = MECAB_NODE_UNIDIC_PARTS
        is_unidic = True
    elif bos_feature_match is not None and bos_feature_match.group(1).strip() == MECAB_NODE_IPADIC_BOS:
        node_parts = MECAB_NODE_IPADIC_PARTS
        is_unidic = False
    else:
        raise OSError(
            "Unexpected MeCab dictionary format; unidic or ipadic required.\n"
            "Try installing the 'Mecab Unidic' or 'Japanese Support' addons,\n"
            "or if using your system's `mecab` try installing a package\n"
            "like `mecab-ipadic`\n")

    dicinfo_dump = spawnCmd(base_cmd + ['-D'], startupinfo).stdout.read()
    charset_match = re.search(
        '^charset:\t(.*)$', str(dicinfo_dump, 'utf-8'), flags=re.M)
    if charset_match is None:
        raise OSError('Can\'t find charset in MeCab dictionary info (`$MECAB -D`):\n\n'
                      + dicinfo_dump)
    MECAB_ENCODING = charset_match.group(1)

    args = ['--node-format=%s\r' % ('\t'.join(node_parts),),
            '--eos-format=\n',
            '--unk-format=']
    return spawnCmd(base_cmd + args, startupinfo)


@memoize
def mecab():  # IO MecabProc
    """Start a MeCab subprocess and return it.
    `mecab` reads expressions from stdin at runtime, so only one
    instance is needed.  That's why this function is memoized.
    """

    if sys.platform.startswith('win'):
        si = subprocess.STARTUPINFO()
        try:
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        except:
            # pylint: disable=no-member
            si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
    else:
        si = None

    # Search for mecab
    reading = None

    # 1st priority - MecabUnidic
    if importlib.util.find_spec('13462835'):
        try:
            reading = importlib.import_module('13462835.reading')
            mecab_source = 'MecabUnidic'
        except ModuleNotFoundError:
            pass

    # 2nd priority - Japanese Support
    if (not reading) and importlib.util.find_spec('3918629684'):
        try:
            reading = importlib.import_module('3918629684.reading')
            mecab_source = 'Japanese Support'
        except ModuleNotFoundError:
            pass

    # 3nd priority - MIAJapaneseSupport
    if (not reading) and importlib.util.find_spec('MIAJapaneseSupport'):
        try:
            reading = importlib.import_module('MIAJapaneseSupport.reading')
            mecab_source = 'MIAJapaneseSupport'
        except ModuleNotFoundError:
            pass
    # 4nd priority - MIAJapaneseSupport via Anki code (278530045)
    if (not reading) and importlib.util.find_spec('278530045'):
        try:
            reading = importlib.import_module('278530045.reading')
            mecab_source = '278530045'
        except ModuleNotFoundError:
            pass

    # 5th priority - From Morphman
    if (not reading) and importlib.util.find_spec('morph') and importlib.util.find_spec('morph.deps.mecab.reading'):
        try:
            reading = importlib.import_module('morph.deps.mecab.reading')
            mecab_source = 'MorphMan'
        except ModuleNotFoundError:
            pass

    # 6th priority - system mecab
    if not reading:
        try:
            return spawnMecab(['mecab'], si), 'System'
        except:
            raise OSError('''
            Mecab Japanese analyzer could not be found.
            Please install one of the following Anki add-ons:
                 https://ankiweb.net/shared/info/3918629684
                 https://ankiweb.net/shared/info/13462835
                 https://ankiweb.net/shared/info/278530045''')

    m = reading.MecabController()
    m.setup()
    # m.mecabCmd[1:4] are assumed to be the format arguments.

    return spawnMecab(m.mecabCmd[:1] + m.mecabCmd[4:], si), mecab_source


@memoize
def interact(expr):  # Str -> IO Str
    """ "interacts" with 'mecab' command: writes expression to stdin of 'mecab' process and gets all the morpheme
    info from its stdout. """
    p, _ = mecab()
    expr = expr.encode(MECAB_ENCODING, 'ignore')
    p.stdin.write(expr + b'\n')
    p.stdin.flush()

    return '\r'.join([str(p.stdout.readline().rstrip(b'\r\n'), MECAB_ENCODING) for l in expr.split(b'\n')])


@memoize
def fixReading(m):  # Morpheme -> IO Morpheme
    """
    'mecab' prints the reading of the kanji in inflected forms (and strangely in katakana). So 歩い[て] will have アルイ as
    reading. This function sets the reading to the reading of the base form (in the example it will be 'アルク').
    """
    if m.pos in ['動詞', '助動詞', '形容詞']:  # verb, aux verb, i-adj
        n = interact(m.base).split('\t')
        if len(n) == MECAB_NODE_LENGTH_IPADIC:
            m.read = n[MECAB_NODE_READING_INDEX].strip()
    return m


#########################################################
#               Korean Mecab Processing                 #
#########################################################

"""
This can be done a lot better. Making direct changes to the functions above
would remove any unnecessary functions I have replicated below. Not as clean
and short as could be.
"""

POS_TAG_VERBS = ["VV", "VA", "VX"]
TAG_TYPES = ["Inflect", "Compound"]


@memoize
def getMorphemesKoMecab(expression):
    """
    Gets morphemes from Mecab program using Korean dictionary

    :param expression: Phrase/Sentence from Anki card
    :return: List of Morphemes (class)
    """
    mecab_r = interactKo(expression)
    # print(mecab_r)
    morphemes = []
    for m in mecab_r[:len(mecab_r)]:
        morphemes.append(getMorphemeKo(m))
    return morphemes


def getMorphemeKo(m):
    """
    Formats the mecab output into Morphman understandable Morpheme

    :param m: Morpheme string from mecab output after interactKo function
    :return: a single instance of Morpheme class
    """
    morpheme_parts = parse(m)
    # print(morpheme_parts)
    if morpheme_parts[5] in TAG_TYPES:
        if morpheme_parts[5] == TAG_TYPES[0]:
            index_split = morpheme_parts[8].split("/")
            morpheme_parts[0] = index_split[0]
            morpheme_parts[1] = index_split[1]
            morpheme_parts[8] = "*"
            morpheme_parts[5] = "*"
        else:
            morpheme_parts[8] = "*"
            morpheme_parts[5] = "*"

    if morpheme_parts[1] in POS_TAG_VERBS:
        morpheme_parts[0] = morpheme_parts[0] + "다"

    morpheme = Morpheme(morpheme_parts[0], morpheme_parts[0], morpheme_parts[4], morpheme_parts[0], morpheme_parts[1],
                        morpheme_parts[7])
    return morpheme


@memoize
def interactKo(expr):  # Str -> IO Str
    """ "interacts" with 'mecab' command: writes expression to stdin of 'mecab' process and gets all the morpheme
    info from its stdout.

    :param expr: Phrase or sentence to input into Mecab
    :return: List of morphemes
    """
    p = mecabKo()
    expr = expr.encode('utf-8', 'ignore')
    p.stdin.write(expr + b'\n')
    p.stdin.flush()
    morphs = []
    idx = 0
    while p.stdout.readable():
        morphs.append(p.stdout.readline().rstrip(b'\r\n').decode('utf-8').replace("'", "*").replace("\"", "*"))
        if morphs[idx] == "EOS":
            break
        if len(morphs[idx].replace('\t', ',').split(',')) >= 2 and (morphs[idx].replace('\t', ',').split(',')[1].__contains__("EP") or morphs[idx].replace('\t', ',').split(',')[1].__contains__("EC") or morphs[idx].replace('\t', ',').split(',')[1].__contains__("EF")):
            if morphs[idx].replace('\t', ',').split(',')[5] != "Inflect":
                add = morphs[idx - 1].replace('\t', ',').split(',')
                add[4] = add[4] + morphs[idx].replace('\t', ',').split(',')[0]
                morphs[idx - 1] = '\t'.join(add)
                morphs.remove(morphs[idx])
                idx = idx - 1
        else:
            if len(morphs[idx].replace('\t', ',').split(',')) >= 2 and (morphs[idx].replace('\t', ',').split(',')[1] == "SY" or morphs[idx].replace('\t', ',').split(',')[1] == "SF"):
                morphs.remove(morphs[idx])
                idx = idx - 1
        idx = idx + 1
    return morphs[:len(morphs) - 1]


@memoize
def mecabKo():  # IO MecabProc
    """Start a MeCab subprocess and return it.
    `mecab` reads expressions from stdin at runtime, so only one
    instance is needed.  That's why this function is memoized.
    """
    if sys.platform.startswith('win'):
        si = subprocess.STARTUPINFO()
        try:
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        except:
            # pylint: disable=no-member
            si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
    else:
        si = None

    # Search for mecab
    # reading = None

    from .deps.mecab import reading
    m = reading.MecabController()
    m.setup()
    return spawnCmdKo(m.mecabKoCmd[:1] + m.mecabKoCmd[1:], si)


def parse(expression):
    """
    Parses the mecab output into something easier to format.

    :param expression: mecab output
    :return: list of strings of unformatted mecab output.
    Each string being a morpheme with its tags.
    """
    tags = []
    for tag in expression.replace('\t', ",").split(','):
        if tag.endswith("'"):
            break
        tags.append(tag)
    return tags


def spawnCmdKo(cmd, startupinfo):
    """
    Creates a new instance of mecab as a subprocess.

    :param cmd: ["/dir/to/mecab", "-d", "dir/to/korean/dic"]
    :return: returns an open mecab subprocess.
    """
    return subprocess.Popen(cmd, startupinfo=startupinfo, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
