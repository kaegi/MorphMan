#-*- coding: utf-8 -*-
from aqt.utils import tooltip
from anki.hooks import addHook
from anki.utils import stripHTML
from ..morphemes import getMorphemes, MorphDb
from ..morphemizer import getMorphemizerByName
from ..util import addBrowserNoteSelectionCmd, getFilter, infoMsg, QInputDialog, QFileDialog, QLineEdit, cfg1
from .. import util
from anki.lang import _

def pre( b ): # :: Browser -> State
    noteCount = len(b.selectedNotes())
    tags, ok = QInputDialog.getText( b, 'Enter tags (e.x \"tag1 tag2\")', 'Tags', QLineEdit.Normal, 'hasMorph' )
    if not ok or not tags: return

    path = QFileDialog.getOpenFileName( caption='Open db', directory=util.dbsPath )[0]
    if path == '': return
    if path.split('.')[-1] != "db":
        infoMsg('The selected file was not a db file')
        return # per() and post() will still execute, but nothing happens

    db = MorphDb( path )
    return { 'b':b, 'db':db, 'tags':str(tags), 'noteCount':noteCount }

def per( st, n ): # :: State -> Note -> State
    notecfg = getFilter(n)
    if notecfg is None: return st
    morphemizer = getMorphemizerByName(notecfg['Morphemizer'])
    for field in notecfg['Fields']:
        for m in getMorphemes(morphemizer, stripHTML(n[ field ]), n.tags):
            if m in st['db'].db:
                n.addTag(st['tags'])
                break
    n.flush()
    return st

def post( st ): # :: State -> State
    tooltip(_( 'Tagged {} notes containing morphemes in the selected db with "{}" '.format(st['noteCount'], st['tags']) ) )
    return st

def runBatchPlay():
    label = 'MorphMan: Mass Tagger'
    tooltipMsg = 'Tag all cards that contain morphemes from db'
    shortcut = cfg1('set mass tagger key')
    addBrowserNoteSelectionCmd( label, pre, per, post, tooltip=tooltipMsg, shortcut=(shortcut,) )

addHook( 'profileLoaded', runBatchPlay )
