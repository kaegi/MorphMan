# -*- coding: utf-8 -*-
import re

from anki.hooks import addHook
from anki.utils import stripHTML
from ..morphemes import getMorphemes
from ..morphemizer import getMorphemizerByName
from ..util import addBrowserNoteSelectionCmd, getFilter, allDb
from ..preferences import get_preference as cfg

def nonSpanSub(sub, repl, string):
    return ''.join(re.sub(sub, repl, s, flags=re.IGNORECASE) if not s.startswith('<span') else s for s in
                    re.split('(<span.*?</span>)', string))

def pre(b): return {'morphemes': []}


def per(st, n):
    notecfg = getFilter(n)
    if notecfg is None:
        return

    changed = False
    proper_nouns_known = cfg('Option_ProperNounsAlreadyKnown')

    morphemizer = getMorphemizerByName(notecfg['Morphemizer'])
    for f in notecfg['Fields']:
        ms = getMorphemes(morphemizer, stripHTML(n[f]), n.tags)

        for m in sorted(ms, key=lambda x: len(x.inflected), reverse=True):  # largest subs first
            locs = allDb().getMatchingLocs(m)
            mat = max(loc.maturity for loc in locs) if locs else 0

            if (proper_nouns_known and m.isProperNoun()) or (mat >= cfg('threshold_known')):
                continue
            
            n[f] = nonSpanSub('(%s)' % m.inflected, '<b>\\1</b>', n[f])
            changed = True
    if changed:
        n.flush()

    return st


def post(st):
    pass

def runBoldUnknowns():
    label = 'MorphMan: Bold Unnown Morphemes'
    tooltipMsg = 'Bold Unnown Morpheme on selected note'
    addBrowserNoteSelectionCmd(label, pre, per, post, tooltip=tooltipMsg)


addHook('profileLoaded', runBoldUnknowns)
