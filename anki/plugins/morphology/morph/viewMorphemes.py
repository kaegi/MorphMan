from PyQt4.QtCore import *
from PyQt4.QtGui import *

import morphemes as M
import util

def pre( ed ):
   if not util.requireKnownDb(): return 'BAIL'
   bs = util.getBlacklist( ed )
   return { 'ed':ed, 'txt':'', 'bs':bs, 'mp':M.mecab(None) }

def per( st, f ):
   st['txt'] += f['Expression']
   return st

def post( st ):
   ms = M.getMorphemes( st['mp'], st['txt'], bs=st['bs'] )
   util.killMecab( st )
   txt = M.ms2str( ms ).decode('utf-8')

   kdb = M.loadDb( util.knownDbPath )
   newMs = [ x for x in ms if x not in kdb ]
   newTxt = M.ms2str( newMs ).decode('utf-8')

   txt = '-----All-----\n' + txt + '\n-----New-----\n' + newTxt
   QMessageBox.information( st['ed'], 'Morphemes', txt )

util.addDoOnSelectionBtn( 'View morphemes', 'View morphemes', 'Viewing...', pre, per, post, shortcut='Ctrl+V' )
