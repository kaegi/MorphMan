# -*- coding: utf-8 -*-
from anki.hooks import addHook
from anki.lang import _
from aqt.utils import tooltip

from ..newMorphHelper import focus, focusName
from ..util import addBrowserNoteSelectionCmd, cfg1


def pre(b): return {'focusMorph': [], 'b': b}


def per(st, n):
    if n is None:
        return st

    focusMorph = focus(n)
    if focusMorph not in st['focusMorph']:  # If a unique focus morph to search for
        st['focusMorph'].append(focusMorph)
    return st


def post(st):
    search = ''
    focusField = focusName()
    focusArray = st['focusMorph']
    for f in focusArray:
        if f == focusArray[-1]:  # If last morph in array, don't add "or"
            search += '{}:{}'.format(focusField, f)
        else:
            search += '{}:{} or '.format(focusField, f)

    if search != '':
        st['b'].form.searchEdit.lineEdit().setText(search)
        st['b'].onSearchActivated()
        tooltip(_('Browsing {} morphs'.format(len(st['focusMorph']))))
    return st


def runBrowseMorph():
    label = 'MorphMan: Browse Morphs'
    tooltipMsg = 'Browse all notes containing the morphs from selected notes'
    shortcut = cfg1('browse same focus key')
    addBrowserNoteSelectionCmd(label, pre, per, post, tooltip=tooltipMsg, shortcut=(shortcut,))


addHook('profileLoaded', runBrowseMorph)
