#!/usr/bin/env python
#-*- coding: utf-8 -*-
import codecs, subprocess
# type StarDict = Map Int { lookup, key }

################################################################################
## Loading J Sensei files
################################################################################
# :: FilePath -> m Map Int (Expr,Read,Index)
def loadDatDict( filename, d={} ): # !! no longer used as the .dat data is provided elsewhere in a better way
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
def load( path ): return _load( '%s.idx' % path, '%s.dict' % path )

# :: FilePath -> FilePath -> StarDict
def _load( idxPath, dictPath ):
   idx = loadIdx( idxPath )
   d = crossRef( idx, dictPath )
   print 'Loaded %d from %s' % ( len(d), idxPath )
   return d

################################################################################
## Utils
################################################################################
def sum( xs ): return reduce( lambda x,a: x+a, xs )
def prints( xs ): # useful for displaying a list of unicode when debugging
   for x in xs: print x

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
## Combine Data
################################################################################
# Map Int { key1 :: a, key2, :: IndiciesStr } -> Maybe key1 -> Maybe key2 -> Map Index [a]
def rev( dic, a='key', b='lookup' ):
   D = {}
   for i,d in dic.items():
      x = d[a]
      ns = d[b].strip().split(',')
      for n in ns:
         if not n in D: D[n] = []
         D[n] = D[n] + [x]
   return D

# Map Int { reading :: Str, ... } -> m ()
def linkAudio( d ):
   for i in d:
      d[i]['phoneticIndex'] = swords.index( d[i]['read'] )
      d[i]['audio'] = dword[ d[i]['phoneticIndex'] ]['key']
      d[i]['sentAudio'] = d[i]['audio'].replace('jw','js')

# [ Map Int Entry ] -> Map Int Entry # Int keys aren't preserved
def merge( ds ):
   D = {}
   i = 0
   for d in ds:
      for k in d:
         D[ i ] = d[k]
         i += 1
   return D

# Map Int { key :: Index, lookup :: ExampleJapSent } -> PackDict
def parseExampleDict( d ):
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

# Map Int { expr, read, sentExpr, index } -> StarDict -> StarDict -> PacNameStr -> PackDict
def pack( exampleDict, engMeanDict, jpnMeanDict, packName ):
   # word expr, word read, sentence expr
   ed = parseExampleDict( exampleDict )
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

# PackDict -> TsvStr
def mkTsv( dic ):
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

################################################################################
## Output results
################################################################################
# :: StarDict FileName AudioData -> SubDirPath -> IO ()
def writeAudio( d, path ):
   for i in d:
      try: open( path+'/'+d[i]['key'], 'wb' ).write( d[i]['lookup'] )
      except: print 'Failed to write %s, continuing...' % i

# PackDict -> IO ()
def writeTsv( d, path='jsensei.tsv' ):
   tsv = mkTsv( d )
   open( 'jsensei.tsv', 'wb' ).write( tsv.encode('utf-8') )

################################################################################
## Load E->J
################################################################################
ejA = load( 'JIB_ejA' ) # Map Int (EnglishMeaning,[Index])
ejB = load( 'JIB_ejB' )
ejS = load( 'JIB_ejS' )

#ejSi = load( 'JIB_ejS.index.example' ) # Map Int (EnglishSentence,[Index])

#ejSir = load( 'JIB_ejS.index.example.res' ) # Map Int (Index,JapExpr,JapSentence)

#ejAr = load( 'JIB_ejA.res' ) # Map Index ???
#ejBr = load( 'JIB_ejB.res' )
#ejSr = load( 'JIB_ejS.res' ) # Map Index XMLinfo (example sentence, audio file name, romaji, etc)

################################################################################
## Load J->E
################################################################################
jeA = load( 'JIB_jeA' )
jeB = load( 'JIB_jeB' )
jeS = load( 'JIB_jeS' )

#jeAc = load( 'JIB_jeA.component' )
#jeBc = load( 'JIB_jeB.component' )
#jeSc = load( 'JIB_jeS.component' )

#jeAi = load( 'JIB_jeA.index.example' )
#jeBi = load( 'JIB_jeB.index.example' )
#jeSi = load( 'JIB_jeS.index.example' )

jeAir = load( 'JIB_jeA.index.example.res' )
jeBir = load( 'JIB_jeB.index.example.res' )
jeSir = load( 'JIB_jeS.index.example.res' )

#jeAr = load( 'JIB_jeA.res' )
#jeBr = load( 'JIB_jeB.res' )
#jeSr = load( 'JIB_jeS.res' )

################################################################################
## Create Packs and write files
################################################################################
# Map Int (FileName,AudioData) # close to phonetic ordering
dword = load( 'headwords' ); writeAudio( dword, 'wordAudio' )
dsent = load( 'sentences' ); writeAudio( dsent, 'sentenceAudio' )

# audio files are stored in approx phonetic order, so assign every word a phonetic index
swords = open('words.sorted','rb').read().decode('utf-8').split('\n') # from `jsort.pl < words.unsorted > words.sorted`

dA = pack( jeAir, ejA, jeA, 'A' )
dB = pack( jeBir, ejB, jeB, 'B' )
dS = pack( jeSir, ejS, jeS, 'S' )
d = merge( [dA,dB,dS] )
writeTsv( d )
