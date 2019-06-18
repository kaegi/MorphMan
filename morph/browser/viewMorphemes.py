#-*- coding: utf-8 -*-
from ..morphemes import getMorphemes, ms2str
from ..morphemizer import getMorphemizerByName
from ..util import addBrowserNoteSelectionCmd, getFilter, infoMsg

def pre( b ): return { 'morphemes': [] }

def per( st, n ):
    notecfg = getFilter(n)
    if notecfg is None: return st
    morphemizer = getMorphemizerByName(notecfg['Morphemizer'])
    for f in notecfg['Fields']:
        ms = getMorphemes(morphemizer, n[f], n.tags)
        st['morphemes'] += ms
    return st

def post( st ):
    if len(st['morphemes']) == 0:
        infoMsg('----- No morphemes, check your filters -----')
        return
    s = ms2str( st['morphemes'] )
    infoMsg( '----- All -----\n' + s )

addBrowserNoteSelectionCmd( 'MorphMan: View Morphemes', pre, per, post, tooltip='View Morphemes for selected note', shortcut=('Ctrl+Shift+V',) )
