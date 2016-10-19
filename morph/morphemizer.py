# -*- coding: utf-8 -*-
import codecs, cPickle as pickle, gzip, os, subprocess, re
from util import cfg1, getFilterByTagsAndType
from morphemes import Morpheme

# need some fallbacks if not running from anki and thus morph.util isn't available
try:
    from morph.util import memoize, errorMsg
except ImportError:
    from util_external import memoize
    def errorMsg( msg ): pass

####################################################################################################
# Base Class
####################################################################################################

class Morphemizer:
    def getMorphemesFromExpr(self, expression): # Str -> [Morpeme]
        '''
        The heart of this plugin: convert an expression to a list of its morphemes.
        '''
        return []

    def getDescription(self):
        '''
        Returns a signle line, for which languages this Morphemizer is.
        '''
        return 'No information availiable'

####################################################################################################
# Morphemizer Helpers
####################################################################################################

def getAllMorphemizers(): # -> [Morphemizer]
    return [SpaceMorphemizer(), MecabMorphemizer(), CjkCharMorphemizer()]

def getMorphemizerForNote(note):
    ''' :type note: anki.notes.Note '''
    return getMorphemizerForTagsAndType(note.model()['name'], note.stringTags().split())

def getMorphemizerForTagsAndType(type, tags): # Str -> [Str] -> Morphemizer
    filter = getFilterByTagsAndType(type, tags)
    if filter is None: return None
    return getMorphemizerForFilter(filter)

def getMorphemizerForFilter(filter):
    return getMorphemizerByName(filter['Morphemizer'])

def getMorphemizerByName(name):
    for m in getAllMorphemizers():
        if m.__class__.__name__ == name:
            return m
    return None

####################################################################################################
# Mecab Morphemizer
####################################################################################################

class MecabMorphemizer(Morphemizer):
    '''
    Because in japanese there are no spaces to differentiate between morphemes,
    a extra tool called 'mecab' has to be used.
    '''
    def getMorphemesFromExpr(self, e): # Str -> IO [Morpheme]
        return getMorphemesMecab(e)

    def getDescription(self):
        return 'Japanese'

MECAB_NODE_PARTS = ['%f[6]','%m','%f[0]','%f[1]','%f[7]']
MECAB_NODE_READING_INDEX = 4
MECAB_NODE_LENGTH = len( MECAB_NODE_PARTS )
MECAB_ENCODING = None

@memoize
def getMorphemesMecab(e):
    ms = [ tuple( m.split('\t') ) for m in interact( e ).split('\r') ] # morphemes
    ms = [ Morpheme( *m ) for m in ms if len( m ) == MECAB_NODE_LENGTH ] # filter garbage
    #if whitelist: ms = [ m for m in ms if m.pos in whitelist ]
    blacklist = cfg1('mecab_blacklist')
    if blacklist: ms = [ m for m in ms if m.pos not in blacklist ]
    ms = [ fixReading( m ) for m in ms ]
    return ms

def runMecabCmd( args ): # [Str] -> IO MecabProc
    try:
        from japanese.reading import si, MecabController
        m = MecabController()
        m.setup()
        cmd = m.mecabCmd[:1] + m.mecabCmd[4:]
        s = subprocess.Popen( cmd + args, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=si )
    except (ImportError, OSError):
        # this handles two cases:
        #   - the japanese plugin is not installed -> try running the command directly as last instance (the user *might* have it installed)
        #   - we are not using windows, so the japanese plugin binaries won't work -> for example the Arch User Repositories (AUR) have
        #     a "mecab"-package available, which can be installed
        si = None
        cmd = ['mecab']
        s = subprocess.Popen( cmd + args, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=si )

    return s

def getMecabEncoding(): # IO CharacterEncoding
    return runMecabCmd( [ '-D' ] ).stdout.readlines()[2].lstrip( 'charset:' ).lstrip()

@memoize
def mecab(): # IO MecabProc
    ''' Returns a running mecab instance. 'mecab' reads expressions from stdin at runtime, so only one instance is needed. Thats why this function is memoized. '''
    global MECAB_ENCODING
    if not MECAB_ENCODING: MECAB_ENCODING = getMecabEncoding()
    nodeFmt = '\t'.join( MECAB_NODE_PARTS )+'\r'
    args = [ '--node-format=%s' % nodeFmt, '--eos-format=\n', '--unk-format=%m\tUnknown\tUnknown\tUnknown\r' ]
    return runMecabCmd( args )

@memoize
def interact( expr ): # Str -> IO Str
    ''' "interacts" with 'mecab' command: writes expression to stdin of 'mecab' process and gets all the morpheme infos from its stdout. '''
    p = mecab()
    expr = expr.encode( MECAB_ENCODING, 'ignore' )
    p.stdin.write( expr + '\n' )
    p.stdin.flush()
    return u'\r'.join( [ unicode( p.stdout.readline().rstrip( '\r\n' ), MECAB_ENCODING ) for l in expr.split('\n') ] )

@memoize
def fixReading( m ): # Morpheme -> IO Morpheme
    '''
    'mecab' prints the reading of the kanji in inflected forms (and strangely in katakana). So 歩い[て] will
    have アルイ as reading. This function sets the reading to the reading of the base form (in the example it will be 'アルク').
    '''
    if m.pos in [u'動詞', u'助動詞', u'形容詞']: # verb, aux verb, i-adj
        n = interact( m.base ).split('\t')
        if len(n) == MECAB_NODE_LENGTH:
            m.read = n[ MECAB_NODE_READING_INDEX ].strip()
    return m




####################################################################################################
# Space Morphemizer
####################################################################################################

class SpaceMorphemizer(Morphemizer):
    '''
    Morphemizer for languages that use spaces (English, German, Spanish, ...). Because it is
    a general-use-morphemizer, it can't generate the base form from inflection.
    '''
    def getMorphemesFromExpr(self, e): # Str -> [Morpheme]
        wordList = re.sub("[^\w-]", " ",  e).split()
        return [Morpheme(word, word, 'UNKNOWN', 'UNKNOWN', word) for word in wordList]

    def getDescription(self):
        return 'Languages with spaces (English, German, Spansh, ...)'

####################################################################################################
# CJK Character Morphemizer
####################################################################################################

class CjkCharMorphemizer(Morphemizer):
    '''
    Morphemizer that splits sentence into characters and filters for Chinese-Japanese-Korean logographic/idiographic characters.
    '''
    def getMorphemesFromExpr(self, e): # Str -> [Morpheme]
        from deps.zhon.hanzi import characters
        return [Morpheme(character, character, 'UNKNOWN', 'UNKNOWN', character) for character in re.findall('[%s]' % characters, e)]

    def getDescription(self):
        return 'CJK characters'
