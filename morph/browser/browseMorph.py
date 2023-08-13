# -*- coding: utf-8 -*-
from anki.hooks import addHook
from anki.lang import _
from aqt.utils import tooltip

from ..reviewing_utils import try_to_get_focus_morphs, focus_query
from ..util import addBrowserNoteSelectionCmd, runOnce
from ..preferences import get_preference as cfg


def pre(b): return {'focusMorphs': set(), 'b': b}


def per(st, n):
    if n is None:
        return st

    for focusMorph in try_to_get_focus_morphs(n):  # TODO: is this safe??
        st['focusMorphs'].add(focusMorph)
    return st


def post(st):
    search = ''
    focusField = cfg('Field_FocusMorph')
    focusMorphs = st['focusMorphs']
    
    q = focus_query(focusField, focusMorphs)
    if q != '':
        st['b'].form.searchEdit.lineEdit().setText(q)
        st['b'].onSearchActivated()
        tooltip(_('Browsing {} morphs'.format(len(focusMorphs))))
    return st


@runOnce
def runBrowseMorph():
    label = 'MorphMan: Browse Morphs'
    tooltipMsg = 'Browse all notes containing the morphs from selected notes'
    shortcut = cfg('browse same focus key')
    addBrowserNoteSelectionCmd(label, pre, per, post, tooltip=tooltipMsg, shortcut=(shortcut,))


addHook('profileLoaded', runBrowseMorph)
