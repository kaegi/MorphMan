#!/usr/bin/env python
#-*- coding: utf-8 -*-
import codecs, re, subprocess
# type StarDict = Map Order IdxEntry

################################################################################
## Loading data
################################################################################
# :: FilePath -> m Map Order (Expr,Read,Index)
def loadDatDict( filename, d={} ):
    ls = codecs.open( filename, encoding='utf-8').read().split('\n')[:-1]
    for l in ls:
        ps = l.split() # First get word with furigana, without, and index
        assert len(ps) == 2 or len(ps) == 3
        wf = w = ps[0]
        i = int( ps[-1] )
        if len(ps) == 3: w = ps[1][1:][:-1] # extract from inside brackets
        e = r = wf # Next separate furigana if applicable
        ps = wf.split('^')
        assert len(ps) <= 2
        if len(ps) == 2: e,r = ps[0],ps[1]
        d[ i ] = { 'id':i, 'word':w, 'withFurigana':wf, 'expression':e, 'reading':r }
    return d

# :: Str -> Unsigned Int
def getUint( xs ): # network byte order
   [a,b,c,d] = [ ord(x) for x in xs ]
   return a*256**3 + b*256**2 + c*256**1 + d*256**0

# :: FilePath -> StarDict
def loadIdx( path ):
   d = {}
   b = open( path, 'rb' ).read()
   s, maxS, i = 0, len(b), 0
   while s < maxS:
      t = b.find( '\x00', s ) +1
      word_str = b[s:t-1] # null terminated utf-8 word_str (but we drop the null)
      word_data_offset = getUint( b[t:t+4] )
      word_data_size = getUint( b[t+4:t+8] )
      d[i] = { 'key':word_str, 'offset':word_data_offset, 'size':word_data_size }
      s = t+8
      i += 1
   return d

# :: DictStr -> IdxEntry -> DictData
def lookupDict( src, e ): return src[ e['offset'] : e['offset']+e['size'] ]

# :: StarDict -> FilePath -> StarDict
def crossRef( idx, dic ):
   dic = open( dic, 'rb' ).read()
   for k in idx: idx[k]['lookup'] = lookupDict( dic, idx[k] )
   return idx

# :: FilePath -> Maybe Dat -> StarDict
def load( path, dat=None ):
   d = _load( '%s.idx' % path, '%s.dict' % path )
   return d # used to apply dat in wrong way
# :: FilePath -> FilePath -> StarDict
def _load( idxPath, dictPath ):
   idx = loadIdx( idxPath )
   d = crossRef( idx, dictPath )
   print 'Loaded %d from %s' % ( len(d), idxPath )
   return d

def mergeDicts( ds, f=lambda new,old:new ):
   D = {}
   for d in ds:
      for i in d:
         k = d[i]['key']
         v = d[i]['lookup']
         if k in D: D[k] = f( v, D[k] )
         else: D[k] = f( v, None )
   return D

################################################################################
## Utils
################################################################################
def sum( xs ): return reduce( lambda x,a: x+a, xs )
def prints( xs ):
   for x in xs: print x
def getDictDupes( a, b ):
   xs = []
   for n in a:
      for m in b:
         if n != m and a[n] == b[m]: xs.append( (n,m,a[n],b[m]) )
   return xs
def getDictOfDictDupes( a, b, k, k2 ):
   xs = []
   for n in a:
      for m in b:
         if n != m and a[n][k] == b[m][k]: xs.append( (n,m,a[n][k],b[m][k],a[n][k2],b[m][k2]) )
   return xs

def playN( n, basedir='wordAudio/' ):
   path = basedir + dword[ n ]['key']
   subprocess.call( ['mplayer', path ] )
   print 'Played %d th sound file in phonetic ordering' % n

def play( e, wbasedir='wordAudio/', sbasedir='sentenceAudio/' ):
   wpath = wbasedir + e['audio']
   spath = sbasedir + e['sentAudio']
   subprocess.call( ['mplayer', '%s' % wpath] )
   subprocess.call( ['mplayer', '%s' % spath] )

def test( e ):
   play( e )
   print 'Sent',e['sentExpr']
   print 'Expr',e['expr']
   print 'Read',e['read']
   print 'English meanings:'
   for x in e['mean']: print '    '+x
   print 'Japanese meanings:'
   for x in e['meanJpn']: print '    '+x

################################################################################
## Output results
################################################################################
# :: StarDict FileName AudioData -> SubDirPath -> IO ()
def writeAudio( d, path ):
   for i in d:
      try: open( path+'/'+d[i]['key'], 'wb' ).write( d[i]['lookup'] )
      except: print 'Failed to write %s, continuing...' % i

################################################################################
## Load Core
################################################################################

# Map Index (JapExpression, JapReading, JapFurigana)
dat = {}
#TODO: should we also use S1 and UA1-10?
for f in [ '%s%d.dat' % (m,n) for n in range(1,11) for m in 'AB' ]: loadDatDict(f, dat )
print 'Loaded %d from .dat files' % len( dat )

# Map Int (FileName,AudioData)
dword = load( 'headwords' ); writeAudio( dword, 'wordAudio' )
dsent = load( 'sentences' ); writeAudio( dsent, 'sentenceAudio' )

################################################################################
## Load E->J
################################################################################
ejA = load( 'JIB_ejA', dat ) # Map Int (EnglishMeaning,[Index],[JapExpr],[JapRead])
ejB = load( 'JIB_ejB', dat )
ejS = load( 'JIB_ejS', dat )
#ejMean = mergeDatDicts( [ejA,ejB,ejS] ) # Map EnglishMeaning [Index]

ejSi = load( 'JIB_ejS.index.example', dat ) # Map Int (EnglishSentence,[Index],[JapExpr],[JapRead])
#ejSentence = mergeDatDicts( [ejSi] ) # Map EnglishSentence [Index]

ejSir = load( 'JIB_ejS.index.example.res' ) # Map Int (Index,JapExpr, JapSentence)
#ejIndex = mergeDicts( [indexifyDict(ejSir)] ) # Map Index JapExpr+JapSentence

ejAr = load( 'JIB_ejA.res' ) # Map Index ???
ejBr = load( 'JIB_ejB.res' )
ejSr = load( 'JIB_ejS.res' ) # Map Index XMLinfo (example sentence, audio file name, romaji, etc)

################################################################################
## Load J->E
################################################################################
jeA = load( 'JIB_jeA', dat )
jeB = load( 'JIB_jeB', dat )
jeS = load( 'JIB_jeS', dat )
#jeMean = mergeDatDicts( [jeA,jeB,jeS] ) # Map JapMeaning [Index]

jeAc = load( 'JIB_jeA.component' )
jeBc = load( 'JIB_jeB.component' )
jeSc = load( 'JIB_jeS.component' )
#jeComponent = mergeDicts( [jeAc,jeBc,jeSc] ) # Map Component Examples

jeAi = load( 'JIB_jeA.index.example' )
jeBi = load( 'JIB_jeB.index.example' )
jeSi = load( 'JIB_jeS.index.example' )
#jeSentence = mergeDatDicts( [jeAi,jeBi,jeSi] ) # Map JapSentence [Index]

jeAir = load( 'JIB_jeA.index.example.res' )
jeBir = load( 'JIB_jeB.index.example.res' )
jeSir = load( 'JIB_jeS.index.example.res' )
#jeIndex = mergeDicts( [indexifyDict(jeAir),indexifyDict(jeBir),indexifyDict(jeSir)] ) # Map Index JapExpr+JapSentence

jeAr = load( 'JIB_jeA.res' )
jeBr = load( 'JIB_jeB.res' )
jeSr = load( 'JIB_jeS.res' )

################################################################################
## Link Audio
################################################################################
# audio files are stored in phonetic order, so assign every word a phonetic index
swords = open('words.sorted','rb').read().decode('utf-8').split('\n') # from `jsort.pl < words.unsorted > words.sorted`

################################################################################
## Extract Word Expr, Word Read, Sentence Expr
################################################################################
def ier( d ):
   D = {}
   xs = [ (d[i]['key'],d[i]['lookup']) for i in d ]
   for i,(index,x) in enumerate(xs):
      # expression?^reading [expression] | sentenceExpr
      wordRaw, sentence = x.split('|')
      # get reading and possibly expr
      ps = wordRaw.split() # expr^read
      wf = ps[0]
      if '^' in wf: expr,read = wf.split('^')
      else: expr = read = wf
      # definately get expr if bracket version is there
      if len( ps ) == 2:
         wo = ps[1]
         expr2 = wo.replace('\xe3\x80\x90','').replace('\xe3\x80\x91','').replace('(','').replace(')','')
         # sanity check
         if expr2 != expr and expr != read:
            print 'MISMATCH: raw:%s -> expr:%s vs expr2:%s' % (wordRaw,expr,expr2)
            print 'Failing out'
            return None
         expr = expr2
      D[i] = { 'expr':expr.decode('utf-8'), 'read':read.decode('utf-8'), 'sentExpr':sentence.decode('utf-8'), 'index':index }
   return D

def rev( dic, a='key', b='lookup' ):
   D = {}
   for i,d in dic.items():
      x = d[a]
      ns = d[b].strip().split(',')
      for n in ns:
         if not n in D: D[n] = []
         D[n] = D[n] + [x]
   return D

def linkAudio( d ):
   for i in d:
      d[i]['phoneticIndex'] = swords.index( d[i]['read'] )
      d[i]['audio'] = dword[ d[i]['phoneticIndex'] ]['key']
      d[i]['sentAudio'] = d[i]['audio'].replace('jw','js')

def pack( exampleDict, engMeanDict, jpnMeanDict, packName ):
   # word expr, word read, sentence expr
   ed = ier( exampleDict )
   # set pack name
   for i in ed: ed[i]['indexPack'] = packName.decode('utf-8')
   # word mean in eng
   md = rev( engMeanDict )
   for i in ed: ed[i]['mean'] = [ x.decode('utf-8') for x in md[ ed[i]['index'] ] ]
   # word mean in jpn
   jmd = rev( jpnMeanDict )
   for i in ed: ed[i]['meanJpn'] = [ x.decode('utf-8') for x in jmd[ ed[i]['index'] ] ]
   # word audio
   linkAudio( ed )
   return ed

def merge( ds ):
   D = {}
   i = 0
   for d in ds:
      for k in d:
         D[ i ] = d[k]
         i += 1
   return D

def mkCsv( dic ):
   #s = ','.join(d.values()[0].keys())
   s = ''
   for e in dic.values():
      s += u'\t'.join(
      [ e['index']
      , e['indexPack']
      , e['expr']
      , e['read']
      , u'; '.join( e['mean'] )
      , u'; '.join( e['meanJpn'] )
      , e['audio']
      , e['sentExpr']
      , e['sentAudio']
      ] ) +'\n'
   return s
da = pack( jeAir, ejA, jeA, 'A' )
db = pack( jeBir, ejB, jeB, 'B' )
ds = pack( jeSir, ejS, jeS, 'S' )
d = merge( [da,db,ds] )
csv = mkCsv( d )
open( 'jsensei.tsv', 'wb' ).write( csv.encode('utf-8') )
