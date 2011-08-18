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
    return { 'ed':ed, 'srcName':name, 'filePath':path, 'db':m.MorphDb(), 'mp':m.mecab(None) }

def per( st, f ):
    ms = m.getMorphemes( st['mp'], f[ 'Expression' ] )
    loc = m.AnkiDeck( f.id, 'Expression', st['ed'].deck.path, st['ed'].deck.name )
    st['db'].addMsL( ms, loc )
    return st

def post( st ):
    util.killMecab( st )
    st['db'].save( st['filePath'] )
    wantMerge = QMessageBox.question( st['ed'], 'Query', 'Would you like to merge with known db?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No )
    if wantMerge == QMessageBox.Yes:
        m.MorphDb.mergeFiles( st['filePath'], util.knownDbPath, util.knownDbPath )

util.addDoOnSelectionBtn( 'Export Morphemes', 'Morpheme export', 'Exporting...', pre, per, post )
