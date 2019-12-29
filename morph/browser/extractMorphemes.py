# -*- coding: utf-8 -*-
import os
from anki.hooks import addHook
from anki.utils import stripHTML
from ..morphemes import AnkiDeck, MorphDb, getMorphemes, ms2str
from ..morphemizer import getMorphemizerByName
from ..util import addBrowserNoteSelectionCmd, mw, getFilter, infoMsg, QFileDialog
from ..preferences import get_preference as cfg


def pre(b):
    dir_path = cfg('path_dbs') + os.sep + 'exportedMorphs.db'
    path = QFileDialog.getSaveFileName(caption='Save morpheme db to:', directory=dir_path)[0]

    return {'dbpath': str(path), 'morphDb': MorphDb()} if path else None


def per(st, n):
    mats = mw.col.db.list('select ivl from cards where nid = :nid', nid=n.id)
    note_cfg = getFilter(n)
    if note_cfg is None:
        return st

    morphemizer = getMorphemizerByName(note_cfg['Morphemizer'])
    for f in note_cfg['Fields']:
        ms = getMorphemes(morphemizer, stripHTML(n[f]), n.tags)
        loc = AnkiDeck(n.id, f, n[f], n.guid, mats)
        st['morphDb'].addMsL(ms, loc)

    return st


def post(st):
    st['morphDb'].save(st['dbpath'])
    infoMsg('DB saved with extracted morphemes')


def runExtractMorphemes():
    label = 'MorphMan: Extract Morphemes'
    tooltip_msg = 'Extract morphemes in selected notes to a MorphMan db'
    shortcut = cfg('set extract morphemes key')
    addBrowserNoteSelectionCmd(label, pre, per, post, tooltip=tooltip_msg, shortcut=(shortcut,))


addHook('profileLoaded', runExtractMorphemes)
