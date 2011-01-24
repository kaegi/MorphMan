#!/usr/bin/env python
# fork of code for exploring possible encryption of .res.dict files

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
   return applyDat( dat, d ) if dat else d
# :: FilePath -> FilePath -> StarDict
def _load( idxPath, dictPath ):
   idx = loadIdx( idxPath )
   d = crossRef( idx, dictPath )
   print 'Loaded %d from %s' % ( len(d), idxPath )
   return d

# :: Dat -> StarDict -> StarDict
def applyDat( dat, dic ):
   for k in dic:
      ms = dic[k]['lookup'].strip().split(',')
      dic[k]['indicies'] = [ int(m) +1 for m in ms ]
      dic[k]['expressions'] = [ dat[i]['expression'] for i in dic[k]['indicies'] ]
      dic[k]['readings'] = [ dat[i]['reading'] for i in dic[k]['indicies'] ]
   return dic

def indexifyDict( d, key='key' ): # StarDict -> Maybe Key -> StarDict
   D = {}
   for i in d:
      D[i] = {}
      for k in d[i]: D[i][k] = d[i][k]
      D[i][key] = int( d[i][key].strip() )+1
   return D

def mergeDicts( ds, f=lambda new,old:new ):
   D = {}
   for d in ds:
      for i in d:
         k = d[i]['key']
         v = d[i]['lookup']
         if k in D: D[k] = f( v, D[k] )
         else: D[k] = f( v, None )
   return D

def mergeDatDicts( ds ):
   def f( new, old ):
      news = [ int(m)+1 for m in new.strip().split(',') ]
      old = old or []
      return list(set( news+old ) )
   return mergeDicts( ds, f )

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
def play( e, basedir='wordAudio/' ):
   path = basedir + e['Audio']
   print path
   return subprocess.call( ['mplayer', '%s' % path] )

def testa( e ):
   play( e )
   print e['SentenceExpr']
   print e['Expr']
   print e['Read']
   print e['Mean']
   # audio+read, sentence+mean+jmean

################################################################################
## Output results
################################################################################
# :: StarDict FileName AudioData -> SubDirPath -> IO ()
def writeAudio( d, path ):
   for i in d:
      try: open( path+'/'+d[i]['key'], 'wb' ).write( d[i]['lookup'] )
      except: print 'Failed to write %s, continuing...' % i

################################################################################
## Load E->J
################################################################################
ejAr = load( 'JIB_ejA.res' ) # Map Index ???
ejBr = load( 'JIB_ejB.res' )
ejSr = load( 'JIB_ejS.res' ) # Map Index XMLinfo (example sentence, audio file name, romaji, etc)
################################################################################
## Load J->E
################################################################################
jeAr = load( 'JIB_jeA.res' )
jeBr = load( 'JIB_jeB.res' )
jeSr = load( 'JIB_jeS.res' )
################################################################################
## Load Romaji->E
################################################################################
jieAr = load( 'JIB_jieA.res' )
jieBr = load( 'JIB_jieB.res' )
jieSr = load( 'JIB_jieS.res' )
################################################################################
## Collect blobs
################################################################################

def getBlobs( resDic ): return [ d['lookup'] for d in resDic.values() ]
gb = getBlobs
blobsAE = gb( ejAr )
blobsBE = gb( ejBr )
blobsSE = gb( ejSr )
blobsE = blobsAE + blobsBE
blobsAJ = gb( jeAr )
blobsBJ = gb( jeBr )
blobsJ = blobsAJ + blobsBJ
blobsAR = gb( jieAr )
blobsBR = gb( jieBr )
blobsR = blobsAR + blobsBR
blobs = blobsE + blobsJ + blobsR

def collect( bs ):
   d = {}
   for b in bs:
      pre = b[0]
      if not pre in d: d[pre] = 0
      d[pre] = d[pre] + 1
   return d

def getWithPre( bs, pre ):
   for b in bs:
      if b.find(pre) != -1: return b

def starts( bs ):
   d = {}
   for n,b in enumerate(bs):
      if b[0] in d: continue # already handled this prefix
      same = [ a for a in bs if a != b and a[0] == b[0] ]
      if len( same ) == 0: # this is the only one with this prefix
         d[ b[0] ] = (len(b),b)
         break
      a = same[0]
      i = 0
      while i < len(b):
         if a.find( b[:i] ) == -1: break
         i += 1
      d[ b[0] ] = (i,b[:i])
   return d
dae = starts( blobsAE )
d = starts( blobs )
a = blobs[0]
b = blobs[1]
s = blobsSE[0]

def count( cs ):
   d = {}
   for c in cs:
      if not c in d: d[c] = 0
      d[c] = d[c] + 1
   return d
