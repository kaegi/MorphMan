# -*- coding: utf-8 -*-
from aqt.utils import tooltip
from anki.hooks import addHook
from anki.utils import strip_html
from ..morphemes import getMorphemes, MorphDb
from ..morphemizer import getMorphemizerByName
from ..util import addBrowserNoteSelectionCmd, getFilter, infoMsg, QInputDialog, QFileDialog, QLineEdit, runOnce
from ..preferences import get_preference as cfg
from anki.lang import _


def pre(b):  # :: Browser -> State
    note_count = len(b.selectedNotes())
    tags, ok = QInputDialog.getText(b, 'Enter tags (e.x \"tag1 tag2\")', 'Tags', QLineEdit.Normal, 'hasMorph')
    if not ok or not tags:
        return

    path = QFileDialog.getOpenFileName(caption='Open db', directory=cfg('path_dbs'))[0]
    if not path:
        return
    if path.split('.')[-1] != "db":
        infoMsg('The selected file was not a db file')
        return  # per() and post() will still execute, but nothing happens

    db = MorphDb(path)
    return {'b': b, 'db': db, 'tags': str(tags), 'noteCount': note_count}


def per(st, n):  # :: State -> Note -> State

    note_cfg = getFilter(n)
    if note_cfg is None:
        return st
    morphemizer = getMorphemizerByName(note_cfg['Morphemizer'])
    for field in note_cfg['Fields']:
        for m in getMorphemes(morphemizer, strip_html(n[field]), n.tags):
            if m in st['db'].db:
                n.addTag(st['tags'])
                break
    n.flush()
    return st


def post(st):  # :: State -> State
    tooltip(_('Tagged {} notes containing morphemes in the selected db with "{}" '.format(st['noteCount'], st['tags'])))
    return st


@runOnce
def runBatchPlay():
    label = 'MorphMan: Mass Tagger'
    tooltip_msg = 'Tag all cards that contain morphemes from db'
    shortcut = cfg('set mass tagger key')
    addBrowserNoteSelectionCmd(label, pre, per, post, tooltip=tooltip_msg, shortcut=(shortcut,))


addHook('profileLoaded', runBatchPlay)
