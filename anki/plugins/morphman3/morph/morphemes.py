# -*- coding: utf-8 -*-
import codecs, cPickle as pickle, gzip, os, subproceess
from morph.util import memoize, errorMsg

################################################################################
## Lexical analysis
################################################################################

MECAB_NODE_PARTS = ['%f[6]','%m','%f[0]','%f[1]','%f[7]']
MECAB_NODE_READING_INDEX = 4
MECAB_NODE_LENGTH = len( MECAB_NODE_PARTS )
MECAB_ENCODING = None

class Morpheme:
    def __init__( self, base, inflected, pos, subPos, read ):
        self.pos    = pos
        self.subPos = subPos
        self.read   = read
        self.base   = base
        self.inflected = inflected

    def __eq__( self, o ):
        if not isinstance( o, Morpheme ): return False
        if self.pos != o.pos: return False
        if self.subPos != o.subPos: return False
        if self.read != o.read: return False
        if self.base != o.base: return False
        #if self.inflected != o.inflected: return False
        return True

    def __hash__( self ):
        #return hash( (self.pos, self.subPos, self.read, self.base, self.inflected) )
        return hash( (self.pos, self.subPos, self.read, self.base, self.inflected) )

    def show( self ): # Str
        return u'\t'.join([ self.base, self.pos, self.subPos, self.read ])

def ms2str( ms ): # [Morpheme] -> Str
    return u'\n'.join( m.show() for m in ms )

def runMecabCmd( args ): # [Str] -> IO MecabProc
    try:
        from japanese.reading import si, MecabController
        m = MecabController()
        m.setup()
        cmd = m.mecabCmd[:1] + m.mecabCmd[4:]
    except ImportError:
        si = None
        cmd = ['mecab']
    s = subprocess.Popen( cmd + args, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=si )
    return s

def getMecabEncoding(): # IO CharacterEncoding
    return runMecabCmd( [ '-D' ] ).stdout.readlines()[2].lstrip( 'charset:' ).lstrip()

@memoize
def mecab(): # IO MecabProc
    global MECAB_ENCODING
    if not MECAB_ENCODING: MECAB_ENCODING = getMecabEncoding()
    nodeFmt = '\t'.join( MECAB_NODE_PARTS )+'\r'
    args = [ '--node-format=%s' % nodeFmt, '--eos-format=\n', '--unk-format=%m\tUnknown\tUnknown\tUnknown\r' ]
    return runMecabCmd( args )

@memoize
def interact( expr ): # Str -> IO Str
    p = mecab()
    expr = expr.encode( MECAB_ENCODING, 'ignore' )
    p.stdin.write( expr + '\n' )
    p.stdin.flush()
    return u'\r'.join( [ unicode( p.stdout.readline().rstrip( '\r\n' ), MECAB_ENCODING ) for l in expr.split('\n') ] )

@memoize
def fixReading( m ): # Morpheme -> IO Morpheme
    if m.pos in [u'動詞', u'助動詞', u'形容詞']: # verb, aux verb, i-adj
        n = interact( m.base ).split('\t')
        if len(n) == MECAB_NODE_LENGTH:
            m.read = n[ MECAB_NODE_READING_INDEX ].strip()
    return m

@memoize
def getMorphemes( e, ws=None, bs=None ): # Str -> PosWhiteList? -> PosBlackList? -> IO [Morpheme]
    ms = [ tuple( m.split('\t') ) for m in interact( e ).split('\r') ] # morphemes
    ms = [ Morpheme( *m ) for m in ms if len( m ) == MECAB_NODE_LENGTH ] # filter garbage
    if ws: ms = [ m for m in ms if m.pos in ws ]
    if bs: ms = [ m for m in ms if m.pos not in bs ]
    ms = [ fixReading( m ) for m in ms ]
    return ms

################################################################################
## Morpheme db manipulation
################################################################################

### Locations
class Location:
    pass

class Nowhere( Location ):
    def __init__( self, tag ):
        self.tag
    def show( self ):
        return '%s' % self.tag

class TextFile( Location ):
    def __init__( self, filePath, lineNo ):
        self.filePath   = filePath
        self.lineNo     = lineNo
    def show( self ):
        return '%s:%d' % ( self.filePath, self.lineNo )

class AnkiDeck( Location ):
    def __init__( self, noteId, fieldName, fieldValue, guid, maturities ):
        self.noteId     = noteId
        self.fieldName  = fieldName
        self.fieldValue = fieldValue
        self.guid       = guid
        self.maturities = maturities
        self.maturity   = max( maturities ) if maturities else 0
    def show( self ):
        return '%d[%s]@%d' % ( self.noteId, self.fieldName, self.maturity )

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
    def mkFromFile( path ): # FilePath -> IO Db
        '''Returns None and shows error dialog if failed'''
        d = MorphDb()
        try:    d.importFile( path )
        except (UnicodeDecodeError, IOError), e:
            return errorMsg( 'Unable to import file. Please verify it is a UTF-8 text file and you have permissions.\nFull error:\n%s' % e )
        return d

    def __init__( self, path=None, ignoreErrors=False ): # Maybe Filepath -> m ()
        self.db     = {} # Map Morpheme {Location}
        if path:
            try: self.load( path )
            except IOError:
                if not ignoreErrors: raise
        self.analyze()

    # Serialization
    def show( self ): # Str
        s = u''
        for m,ls in self.db.iteritems():
            s += u'%s\n' % m.show()
            for l in ls:
                s += u'  %s\n' % l.show()
        return s

    def showLocDb( self ): # m Str
        s = u''
        for l,ms in self.locDb().iteritems():
            s += u'%s\n' % l.show()
            for m in ms:
                s += u'  %s\n' % m.show()
        return s

    def showMs( self ): # Str
        return ms2str( self.db.keys() )

    def save( self, path ): # FilePath -> IO ()
        par = os.path.split( path )[0]
        if not os.path.exists( par ):
            os.makedirs( par )
        f = gzip.open( path, 'wb' )
        pickle.dump( self.db, f, -1 )
        f.close()

    def load( self, path ): # FilePath -> m ()
        f = gzip.open( path, 'rb' )
        self.db = pickle.load( f )
        f.close()

    # Adding
    def clear( self ): # m ()
        self.db = {}

    def addMLs( self, mls ): # [ (Morpheme,Location) ] -> m ()
        for m,loc in mls:
            try:
                self.db[m].add( loc )
            except KeyError:
                self.db[m] = set([ loc ])

    def addMLs1( self, m, locs ): # Morpheme -> {Location} -> m ()
        if m not in self.db:
            self.db[m] = locs
        else:
            self.db[m].update( locs )

    def addMsL( self, ms, loc ): # [Morpheme] -> Location -> m ()
        self.addMLs( (m,loc) for m in ms )

    def addFromLocDb( self, ldb ): # Map Location {Morpheme} -> m ()
        for l,ms in ldb.iteritems():
            for m in ms:
                try:
                    self.db[ m ].add( l )
                except KeyError:
                    self.db[ m ] = set([ l ])

    # returns number of added entries
    def merge( self, md ): # Db -> m Int
        new = 0
        for m,locs in md.db.iteritems():
            try:
                new += len( locs - self.db[m] )
                self.db[m].update( locs )
            except KeyError:
                self.db[m] = locs
                new += len( locs )
        return new

    def importFile( self, path, ws=None, bs=[u'記号'] ): # FilePath -> PosWhitelist? -> PosBlacklist? -> IO ()
        f = codecs.open( path, 'r', 'utf-8' )
        inp = f.readlines()
        f.close()

        for i,line in enumerate(inp):
            ms = getMorphemes( line.strip(), ws, bs )
            self.addMLs( ( m, TextFile( path, i+1 ) ) for m in ms )

    # Analysis
    def locDb( self, recalc=True ): # Maybe Bool -> m Map Location {Morpheme}
        if hasattr( self, '_locDb' ) and not recalc:
            return self._locDb
        self._locDb = d = {}
        for m,ls in self.db.iteritems():
            for l in ls:
                try: d[ l ].add( m )
                except: d[ l ] = set([ m ])
        return d

    def fidDb( self, recalc=True ): # Maybe Bool -> m Map FactId Location
        if hasattr( self, '_fidDb' ) and not recalc:
            return self._fidDb
        self._fidDb = d = {}
        for loc in self.locDb():
            d[ ( loc.noteId, loc.guid, loc.fieldName ) ] = loc
        return d

    def popDb( self ): # Map BaseForm Int
        d = {}
        for m,ls in self.db.iteritems():
            d[ m.base ] = len( ls ) + d.get( m.base, 0 )
        return d

    def countByType( self ): # Map Pos Int
        d = {}
        for m in self.db:
            try: d[ m.pos ] += 1
            except KeyError: d[ m.pos ] = 1
        return d

    def analyze( self ): # m ()
        self.posBreakdown = self.countByType()
        self.count = len( self.db )

    def analyze2str( self ): # m Str
        self.analyze()
        posStr = u'\n'.join( '%d\t%d%%\t%s' % ( v, 100.*v/self.count, k ) for k,v in self.posBreakdown.iteritems() )
        return 'Total morphemes: %d\nBy part of spech:\n%s' % ( self.count, posStr )
