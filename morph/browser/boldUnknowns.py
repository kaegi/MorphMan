# -*- coding: utf-8 -*-

from anki.hooks import addHook
from ..text_utils import bold_unknowns
from ..util import addBrowserNoteSelectionCmd, getFilterByMidAndTags, runOnce
from ..preferences import get_preference as cfg

def pre(b): return {'morphemes': []}


def per(st, n):
    mid = n.model()['id']
    tags = n.tags

    notecfg = getFilterByMidAndTags(mid, tags)
    if notecfg is None:
        return

    changed = False

    for f in notecfg['Fields']:
        before = n[f]
        n[f] = bold_unknowns(mid, before, tags)
        changed = changed or (before != n[f])

    if changed:
        n.flush()

    return st


def post(st):
    pass

@runOnce
def runBoldUnknowns():
    label = 'MorphMan: Bold Unnown Morphemes'
    tooltipMsg = 'Bold Unnown Morpheme on selected notes'
    shortcut = cfg('set bold unknowns key')
    addBrowserNoteSelectionCmd(label, pre, per, post, tooltip=tooltipMsg, shortcut=(shortcut,))


addHook('profileLoaded', runBoldUnknowns)
