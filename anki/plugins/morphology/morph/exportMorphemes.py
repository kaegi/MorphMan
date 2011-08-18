from PyQt4.QtCore import *
from PyQt4.QtGui import *

import morphemes as m
import util

def pre( ed ):
    name, ok = QInputDialog.getText( ed, 'Enter name of source', 'Name', QLineEdit.Normal, 'recentSelection' )
    if not ok: return 'BAIL'
    defPath = util.dbPath + name + '.db'
    path = QFileDialog.getSaveFileName( caption='Save morpheme db to?', directory=defPath )
    if not path: return 'BAIL'
    return { 'ed':ed, 'srcName':name, 'filePath':path, 'ms':[], 'mp':m.mecab(None) }

def per( st, f ):
   st['ms'].extend( m.getMorphemes( st['mp'], f[ 'Expression' ] ) )
   return st

def post( st ):
   util.killMecab( st )
   m.saveDb( m.ms2db( st['ms'], srcName=st['srcName'] ), st['filePath'] )
   wantMerge = QMessageBox.question( st['ed'], 'Query', 'Would you like to merge with known db?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No )
   if wantMerge == QMessageBox.Yes:
      m.mergeFiles( st['filePath'], util.knownDbPath, util.knownDbPath )

util.addDoOnSelectionBtn( 'Export Morphemes', 'Morpheme export', 'Exporting...', pre, per, post )
