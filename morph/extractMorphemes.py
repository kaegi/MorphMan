#-*- coding: utf-8 -*-
import os

from morphemes import AnkiDeck, MorphDb, getMorphemes2, getMorphemizorForNote, ms2str
from util import addBrowserSelectionCmd, cfg, cfg1, mw, infoMsg, QFileDialog

def pre( b ):
    from util import dbsPath # not defined until late, so don't import at top of module
    path = QFileDialog.getSaveFileName( caption='Save morpheme db to?', directory=dbsPath + os.sep + 'exportedMorphs.db' )
    if not path: return
    return { 'dbpath':str(path), 'morphDb':MorphDb() }

def per( st, n ):
    mats = mw.col.db.list( 'select ivl from cards where nid = :nid', nid=n.id )
    for f in cfg( n.mid, None, 'morph_fields' ):
        ms = getMorphemes2(getMorphemizorForNote(n), n[ f ], None, cfg1('morph_blacklist') )
        loc = AnkiDeck( n.id, f, n[ f ], n.guid, mats )
        st['morphDb'].addMsL( ms, loc )
    return st

def post( st ):
    st['morphDb'].save( st['dbpath'] )
    infoMsg( 'DB saved with extracted morphemes' )

addBrowserSelectionCmd( 'Extract Morphemes', pre, per, post, tooltip='Extract morphemes in selected notes to a MorphMan db', shortcut=('Ctrl+Shift+E',) )
