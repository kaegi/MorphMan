# -*- coding: utf-8 -*-
from anki.hooks import addHook
from anki.utils import strip_html
from ..morphemes import getMorphemes, ms2str
from ..morphemizer import getMorphemizerByName
from ..util import addBrowserNoteSelectionCmd, get_filter, infoMsg, runOnce
from ..preferences import get_preference as cfg


def pre(b): return {'morphemes': []}


def per(st, n):
    notecfg = get_filter(n)
    if notecfg is None:
        return st

    morphemizer = getMorphemizerByName(notecfg['Morphemizer'])
    for f in notecfg['Fields']:
        ms = getMorphemes(morphemizer, strip_html(n[f]), n.tags)
        st['morphemes'] += ms
    return st


def post(st):
    if len(st['morphemes']) == 0:
        infoMsg('----- No morphemes, check your filters -----')
        return
    s = ms2str([(m, []) for m in st['morphemes']])
    infoMsg('----- All -----\n' + s)


@runOnce
def runViewMorphemes():
    label = 'MorphMan: View Morphemes'
    tooltipMsg = 'View Morphemes for selected note'
    shortcut = cfg('set view morphemes key')
    addBrowserNoteSelectionCmd(label, pre, per, post, tooltip=tooltipMsg, shortcut=(shortcut,))


addHook('profileLoaded', runViewMorphemes)
