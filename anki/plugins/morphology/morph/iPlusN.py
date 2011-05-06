import util
import morphemes as m

def pre( ed ):
   if not util.requireKnownDb(): return 'BAIL'
   bs = util.getBlacklist( ed )
   return { 'bs':bs, 'kdb': m.loadDb( util.knownDbPath ), 'mp':m.mecab(None) }

def per( st, f ):
   ms = m.getMorphemes( st['mp'], f[ 'Expression' ], bs=st['bs'] )
   N = 0
   for x in ms:
      if not x in st['kdb']: N += 1
   f[ 'iPlusN' ] = u'%d' % N
   return st

def post( st ):
   st['mp'].kill()

util.addDoOnSelectionBtn( 'Generate i+N', 'Finding N', 'Analyzing...', pre, per, post )
