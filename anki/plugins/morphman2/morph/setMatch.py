from PyQt4.QtCore import *
from PyQt4.QtGui import *
import util
from util import infoMsg, errorMsg
import matchingLib as ML
import morphemes as M

def pre( ed ):
   path = QFileDialog.getOpenFileName( caption='Open db', directory=util.knownDbPath )
   if not path: return 'BAIL'
   bs = util.getBlacklist( ed )

   db = M.MorphDb( path ).db
   return { 'mp':M.mecab(None), 'fmmap':{}, 'mfmap':{}, 'db':db, 'bs':bs, 'ed':ed }

def per( st, f ):
   ms = M.getMorphemes( st['mp'], f['Expression'], bs=st['bs'] )
   for m in ms:
      if m not in st['mfmap']: st['mfmap'][m] = []
      if f not in st['mfmap'][m]: st['mfmap'][m].append( f )
   return st

def uniqueFlatten( xss ): return list(set( [ x for xs in xss for x in xs ] ))

# get maximum cardinality morpheme<->fact matching
def getMatches( st, allM, allF ):
   pairs = []
   for m in allM:             # for ea morpheme we want to learn
      if m not in st['mfmap']: continue
      for f in st['mfmap'][m]:   # for ea fact we can learn said morpheme from
         pairs.append( (m,f) )      # add morpheme,fact pair to graph

   A, B = [], []
   for (a,b) in pairs:
      if a not in A: A.append( a )
      if b not in B: B.append( b )

   g = ML.Graph()
   g.mkMatch( pairs )
   infoMsg( '%d possible pairings for %d/%d morphemes to %d/%d facts, %s. Calculating now...' % ( len(pairs), len(A), len(allM), len(B), len(allF), g.complexity() ), p=st['ed'] )
   return g.doMatch()

def post( st ):
   util.killMecab( st )

   allM = st['db'].keys()                       # morphemes to learn
   allF = uniqueFlatten( st['mfmap'].values() ) # facts to learn from
   ps = getMatches( st, allM, allF )

   infoMsg( 'Successfully matched %d pairs.' % len(ps), p=st['ed'] )
   for m,f in ps: f['matchedMorpheme'] = u'%s' % m.base
   infoMsg( 'Saved' )

util.addDoOnSelectionBtn( 'Morph match', 'Match morphs', 'Generating match db...', pre, per, post )
