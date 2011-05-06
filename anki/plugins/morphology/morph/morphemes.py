# -*- coding: utf-8 -*-
import os, subprocess, sys, bz2

#TODO: update db format to know about sources

################################################################################
## Lexical analysis
################################################################################

# Creates an instance of mecab process
def mecab( fixPath=r'C:\Program Files\Anki\mecab' ): # :: Maybe Path -> IO MecabProc
    if fixPath:
        os.environ['PATH'] += ';%s\\bin' % fixPath
        os.environ['MECABRC'] = '%s\\etc\\mecabrc' % fixPath
    mecabCmd = ['mecab', '--node-format=%m\t%f[0]\t%f[1]\t%f[8]\r', '--eos-format=\n', '--unk-format=%m\tUnknown\tUnknown\tUnknown\r']
    return subprocess.Popen( mecabCmd, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

# Used to escape all strings interacting with mecab (useful for hooking)
def escape( s ): return s # Str -> Str

# Send mecab 1 input and receive 1 output
def interact( p, expr ): # MecabProc -> Str -> IO Str
    expr = escape( expr ).encode( 'euc-jp', 'ignore' )
    p.stdin.write( expr + '\n' )
    p.stdin.flush()
    return u'\r'.join( [ unicode( p.stdout.readline().rstrip( '\r\n' ), 'euc-jp' ) for l in expr.split('\n') ] )

# MecabProc -> Str -> Maybe PosWhiteList -> Maybe PosBlackList -> IO [Morpheme]
def getMorphemes( p, e, ws=None, bs=None ):
    ms = [ tuple( m.split('\t') ) for m in interact( p, e ).split('\r') ] # morphemes
    if ws: ms = [ m for m in ms if m[1] in ws ]
    if bs: ms = [ m for m in ms if not m[1] in bs ]
    return ms

# Str -> Maybe PosWhiteList -> Maybe PosBlackList -> IO [Morpheme]
def getMorphemes1( e, ws=None, bs=None ): return getMorphemes( mecab(), e, ws, bs )

################################################################################
## Morpheme db manipulation
################################################################################

def ms2db( ms, srcName='unknown' ): # :: [Morpheme] -> Maybe SrcName -> Map Morpheme Int
    d = {}
    for m in ms:
        if m in d: d[m] += 1
        else: d[m] = 1
    return d

def saveDbC( db, path ): open( path, 'wb' ).write( bz2.compress( db2str( db ) ) ) # :: Map Morpheme Int -> Path -> IO ()
def loadDbC( path ):
    buf = bz2.decompress( open( path, 'rb' ).read() ).decode('utf-8')
    return dict([ ((a,b,c,d),int(i)) for (a,b,c,d,i) in [ row.split('\t') for row in buf.split('\n') ]])

# uncompressed/human readable versions
def saveDbU( db, path ): open( path, 'wb' ).write( db2str( db ) ) # :: Map Morpheme Int -> Path -> IO ()
def loadDbU( path ): # :: Path -> IO Map Morpheme Int
    buf = open( path, 'rb' ).read().decode('utf-8')
    return dict([ ((a,b,c,d),int(i)) for (a,b,c,d,i) in [ row.split('\t') for row in buf.split('\n') ]])

loadDb = loadDbU
saveDb = saveDbU

# :: [Morpheme] -> Str
def ms2str( ms ): return u'\n'.join( [ u'\t'.join(m) for m in ms ] ).encode('utf-8')
# :: Map Morpheme Int -> Str
def db2str( db ): return u'\n'.join( [ u'\t'.join(m) + u'\t%d' % i for (m, i) in db.iteritems() ] ).encode('utf-8')

def diffDb( da, db ):
    def f( xs, bs=[u'記号',u'助詞'] ): return [ x for x in xs if not x[1] in bs ]

    sa, sb = set( f(da.keys()) ), set( f(db.keys()) )
    i = sa.intersection( sb )
    AmB = sa.difference( sb )
    BmA = sb.difference( sa )
    sd = sa.symmetric_difference( sb )
    return (sa,sb,i,AmB,BmA,sd)

def countByType( ms ):
    d = {}
    for m in ms:
        try: d[ m[1] ] += 1
        except KeyError: d[ m[1] ] = 1
    return d


def file2ms( path, ws=None, bs=[u'記号'] ): # bs filters punctuation
    inp = unicode( open( path, 'r' ).read(), 'utf-8' )
    return getMorphemes1( inp, ws, bs)

def file2db( path, ws=None, bs=[u'記号'] ): # bs filters punctuation
    ms = file2ms( path, ws, bs )
    return ms2db( ms )

def mergeDbs( a, b ): # :: Map Morpheme Int -> Map Morpheme Int -> Map Morpheme Int
   D = {}
   for (m,i) in a.iteritems():
      try: D[m] += i
      except KeyError: D[m] = 1
   for (m,i) in b.iteritems():
      try: D[m] += i
      except KeyError: D[m] = 1
   return D

def mergeFiles( aPath, bPath, destPath ):
   a, b = loadDb( aPath ), loadDb( bPath )
   c = mergeDbs( a, b )
   saveDb( c, destPath )

################################################################################
## Standalone program
################################################################################

def test():
    def f( xs ):
        N = len(xs)
        return u'\n'.join( [ '%s: %d/%d = %d%%' % (t,n,N,100*n/N) for t,n in countByType( xs ).items() ] ).encode('utf-8')
    k = loadDb('known.morphdb')
    fsn = loadDb('fsnE01.morphdb')
    sa,sb,i,AmB,BmA,sd = diffDb( k, fsn )
    open('inter.txt','wb').write( ms2str(list( i ) ) + f(i) )
    open('B-A.txt','wb').write( ms2str(list( BmA ) ) + f(BmA) )

def test2():
   k = loadDb('dbs/known.db')
   ks = loadDb('dbs/koreSentences.db')
   kw = loadDb('dbs/koreWords.db')
   kall = mergeDbs( ks, kw )
   sa,sb,i,AmB,BmA,sd = diffDb( k, kall )
   print '# missing from either:', len(sd)
   print 'Same morphemes?', set(k.keys()) == set(kall.keys())
   print 'Same # occurances?', sum(k.values()) == sum(kall.values())
   saveDb( kall, 'dbs/koreAll.db' )

def main(): # :: IO ()
    if len( sys.argv ) != 3:
        print 'Usage: %s srcFile destFile' % sys.argv[0]
        return
    ms = file2ms( sys.argv[1] )
    open( sys.argv[2]+'.morphemes', 'w' ).write( ms2str( ms ) ) # save .morphemes
    saveDb( ms2db( ms ), sys.argv[2]+'.db' ) # save .db

if __name__ == '__main__': main()
