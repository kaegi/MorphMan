#-*- coding: utf-8 -*-
from morphemes import getMorphemes, ms2str, MorphDb
from util import addBrowserSelectionCmd, cfg, cfg1, infoMsg, QInputDialog, QFileDialog, QLineEdit
import util

def pre( b ):
    tags, ok = QInputDialog.getText( b, 'Enter tags', 'Tags', QLineEdit.Normal, 'hasMorph' )
    if not ok or not tags: return
    path = QFileDialog.getOpenFileName( caption='Open db', directory=util.dbsPath )
    if not path: return
    db = MorphDb( path )
    return { 'b':b, 'db':db, 'tags':unicode(tags) }

def per( st, n ):
    n.delTag( st['tags'] )

    if n['k+N'] == '1': # FIXME this special but commonly wanted logic must be a cfg option
        ms = getMorphemes( n['focusMorph'], None, cfg1('morph_blacklist') )
        for m in ms:
            if m in st['db'].db:
                n.addTag( st['tags'] )
                break

    n.flush()
    return st

def post( st ):
    return st

addBrowserSelectionCmd( 'Mass Tagger', pre, per, post, tooltip='Tag all cards that contain morphemes from db', shortcut=None )
