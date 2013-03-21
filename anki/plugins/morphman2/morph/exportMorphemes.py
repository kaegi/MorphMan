from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.utils import ids2str
from anki.cards import Card

import morphemes as M
import util

def getCards( deck, fids ):
    cis = deck.s.column0( 'select id from cards where factId in %s' % ids2str(fids) )
    cs = [ deck.s.query(Card).get( id ) for id in cis ]
    return cs

def pre( ed ):
    field, ok = QInputDialog.getText( ed, 'Enter name of field to extract from', 'Field Name', QLineEdit.Normal, 'Expression' )
    if not ok: return 'BAIL'
    defPath = util.dbPath + 'mySelection.db'
    path = QFileDialog.getSaveFileName( caption='Save morpheme db to?', directory=defPath )
    if not path: return 'BAIL'
    return { 'ed':ed, 'fieldName':field, 'filePath':str(path), 'db':M.MorphDb(), 'mp':M.mecab() }

def per( st, f ):
    d, fname = st['ed'].deck, st['fieldName']
    mats = [ c.interval for c in getCards( d, [f.id] ) ]
    ms = M.getMorphemes( st['mp'], f[ fname ] )
    loc = M.AnkiDeck( f.id, fname, f[ fname ], d.path, d.name(), mats )
    st['db'].addMsL( ms, loc )
    return st

def post( st ):
    util.killMecab( st )
    st['db'].save( st['filePath'] )
    wantMerge = QMessageBox.question( st['ed'], 'Query', 'Would you like to merge with known db?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No )
    if wantMerge == QMessageBox.Yes:
        M.MorphDb.mergeFiles( st['filePath'], util.knownDbPath, util.knownDbPath )

util.addDoOnSelectionBtn( 'Export Morphemes', 'Morpheme export', 'Exporting...', pre, per, post )
