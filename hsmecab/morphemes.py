# -*- coding: utf-8 -*-
import os, subprocess, sys, bz2

################################################################################
## Lexical analysis
################################################################################

def mecab( fixPath=r'C:\Program Files\Anki\mecab' ): # :: Maybe Path -> IO MecabProc
    if fixPath:
        os.environ['PATH'] += ';%s\\bin' % fixPath
        os.environ['MECABRC'] = '%s\\etc\\mecabrc' % fixPath
    mecabCmd = ['mecab', '--node-format=%m\t%f[0]\t%f[1]\t%f[8]\r', '--eos-format=\n', '--unk-format=%m\tUnknown\tUnknown\tUnknown\r']
    return subprocess.Popen( mecabCmd, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

def escape( s ): return s # Str -> Str

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

def ms2db( ms ): # :: [Morpheme] -> Map Morpheme Int
    d = {}
    for m in ms:
        if m in d: d[m] += 1
        else: d[m] = 0
    return d

def saveDb( db, path ): open( path, 'wb' ).write( bz2.compress( unicode( db ) ) ) # :: Map Morpheme Int -> Path -> IO ()
def loadDb( path ): return eval( bz2.decompress( open( path, 'rb' ).read() ) ) # :: Path -> IO Map Morpheme Int

# uncompressed versions
def loadDb1( path ): return eval( open( path, 'rb' ).read() ) # :: Path -> IO Map Morpheme Int
def saveDb1( db, path ): open( path, 'wb' ).write( unicode( db ) ) # :: Map Morpheme Int -> Path -> IO ()

# :: [Morpheme] -> Str
def ms2str( ms ): return u'\n'.join( [ u'\t'.join(m) for m in ms ] ).encode('utf-8')

def diffDb( da, db ):
    sa, sb = set( da.keys() ), set( db.keys() )
    i = len( sa.intersection( sb ) )
    d1 = len( sa.difference( sb ) )
    d2 = len( sb.difference( sa ) )
    s = len( sa.symmetric_difference( sb ) )
    return (sa,sb,i,d1,d2,s)

kd = loadDb( r'm:\src\kore.morphdb' )
sd = loadDb( r'm:\src\subs2srs.morphdb' )

################################################################################
## Standalone program
################################################################################

def main(): # :: IO ()
    if len( sys.argv ) != 3:
        print 'Usage: %s srcFile destFile' % sys.argv[0]
        return
    inp = unicode( open( sys.argv[1], 'r' ).read(), 'utf-8' )
    out = ms2str( getMorphemes1( inp, bs=[u'記号'] ) ) # filter punctuation
    open( sys.argv[2], 'w' ).write( out )

if __name__ == '__main__': main()
