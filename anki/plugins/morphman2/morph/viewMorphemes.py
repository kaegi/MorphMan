from PyQt4.QtCore import *
from PyQt4.QtGui import *

import morphemes as M
import util

def pre( ed ):
   if not util.requireKnownDb(): return 'BAIL'
   bs = util.getBlacklist( ed )
   return { 'ed':ed, 'txt':'', 'bs':bs, 'mp':M.mecab() }

def per( st, f ):
   st['txt'] += f['Expression']
   return st

def post( st ):
   ms = M.getMorphemes( st['mp'], st['txt'], bs=st['bs'] )
   util.killMecab( st )
   txt = M.ms2str( ms )

   kdb = M.MorphDb( util.knownDbPath )
   newMs = [ m for m in ms if m not in kdb.db ]
   newTxt = M.ms2str( newMs )

   txt = '-----All-----\n' + txt + '\n-----New-----\n' + newTxt
   QMessageBox.information( st['ed'], 'Morphemes', txt )

util.addDoOnSelectionBtn( 'View morphemes', 'View morphemes', 'Viewing...', pre, per, post, shortcut='Ctrl+V' )
