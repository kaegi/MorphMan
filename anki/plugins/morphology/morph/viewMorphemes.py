from PyQt4.QtCore import *
from PyQt4.QtGui import *

import morphemes as m
import util

def pre( ed ):
   if not util.requireKnownDb(): return 'BAIL'
   bs = util.getBlacklist( ed )
   return { 'ed':ed, 'txt':'', 'bs':bs }

def per( st, f ):
   st['txt'] += f['Expression']
   return st

def post( st ):
   import morphemes as m
   mp = m.mecab( None )
   ms = m.getMorphemes( mp, st['txt'], bs=st['bs'] )
   mp.kill()
   txt = m.ms2str( ms ).decode('utf-8')

   kdb = m.loadDb( util.knownDbPath )
   newMs = [ x for x in ms if x not in kdb ]
   newTxt = m.ms2str( newMs ).decode('utf-8')

   txt = '-----All-----\n' + txt + '\n-----New-----\n' + newTxt
   QMessageBox.information( st['ed'], 'Morphemes', txt )

util.addDoOnSelectionBtn( 'View morphemes', 'View morphemes', 'Viewing...', pre, per, post, shortcut='Ctrl+V' )
