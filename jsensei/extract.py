#!/usr/bin/env python
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
ejMean = mergeDatDicts( [ejA,ejB,ejS] ) # Map EnglishMeaning [Index]

ejSi = load( 'JIB_ejS.index.example', dat ) # Map Int (EnglishSentence,[Index],[JapExpr],[JapRead])
ejSentence = mergeDatDicts( [ejSi] ) # Map EnglishSentence [Index]

#ejSir = load( 'JIB_ejS.index.example.res' ) # Map Int (Index,JapExpr, JapSentence)
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
jeMean = mergeDatDicts( [jeA,jeB,jeS] ) # Map JapMeaning [Index]

jeAc = load( 'JIB_jeA.component' )
jeBc = load( 'JIB_jeB.component' )
jeSc = load( 'JIB_jeS.component' )
jeComponent = mergeDicts( [jeAc,jeBc,jeSc] ) # Map Component Examples

jeAi = load( 'JIB_jeA.index.example' )
jeBi = load( 'JIB_jeB.index.example' )
jeSi = load( 'JIB_jeS.index.example' )
jeSentence = mergeDatDicts( [jeAi,jeBi,jeSi] ) # Map JapSentence [Index]

jeAir = load( 'JIB_jeA.index.example.res' )
jeBir = load( 'JIB_jeB.index.example.res' )
jeSir = load( 'JIB_jeS.index.example.res' )
jeIndex = mergeDicts( [indexifyDict(jeAir),indexifyDict(jeBir),indexifyDict(jeSir)] ) # Map Index JapExpr+JapSentence

jeAr = load( 'JIB_jeA.res' )
jeBr = load( 'JIB_jeB.res' )
jeSr = load( 'JIB_jeS.res' )

################################################################################
## Load Romaji->E
################################################################################
jieA = load( 'JIB_jieA', dat )
jieB = load( 'JIB_jieB', dat )
jieS = load( 'JIB_jieS', dat )
jieMean = mergeDatDicts( [jieA,jieB,jieS] ) # Map JapMeaning [Index]

jieAi = load( 'JIB_jieA.index.example' )
jieBi = load( 'JIB_jieB.index.example' )
jieSi = load( 'JIB_jieS.index.example' )
jieSentence = mergeDatDicts( [jieAi,jieBi,jieSi] ) # Map JapSentence [Index]

#jieAir = load( 'JIB_jieA.index.example.res' )
#jieBir = load( 'JIB_jieB.index.example.res' )
#jieSir = load( 'JIB_jieS.index.example.res' )
#jieIndex = mergeDicts( [indexifyDict(jieAir),indexifyDict(jieBir),indexifyDict(jieSir)] ) # Map Index JapExpr+JapSentence

#jieAr = load( 'JIB_jieA.res' )
#jieBr = load( 'JIB_jieB.res' )
#jieSr = load( 'JIB_jieS.res' )

################################################################################
## Link Audio
################################################################################
# audio files are stored in phonetic order, so assign every word a phonetic index
import locale
locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
words = [ dat[i]['reading'] for i in dat ]
open('words.unsorted','wb').write( (u'\n'.join( words ) +u'\n').encode('utf-8') )
swords = open('words.sorted','rb').read().decode('utf-8').split('\n') # from `jsort.pl < words.unsorted > words.sorted`
#swords = sorted( words, cmp=locale.strcoll ) #FIXME: this puts katakana after hiragana, thus is wrong

################################################################################
## Merge everything
################################################################################
D = {}
for w in dat.values():
   i = w['id']
   D[i] = {}
   D[i]['DatIndex'] = w['id']
   try:
      D[i]['SortedIndex'] = swords.index( w['reading'] )
      D[i]['Audio'] = dword[ D[i]['SortedIndex'] ]['key']
   except Exception, e:
      print i
      print repr(w['reading'])
      print swords.index( w['reading'] )
      raise e
   D[i]['Expr'] = w['expression']
   #assert w['expression'] == w['word']
   D[i]['Read'] = w['reading']
   D[i]['Furi'] = w['withFurigana']
   D[i]['Mean'] = []
   D[i]['JMean'] = []
   D[i]['RMean'] = []
   D[i]['SentenceMean'] = []
   D[i]['SentenceJMean'] = []
for meaning,idxs in ejMean.items():
   for i in idxs: D[i]['Mean'] = D[i]['Mean']+[meaning]
for meaning,idxs in jeMean.items():
   for i in idxs: D[i]['JMean'] = D[i]['JMean']+[meaning]
for meaning,idxs in jieMean.items():
   for i in idxs: D[i]['RMean'] = D[i]['RMean']+[meaning]
for i in jeIndex: D[i]['SentenceExpr'] = jeIndex[i]
for meaning,idxs in ejSentence.items():
   for i in idxs: D[i]['SentenceMean'] = D[i]['SentenceMean']+[meaning]
for meaning,idxs in jeSentence.items():
   for i in idxs: D[i]['SentenceJMean'] = D[i]['SentenceJMean']+[meaning]
