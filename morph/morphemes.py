# -*- coding: utf-8 -*-
import codecs, pickle as pickle, gzip, os, subprocess, re
import re
import aqt

# need some fallbacks if not running from anki and thus morph.util isn't available
try:
    from .util import errorMsg, jcfg, cfg1
except ImportError:
    def errorMsg( msg ): pass
    def jcfg(s): return None
    def cfg1(s): return None

################################################################################
## Lexical analysis
################################################################################

class Morpheme:
    def __init__( self, norm, base, inflected, read, pos, subPos ):
        """ Initialize morpheme class.

        POS means part-of-speech.

        Example morpheme infos for the expression "歩いて":

        :param str norm: 歩く [normalized base form]
        :param str base: 歩く
        :param str inflected: 歩い  [mecab cuts off all endings, so there is not て]
        :param str read: アルイ
        :param str pos: 動詞
        :param str subPos: 自立

        """
        # values are created by "mecab" in the order of the parameters and then directly passed into this constructor
        # example of mecab output:    "歩く     歩い    動詞    自立      アルイ"
        # matches to:                 "base     infl    pos     subPos    read"
        self.norm = norm if norm is not None else base
        self.base   = base
        self.inflected = inflected
        self.read   = read
        self.pos    = pos # type of morpheme detemined by mecab tool. for example: u'動詞' or u'助動詞', u'形容詞'
        self.subPos = subPos

    def __setstate__(self, d):
        """ Override default pickle __setstate__ to initialize missing defaults in old databases
        """
        self.norm = d['norm'] if 'norm' in d else d['base']
        self.base = d['base']
        self.inflected = d['inflected']
        self.read = d['read']
        self.pos = d['pos']
        self.subPos = d['subPos']

    def __eq__( self, o ):
        if not isinstance( o, Morpheme ): return False
        if self.norm != o.norm: return False
        if self.base != o.base: return False
        if self.inflected != o.inflected: return False
        if self.read != o.read: return False
        if self.pos != o.pos: return False
        if self.subPos != o.subPos: return False
        return True

    def __hash__( self ):
        return hash( ( self.norm, self.base, self.inflected, self.read, self.pos, self.subPos ) )

    def getGroupKey( self ):
        if cfg1('ignore grammar position'):
            return '%s\t%s' % (self.norm, self.read)
        else:
            return '%s\t%s\t%s\t' % (self.norm, self.read, self.pos)

    def show( self ): # str
        return '\t'.join([ self.norm, self.base, self.inflected, self.read, self.pos, self.subPos ])

def ms2str( ms ): # [(Morpheme, locs)] -> Str
    return '\n'.join( ['%d\t%s' % (len(m[1]), m[0].show()) for m in ms] )

class MorphDBUnpickler(pickle.Unpickler):
    class MorphDBUnpickler(pickle.Unpickler):
        def __init__(self, file):
            super(MorphDBUnpickler, self).__init__(file) 

    def find_class(self, cmodule, cname):
        # Override default class lookup for this module to allow loading databases generated with older
        # versions of the MorphMan add-on.
        if cmodule.endswith('.morph.morphemes'):
            return globals()[cname]
        return pickle.Unpickler.find_class(self, cmodule, cname)

def getMorphemes(morphemizer, expression, note_tags=None, ignore_positions=False):
    if jcfg('Option_IgnoreBracketContents'):
        regex = r'\[[^\]]*\]'
        if re.search(regex, expression):
            expression = re.sub(regex, '', expression)

    # go through all replacement rules and search if a rule (which dictates a string to morpheme conversion) can be applied
    replace_rules = jcfg('ReplaceRules')
    if not note_tags is None and not replace_rules is None:
        note_tags_set = set(note_tags)
        for (filter_tags, regex, morphemes) in replace_rules:
            if not set(filter_tags) <= note_tags_set: continue

            # find matches
            splitted_expression = re.split(regex, expression, maxsplit=1, flags=re.UNICODE)

            if len(splitted_expression) == 1: continue # no match
            assert(len(splitted_expression) == 2)

            # make sure this rule doesn't lead to endless recursion
            if len(splitted_expression[0]) >= len(expression): continue
            if len(splitted_expression[1]) >= len(expression): continue

            a_morphs = getMorphemes(morphemizer, splitted_expression[0], note_tags)
            b_morphs = [Morpheme(mstr, mstr, 'UNKNOWN', 'UNKNOWN', mstr) for mstr in morphemes]
            c_morphs = getMorphemes(morphemizer, splitted_expression[1], note_tags)

            return a_morphs + b_morphs + c_morphs


    ms = morphemizer.getMorphemesFromExpr(expression)

    return ms



################################################################################
## Morpheme db manipulation
################################################################################

### Locations
class Location:
    pass

class Nowhere( Location ):
    def __init__( self, tag, weight=0 ):
        self.tag = tag
        self.maturity = 0
        self.weight   = weight
    def show( self ):
        return '%s@%d' % ( self.tag, self.maturity )

class Corpus( Location ):
    '''A corpus we want to use for priority, without storing more than morpheme frequencies.'''
    def __init__( self, name, weight ):
        self.name     = name
        self.maturity = 0
        self.weight   = weight
    def show( self ):
        return '%s*%s@%d' % ( self.name, self.weight, self.maturity )

class TextFile( Location ):
    def __init__( self, filePath, lineNo, maturity, weight=1 ):
        self.filePath   = filePath
        self.lineNo     = lineNo
        self.maturity   = maturity
        self.weight     = weight
    def show( self ):
        return '%s:%d@%d' % ( self.filePath, self.lineNo, self.maturity )

class AnkiDeck( Location ):
    """ This maps to/contains information for one note and one relevant field like u'Expression'. """

    def __init__( self, noteId, fieldName, fieldValue, guid, maturities, weight=1 ):
        self.noteId     = noteId
        self.fieldName  = fieldName # for example u'Expression'
        self.fieldValue = fieldValue # for example u'それだけじゃない'
        self.guid       = guid
        self.maturities = maturities # list of intergers, one for every card -> containg the intervals of every card for this note
        self.maturity   = max( maturities ) if maturities else 0
        self.weight     = weight
    def show( self ):
        return '%d[%s]@%d' % ( self.noteId, self.fieldName, self.maturity )

kanji = r'[㐀-䶵一-鿋豈-頻]'
def extract_unicode_block(unicode_block, string):
    ''' extracts and returns all texts from a unicode block from string argument.
        Note that you must use the unicode blocks defined above, or patterns of similar form '''
    return re.findall( unicode_block, string)

def fuzzyMatchMorpheme( m, alt ):
    if m.norm != alt.norm:
        return False
    if m.base == alt.base:
        return True
    m_kanji = extract_unicode_block(kanji, m.base)
    alt_kanji = extract_unicode_block(kanji, alt.base)
    for c in m_kanji:
        if c not in alt_kanji:
            return False
    return True

### Morpheme DB
class MorphDb:
    @staticmethod
    def mergeFiles( aPath, bPath, destPath=None, ignoreErrors=False ): # FilePath -> FilePath -> Maybe FilePath -> Maybe Book -> IO MorphDb
        a, b = MorphDb( aPath, ignoreErrors ), MorphDb( bPath, ignoreErrors )
        a.merge( b )
        if destPath:
            a.save( destPath )
        return a

    @staticmethod
    def mkFromFile( path, morphemizer, maturity=0 ): # FilePath -> Maturity? -> IO Db
        '''Returns None and shows error dialog if failed'''
        d = MorphDb()
        try:    d.importFile( path, morphemizer, maturity=maturity )
        except (UnicodeDecodeError, IOError) as e:
            return errorMsg( 'Unable to import file. Please verify it is a UTF-8 text file and you have permissions.\nFull error:\n%s' % e )
        return d

    def __init__( self, path=None, ignoreErrors=False ): # Maybe Filepath -> m ()
        self.db     = {} # Map Morpheme {Location}
        self.groups = {} # Map NormMorpheme {Set(Morpheme)}
        if path:
            try: self.load( path )
            except IOError:
                if not ignoreErrors: raise
        self.analyze()

    # Serialization
    def show( self ): # Str
        s = ''
        for m,ls in self.db.items():
            s += '%s\n' % m.show()
            for l in ls:
                s += '  %s\n' % l.show()
        return s

    def showLocDb( self ): # m Str
        s = ''
        for l,ms in self.locDb().items():
            s += '%s\n' % l.show()
            for m in ms:
                s += '  %s\n' % m.show()
        return s

    def showMs( self ): # Str       
        return ms2str( sorted(self.db.items(), key=lambda it: it[0].show()) )

    def save( self, path ): # FilePath -> IO ()
        par = os.path.split( path )[0]
        if not os.path.exists( par ):
            os.makedirs( par )
        f = gzip.open( path, 'wb' )
        pickle.dump( self.db, f, -1 )
        f.close()

    def load( self, path ): # FilePath -> m ()
        f = gzip.open( path, 'rb' )
        try:
            db = MorphDBUnpickler(f).load()
            for m,locs in db.items():
                self.addMLs1(m, locs)
        except ModuleNotFoundError as e:
            msg = 'ModuleNotFoundError was thrown. That probably means that you\'re using database files generated in the older versions of MorphMan. To fix this issue, please refer to the written guide on database migration (copy-pasteable link will appear in the next window): https://gist.github.com/InfiniteRain/1d7ca9ad307c4203397a635b514f00c2'
            aqt.utils.showInfo(msg)
            raise e
        f.close()

    # Returns True if DB has variations that can match 'm'.
    def matches( self, m ): # Morpheme
        gk = m.getGroupKey()
        ms = self.groups.get(gk, None)
        if ms is None:
            return False

        # Fuzzy match to variations
        for alt in ms:
            if fuzzyMatchMorpheme(m, alt):
                return True
        
        return False

    def getMatchingLocs( self, m ): # Morpheme
        locs = set()
        gk = m.getGroupKey()
        ms = self.groups.get(gk, None)
        if ms is None:
            return locs

        # Fuzzy match to variations
        for variation in ms:
            if fuzzyMatchMorpheme(m, variation):
                locs.update(self.db[variation])
        return locs

    # Adding
    def clear( self ): # m ()
        self.db = {}
        self.groups = {}

    def addMLs( self, mls ): # [ (Morpheme,Location) ] -> m ()
        for m,loc in mls:
            if m in self.db:
                self.db[m].add( loc )
            else:
                self.db[m] = set([ loc ])
                gk = m.getGroupKey()
                if gk not in self.groups:
                    self.groups[gk] = set([m])
                else:
                    self.groups[gk].add(m)

    def addMLs1( self, m, locs ): # Morpheme -> {Location} -> m ()
        if m in self.db:
            self.db[m].update( locs )
        else:
            self.db[m] = set( locs )
            gk = m.getGroupKey()
            if gk not in self.groups:
                self.groups[gk] = set([m])
            else:
                self.groups[gk].add(m)

    def addMsL( self, ms, loc ): # [Morpheme] -> Location -> m ()
        self.addMLs( (m,loc) for m in ms )

    def addFromLocDb( self, ldb ): # Map Location {Morpheme} -> m ()
        for l,ms in ldb.items():
            self.addMLs([(m,l) for m in ms])

    # returns number of added entries
    def merge( self, md ): # Db -> m Int
        new = 0
        for m,locs in md.db.items():
            if m in self.db:
                new += len( locs - self.db[m] )
                self.db[m].update( locs )
            else:
                new += len( locs )
                self.addMLs1( m, locs )

        return new

    def importFile( self, path, morphemizer, maturity=0 ): # FilePath -> Morphemizer -> Maturity? -> IO ()
        f = codecs.open( path, 'r', 'utf-8' )
        inp = f.readlines()
        f.close()

        for i,line in enumerate(inp):
            ms = getMorphemes( morphemizer, line.strip())
            self.addMLs( ( m, TextFile( path, i+1, maturity ) ) for m in ms )

    # Analysis (local)
    def frequency( self, m ): # Morpheme -> Int
        return sum(getattr(loc, 'weight', 1) for loc in self.db[m])

    # Analysis (global)
    def locDb( self, recalc=True ): # Maybe Bool -> m Map Location {Morpheme}
        if hasattr( self, '_locDb' ) and not recalc:
            return self._locDb
        self._locDb = d = {}
        for m,ls in self.db.items():
            for l in ls:
                if l in d:
                    d[ l ].add( m )
                else:
                    d[ l ] = set([ m ])
        return d

    def fidDb( self, recalc=True ): # Maybe Bool -> m Map FactId Location
        if hasattr( self, '_fidDb' ) and not recalc:
            return self._fidDb
        self._fidDb = d = {}
        for loc in self.locDb():
            try:
                d[ ( loc.noteId, loc.guid, loc.fieldName ) ] = loc
            except AttributeError: pass # location isn't an anki fact
        return d

    def countByType( self ): # Map Pos Int
        d = {}
        for m in self.db.keys():
            d[ m.pos ] = d.get(m.pos, 0) + 1
        return d

    def analyze( self ): # m ()
        self.posBreakdown = self.countByType()
        self.kCount = len( self.groups )
        self.vCount = len( self.db )

    def analyze2str( self ): # m Str
        self.analyze()
        posStr = '\n'.join( '%d\t%d%%\t%s' % ( v, 100.*v/self.vCount, k ) for k,v in self.posBreakdown.items() )
        return 'Total normalized morphemes: %d\nTotal variations: %d\nBy part of speech:\n%s' % ( self.kCount, self.vCount, posStr )
