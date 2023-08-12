# -*- coding: utf-8 -*-
from aqt.utils import tooltip
from anki.hooks import addHook
from ..util import addBrowserNoteSelectionCmd, get_filter, runOnce
from ..preferences import get_preference
from anki.lang import _


def pre(b):  # :: Browser -> State
    noteTotal = len(b.selectedNotes())
    return {'tag': get_preference('Tag_AlreadyKnown'), 'noteTotal': noteTotal}


def per(st, n):  # :: State -> Note -> State
    if get_filter(n) is None:
        return st

    n.addTag(st['tag'])
    n.flush()
    return st


def post(st):  # :: State -> State
    tooltip(_('{} notes given the {} tag'.format(st['noteTotal'], st['tag'])))
    return st


@runOnce
def runAlreadyKnownTagger():
    label = 'MorphMan: Already Known Tagger'
    tooltipMsg = 'Tag all selected cards as already known'
    shortcut = get_preference('set known and skip key')  # type: str
    addBrowserNoteSelectionCmd(label, pre, per, post, tooltip=tooltipMsg, shortcut=(shortcut,))


addHook('profileLoaded', runAlreadyKnownTagger)
