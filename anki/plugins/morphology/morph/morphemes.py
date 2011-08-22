# -*- coding: utf-8 -*-
import os, subprocess, sys, bz2, codecs, pickle, gzip

def printf( s ):
    if sys.platform == 'win32':
        import win32console as W
        W.SetConsoleOutputCP( 65001 )
        W.SetConsoleCP( 65001 )
    try: print s
    except: pass

################################################################################
## Lexical analysis
################################################################################

MECAB_NODE_PARTS = ['%f[6]','%m','%f[0]','%f[1]','%f[7]']
MECAB_NODE_READING_INDEX = 4
MECAB_NODE_LENGTH = len( MECAB_NODE_PARTS )

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
        return hash( (self.pos, self.subPos, self.read, self.base, self.inflected) )

    def show( self ): # Str
        return u'\t'.join([ self.base, self.pos, self.subPos, self.read ])

def ms2str( ms ): # [Morpheme] -> Str
    return u'\n'.join( m.show() for m in ms )

def which( app ): # PartialAppPath -> [FullAppPath]
    def isExe( path ):
        return os.path.exists( path ) and os.access( path, os.X_OK )
    apath, aname = os.path.split( app )
    if apath and isExe( app ):  # full path was provided
        return [ app ]
    else:                       # search $PATH for matches
        ps = [ os.path.join( p, aname ) for p in os.environ['PATH'].split( os.pathsep ) ]
        return [ p for p in ps if isExe( p ) ]

# Creates an instance of mecab process
def mecab( customPath=None ): # Maybe Path -> IO MecabProc
    try: from japanese.reading import si
    except: si = None

    path = customPath or 'mecab'
    if not which( 'mecab' ): # probably on windows and only has mecab via Anki
        # maybe we're running from anki?
        aPath = os.path.dirname( os.path.abspath( sys.argv[0] ) )
        amPath = os.path.join( aPath, 'mecab', 'bin', 'mecab.exe' )

        # otherwise check default anki install loc
        if not which( amPath ):
            aPath = r'C:\Program Files\Anki'
        os.environ['PATH'] += ';%s\\mecab\\bin' % aPath
        os.environ['MECABRC'] = '%s\\mecab\\etc\\mecabrc' % aPath
    nodeFmt = '\t'.join( MECAB_NODE_PARTS )+'\r'
    mecabCmd = [ path, '--node-format=%s' % nodeFmt, '--eos-format=\n', '--unk-format=%m\tUnknown\tUnknown\tUnknown\r']
    return subprocess.Popen( mecabCmd, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=si )

# Send mecab 1 input and receive 1 output
def interact( p, expr ): # MecabProc -> Str -> IO Str
    expr = expr.encode( 'euc-jp', 'ignore' )
    p.stdin.write( expr + '\n' )
    p.stdin.flush()
    return u'\r'.join( [ unicode( p.stdout.readline().rstrip( '\r\n' ), 'euc-jp' ) for l in expr.split('\n') ] )

def fixReading( p, m ): # MecabProc -> Morpheme -> Morpheme
    if m.pos in [u'動詞', u'助動詞', u'形容詞']: # verb, aux verb, i-adj
        n = interact( p, m.base ).split('\t')
        if len(n) == MECAB_NODE_LENGTH:
            m.read = n[ MECAB_NODE_READING_INDEX ].strip()
    return m

# MecabProc -> Str -> Maybe PosWhiteList -> Maybe PosBlackList -> IO [Morpheme]
def getMorphemes( p, e, ws=None, bs=None ):
    ms = [ tuple( m.split('\t') ) for m in interact( p, e ).split('\r') ] # morphemes
    ms = [ Morpheme( *m ) for m in ms if len( m ) == MECAB_NODE_LENGTH ] # filter garbage
    if ws: ms = [ m for m in ms if m.pos in ws ]
    if bs: ms = [ m for m in ms if m.pos not in bs ]
    ms = [ fixReading( p, m ) for m in ms ]
    return ms

# Str -> Maybe PosWhiteList -> Maybe PosBlackList -> IO [Morpheme]
def getMorphemes1( e, ws=None, bs=None ):
    return getMorphemes( mecab(), e, ws, bs )

################################################################################
## Morpheme db manipulation
################################################################################

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
    def __init__( self, factId, fieldName, fieldValue, deckPath, deckName, maturities ):
        self.factId     = factId
        self.fieldName  = fieldName
        self.fieldValue = fieldValue
        self.deckPath   = deckPath
        self.deckName   = deckName
        self.maturities = maturities
        self.maturity   = max( maturities ) if maturities else 0
    def show( self ):
        return '%s.%d[%s]@%d' % ( self.deckName, self.factId, self.fieldName, self.maturity )

class MorphDb:
    @staticmethod
    def mergeFiles( aPath, bPath, destPath ): # FilePath -> FilePath -> FilePath -> IO ()
        a, b = MorphDb( path=aPath ), MorphDb( path=bPath )
        a.merge( b )
        a.save( destPath )

    @staticmethod
    def mkFromFile( path ): # FilePath -> IO Db
        d = MorphDb()
        d.importFile( path )
        return d

    def __init__( self, path=None ): # Maybe Filepath -> m ()
        self.db     = {} # Map Morpheme -> {Location}
        if path:
            self.load( path )
        self.analyze()

    # Serialization
    def show( self ):
        s = u''
        for m,ls in self.db.iteritems():
            s += u'%s\n' % m.show()
            for l in ls:
                s += u'  %s\n' % l.show()
        return s

    def showLocDb( self ):
        s = u''
        for l,ms in self.locDb().iteritems():
            s += u'%s\n' % l.show()
            for m in ms:
                s += u'  %s\n' % m.show()
        return s

    def showMs( self ):
        return ms2str( self.db.keys() )

    def save( self, path ): # FilePath -> IO ()
        par = os.path.split( path )[0]
        if not os.path.exists( par ):
            os.makedirs( par )
        f = gzip.open( path, 'wb' )
        pickle.dump( self.db, f )
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

    def merge( self, md ): # Db -> m ()
        for m,locs in md.db.iteritems():
            try:
                self.db[m].update( locs )
            except KeyError:
                self.db[m] = locs

    def importFile( self, path, ws=None, bs=[u'記号'] ): # FilePath -> PosWhitelist? -> PosBlacklist? -> IO ()
        f = codecs.open( path, 'r', 'utf-8' )
        inp = f.readlines()
        f.close()
        mp = mecab()

        for i,line in enumerate(inp):
            ms = getMorphemes( mp, line.strip(), ws, bs )
            self.addMLs( ( m, TextFile( path, i+1 ) ) for m in ms )

        mp.terminate()

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
            d[ (loc.factId, loc.fieldName) ] = loc
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
