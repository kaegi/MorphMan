#-*- coding: utf-8 -*-
from anki.hooks import addHook
from ..morphemes import getMorphemes, ms2str
from ..morphemizer import getMorphemizerByName
from ..util import addBrowserNoteSelectionCmd, getFilter, infoMsg, cfg1

def pre( b ): return { 'morphemes': [] }

def per( st, n ):
    notecfg = getFilter(n)
    if notecfg is None: return st
    morphemizer = getMorphemizerByName(notecfg['Morphemizer'])
    for f in notecfg['Fields']:
        ms = getMorphemes(morphemizer, n[f], n.tags, cfg1('ignore grammar position'))
        st['morphemes'] += ms
    return st

def post( st ):
    if len(st['morphemes']) == 0:
        infoMsg('----- No morphemes, check your filters -----')
        return
    s = ms2str( st['morphemes'] )
    infoMsg( '----- All -----\n' + s )

def runViewMorphemes():
    label = 'MorphMan: View Morphemes'
    tooltipMsg = 'View Morphemes for selected note'
    shortcut = cfg1('set view morphemes key')
    addBrowserNoteSelectionCmd( label, pre, per, post, tooltip=tooltipMsg, shortcut=(shortcut,) )

addHook( 'profileLoaded', runViewMorphemes )
