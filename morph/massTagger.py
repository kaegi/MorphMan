#-*- coding: utf-8 -*-
from morphemes import getMorphemes, MorphDb
from morphemizer import getMorphemizerForNote
from util import addBrowserSelectionCmd, cfg, cfg1, infoMsg, QInputDialog, QFileDialog, QLineEdit
import util

def pre( b ): # :: Browser -> State
    tags, ok = QInputDialog.getText( b, 'Enter tags', 'Tags', QLineEdit.Normal, 'hasMorph' )
    if not ok or not tags: return
    path = QFileDialog.getOpenFileName( caption='Open db', directory=util.dbsPath )
    if not path: return
    db = MorphDb( path )
    return { 'b':b, 'db':db, 'tags':unicode(tags) }

def per( st, n ): # :: State -> Note -> State
    #n.delTag( st['tags'] ) # clear tags if they already exist?

    for field in cfg( n.mid, None, 'morph_fields' ):
        for m in getMorphemes(getMorphemizerForNote(n), n[ field ]):
            if m in st['db'].db:
                n.addTag( st['tags'] )
                break
    n.flush()
    return st

def post( st ): # :: State -> State
    infoMsg( 'Tagged all notes containing morphemes in that db' )
    return st

addBrowserSelectionCmd( 'MorphMan: Mass Tagger', pre, per, post, tooltip='Tag all cards that contain morphemes from db', shortcut=None )
