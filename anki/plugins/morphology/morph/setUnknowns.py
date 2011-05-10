import util
import morphemes as m

def pre( ed ):
   if not util.requireKnownDb(): return 'BAIL'
   bs = util.getBlacklist( ed )
   return { 'bs':bs, 'kdb': m.loadDb( util.knownDbPath ), 'mp':m.mecab(None) }

def per( st, f ):
   ms = m.getMorphemes( st['mp'], f[ 'Expression' ], bs=st['bs'] )
   us = []
   for x in ms:
      if not x in st['kdb']: us += [ x[0] ]
   f[ 'unknowns' ] = u','.join( us )
   return st

def post( st ):
   st['mp'].kill()

util.addDoOnSelectionBtn( 'Set unknowns', 'unknowns set', 'Analyzing...', pre, per, post )
