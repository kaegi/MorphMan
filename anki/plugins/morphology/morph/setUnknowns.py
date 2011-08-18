import util
import morphemes as M

def pre( ed ):
   if not util.requireKnownDb(): return 'BAIL'
   bs = util.getBlacklist( ed )
   return { 'bs':bs, 'kdb': M.loadDb( util.knownDbPath ), 'mp':M.mecab(None) }

def per( st, f ):
   ms = M.getMorphemes( st['mp'], f[ 'Expression' ], bs=st['bs'] )
   us = []
   for x in ms:
      if not x in st['kdb']: us += [ x[0] ]
   f[ 'unknowns' ] = u','.join( us )
   return st

def post( st ):
   util.killMecab( st )

util.addDoOnSelectionBtn( 'Set unknowns', 'unknowns set', 'Analyzing...', pre, per, post )
