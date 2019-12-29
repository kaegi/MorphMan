# -*- coding: utf-8 -*-
from anki.hooks import addHook
from anki.utils import stripHTML
from ..morphemes import getMorphemes, ms2str
from ..morphemizer import getMorphemizerByName
from ..util import addBrowserNoteSelectionCmd, getFilter, infoMsg
from ..preferences import get_preference as cfg


def pre(b): return {'morphemes': []}


def per(st, n):
    notecfg = getFilter(n)
    if notecfg is None:
        return st

    morphemizer = getMorphemizerByName(notecfg['Morphemizer'])
    for f in notecfg['Fields']:
        ms = getMorphemes(morphemizer, stripHTML(n[f]), n.tags)
        st['morphemes'] += ms
    return st


def post(st):
    if len(st['morphemes']) == 0:
        infoMsg('----- No morphemes, check your filters -----')
        return
    s = ms2str([(m, []) for m in st['morphemes']])
    infoMsg('----- All -----\n' + s)


def runViewMorphemes():
    label = 'MorphMan: View Morphemes'
    tooltipMsg = 'View Morphemes for selected note'
    shortcut = cfg('set view morphemes key')
    addBrowserNoteSelectionCmd(label, pre, per, post, tooltip=tooltipMsg, shortcut=(shortcut,))


addHook('profileLoaded', runViewMorphemes)
