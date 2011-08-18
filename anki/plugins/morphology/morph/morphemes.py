# -*- coding: utf-8 -*-
import os, subprocess, sys, bz2, codecs, pickle, gzip

################################################################################
## Lexical analysis
################################################################################

MECAB_NODE_PARTS = ['%f[6]','%f[0]','%f[1]','%f[7]']
MECAB_NODE_READING_INDEX = 3
MECAB_NODE_LENGTH = len( MECAB_NODE_PARTS )

class Morpheme:
    def __init__( self, expr, pos, subPos, read ):
        self.pos    = pos
        self.subPos = subPos
        self.expr   = expr
        self.read   = read

    def __eq__( self, o ):
        if not isinstance( o, Morpheme ): return False
        if self.pos != o.pos: return False
        if self.subPos != o.subPos: return False
        if self.expr != o.expr: return False
        if self.read != o.read: return False
        return True

    def __hash__( self ):
        return hash( (self.pos, self.subPos, self.expr, self.read) )

    def show( self ): # Str
        return u'\t'.join([ self.expr, self.pos, self.subPos, self.read ])

def ms2str( ms ): # [Morpheme] -> Str
    return u'\n'.join( m.show() for m in ms )

# Creates an instance of mecab process
def mecab( fixPath=r'C:\Program Files\Anki\mecab' ): # :: Maybe Path -> IO MecabProc
    try: from japanese.reading import si
    except: si = None
    if fixPath:
        os.environ['PATH'] += ';%s\\bin' % fixPath
        os.environ['MECABRC'] = '%s\\etc\\mecabrc' % fixPath
    nodeFmt = '\t'.join( MECAB_NODE_PARTS )+'\r'
    mecabCmd = ['mecab', '--node-format=%s' % nodeFmt, '--eos-format=\n', '--unk-format=%m\tUnknown\tUnknown\tUnknown\r']
    return subprocess.Popen( mecabCmd, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=si )

# Send mecab 1 input and receive 1 output
def interact( p, expr ): # MecabProc -> Str -> IO Str
    expr = expr.encode( 'euc-jp', 'ignore' )
    p.stdin.write( expr + '\n' )
    p.stdin.flush()
    return u'\r'.join( [ unicode( p.stdout.readline().rstrip( '\r\n' ), 'euc-jp' ) for l in expr.split('\n') ] )

def fixReading( p, m ): # MecabProc -> Morpheme -> Morpheme
    if m.pos in [u'動詞', u'助動詞', u'形容詞']: # verb, aux verb, i-adj
        n = interact( p, m.expr ).split('\t')
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
    return getMorphemes( mecab(None), e, ws, bs )

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
    def __init__( self, factId, field, deckPath, deckName ):
        self.factId     = factId
        self.field      = field
        self.deckPath   = deckPath
        self.deckName   = deckName
    def show( self ):
        return '%s.%d[%s]' % ( self.deckName, self.factId, self.field )

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
        self.db = {} # Map Morpheme -> {Location}
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

    def showMs( self ):
        return ms2str( self.db.keys() )

    def save( self, path ): # FilePath -> IO ()
        with gzip.open( path, 'wb' ) as f:
            pickle.dump( self, f )

    def load( self, path ): # FilePath -> m ()
        with gzip.open( path, 'rb' ) as f:
            self.db = pickle.load( f ).db
    
    # Adding
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
        mp = mecab( None )

        for i,line in enumerate(inp):
            ms = getMorphemes( mp, line.strip(), ws, bs )
            self.addMLs( ( m, TextFile( path, i+1 ) ) for m in ms )

        mp.terminate()

    # Analysis
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

################################################################################
## Standalone program
################################################################################

def test():
    a = MorphDb.mkFromFile( 'tests/test.txt' )
    a.save( 'tests/test.db.testTmp' )
    d = MorphDb( path='tests/test.db.testTmp' )
    assert d.count == 81, 'wrong number of morphemes'
    print d.analyze2str()

def main(): # :: IO ()
    if '--test' in sys.argv:
        return test()
    elif len( sys.argv ) != 3:
        print 'Usage: %s srcTxtFile destDbFile' % sys.argv[0]
        return
    d = MorphDb.mkFromFile( sys.argv[1] )
    d.save( sys.argv[2] )

if __name__ == '__main__': main()
