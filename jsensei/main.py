import codecs, re

################################################################################
## Seem to work
################################################################################

# Load *.dat files
def loadDatDict( filename, d={} ):
    ls = codecs.open( filename, encoding='utf-8').read().split('\n')[:-1]
    for l in ls:
        # First get word with furigana, without, and index
        ps = l.split()
        assert len(ps) == 2 or len(ps) == 3
        wf = w = ps[0]
        i = int( ps[-1] )
        if len(ps) == 3: w = ps[1][1:][:-1] # extract from inside brackets
        # Next separate furigana if applicable
        e = r = wf
        ps = wf.split('^')
        assert len(ps) <= 2
        if len(ps) == 2:
            e = ps[0]
            r = ps[1]
        # 9520 for key=wf, 9617 for key=i
        d[ i ] = { 'id':i, 'word':w, 'withFurigana':wf, 'expression':e, 'reading':r }
    return d

def diffWithKore(): # :: IO ([Item],[Item])
    # Check differences
    notInJD = []
    for n in kd:
        matchFound = False
        for m in jd:
            if kd[n]['expression'] == jd[m]['expression']:
                matchFound = True
                break
        if not matchFound: notInJD.append( n )
    # 20 things in Kore but not in JSensei

    # Check differences in other direction
    notInKore = []
    for n in jd:
        matchFound = False
        for m in kd:
            if kd[m]['expression'] == jd[n]['expression']:
                matchFound = True
                break
        if not matchFound: notInKore.append( n )
    # 3568 not in kore
    return (notInJD, notInKore)


################################################################################
## Testing
################################################################################

# Load word indexes
jd,jbd = {},{}
for f in [ '%s%d.dat' % (m,n) for n in range(1,11) for m in 'AB' ]: loadDatDict( f, jd )
#for f in [ '%s%d.dat' % (m,n) for n in range(1,11) for m in 'B' ]: loadDatDict( f, jbd )


# Load Kore
def loadKore( filename='kore.txt' ):
   kd = {}
   i = 0
   for l in open( filename ).read().split('\n'):
       ps = l.split('\t')
       kd[i] = { 'expression':ps[0].decode('utf-8'), 'reading':ps[1].decode('utf-8'), 'meaning':ps[2] }
       i += 1
   return kd
#kd = loadKore()

Bdict = open('JIB_ejB.dict','rb').read()
Bidx = open('JIB_ejB.idx','rb').read()
Bresidx = open('JIB_ejB.res.idx','rb').read()
Bresdict = open('JIB_ejB.res.dict','rb').read()
Wdict = open( 'headwords.dict','rb').read()

def loadResIdx( path ):
   d = {}
   b = open( path, 'rb' ).read()
   n = 0
   for i in range( len(b)/18 ):
      s = i*18
      t = s+18
      r = b[s:t]
      d[ n ] = { 'unknown':r[9:], 'index':r[:9] }
      n += 1
   return d
bri = loadResIdx( 'JIB_ejB.res.idx' ) # :: Map Index (Unknown,Index)
print '%d .res.idx records' % len(bri)

def loadIdx( path ):
   d = {}
   b = open( path, 'rb' ).read()
   # read meaning until we see \x00, then grab the 9 unknown bytes
   s = t = 0
   maxS = len(b)
   i = 0
   while s < maxS:
      t = s + b[s:].find('\x00')
      #print s,t,repr(b[s:s+50])
      if t == -1: break
      meaning = b[s:t]
      unknown = b[t:t+9]
      s = t+9
      d[ i ] = { 'meaning':meaning, 'unknown':unknown, 'order':i }
      i += 1
   return d
#bi = loadIdx( 'JIB_ejB.idx' ) # :: Map Order (Meaning, Unknown?, Order)
#print '%d .idx records' % len(bi)

def loadDict( path ):
   d = {}
   ls = open( path, 'rb' ).read().split('\n')[:-1]
   for i,l in enumerate(ls):
      d[i] = {'line':i,'index':l}
   return d
bd = loadDict( 'JIB_ejB.dict' ) # :: Map LineNo Index?
print '%d .dict records' % len(bd)

def loadWordsIdx( path ):
   d = {}
   b = open( path, 'rb' ).read()
   n = 0
   for i in range( len(b)/21 ):
      s = i*21
      t = s+21
      r = b[s:t]
      d[ n ] = { 'unknown':r[12:], 'audioFile':r[:12] }
      n += 1
   return d
wi = loadWordsIdx( 'headwords.idx' )
print '%d words.idx records' % len(wi)

################################################################################
## Utils
################################################################################
def sum( xs ): return reduce( lambda x,a: x+a, xs )

def matchOn( a, b, key ):
   matches = []
   for n in a:
      for m in b:
         if a[n][key] == b[m][key]: matches.append( (n,m,a,b) )
   return matches
def search( d, key, s ): return [ d[k] for k in d if s in d[k][key] ]
def searchP( d, key, s ):
   for x in search( d, key, s ): print x

################################################################################
## Completely correct
################################################################################

#### Audio

def loadAudio( path ): # :: Map Order (Data, Filename)
   d = {}
   b = open( path,'rb').read()
   magic = '\x00\x00\x00\x18ftypmp42'
   for i,p in enumerate( b.split( magic )[1:] ):
      x = magic+p
      s = x.find( '\xa9nam' )
      name = x[s+20:s+20+8] if s != -1 else 'UNKNOWN_'+str(i)
      name += '.m4a'
      d[i] = { 'data':x, 'audioFile':name }
   return d
wad = loadAudio( 'headwords.dict' )
sad = loadAudio( 'sentences.dict' )
print '%d word audio records' % len(wad)
print '%d sentence audio records' % len(sad)

def writeAudioFiles( d, path ):
   for i in d:
      try: open( path+'/'+d[i]['audioFile'], 'wb' ).write( d[i]['data'] )
      except:
         print i
         print path+'/'+d[i]['audioFile']
         print 'ERROR!!!! continuing...'
#writeAudioFiles( wad, 'wordAudio' )
#writeAudioFiles( sad, 'sentenceAudio' )

#### Index
def getUint( xs ):
   [a,b,c,d] = [ ord(x) for x in xs ]
   return a*256**3 + b*256**2 + c*256**1 + d*256**0
def loadStarDictIdx( path ):
   d = {}
   b = open( path, 'rb' ).read()
   s, maxS, i = 0, len(b), 0
   while s < maxS:
      t = b.find( '\x00', s ) +1
      word_str = b[s:t-1] # null terminated utf-8 word_str (but we drop the null)
      word_data_offset = getUint( b[t:t+4] )
      word_data_size = getUint( b[t+4:t+8] )
      d[i] = { 'meaning':word_str, 'offset':word_data_offset, 'size':word_data_size }
      #d[i]['lookup'] = lookupDict( Bdict, d[i] ) #FIXME: fragile
      s = t+8
      i += 1
   return d
ai = loadStarDictIdx( 'JIB_ejA.idx' ) # :: Map Order (Meaning, Offset, Size)
bi = loadStarDictIdx( 'JIB_ejB.idx' ) # :: Map Order (Meaning, Offset, Size)
print '%d A.idx records' % len(ai)
print '%d B.idx records' % len(bi)

#### Cross-reference with dict
def lookupDict( src, e ): return src[ e['offset'] : e['offset']+e['size'] ]
def crossIdxAndDict( idx, dic ): # :: Idx DB -> FilePath -> DB
   dic = open( dic, 'rb' ).read()
   for k in idx:
      ms = lookupDict( dic, idx[k] ).strip().split(',')
      idx[k]['indicies'] = [ int(m) +1 for m in ms ]
crossIdxAndDict( ai, 'JIB_ejA.dict' )
crossIdxAndDict( bi, 'JIB_ejB.dict' )
