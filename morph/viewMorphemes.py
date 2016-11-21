#-*- coding: utf-8 -*-
from morphemes import getMorphemes, ms2str
from morphemizer import getMorphemizerForFilter
from util import addBrowserSelectionCmd, cfg, cfg1, getFilter, infoMsg

def pre( b ): return { 'txt':'', 'morphemizer': None }

def per( st, n ):
    notecfg = getFilter(n)
    if notecfg is None: return st
    st['morphemizer'] = getMorphemizerForFilter(notecfg)
    for f in notecfg['Fields']:
        st['txt'] += n[ f ] + '  '
    return st

def post( st ):
    if st['txt'] == '':
        infoMsg('----- No morphemes, check your filters -----')
        return
    ms = getMorphemes(st['morphemizer'], st['txt'])
    s = ms2str( ms )
    infoMsg( '----- All -----\n' + s )

addBrowserSelectionCmd( 'MorphMan: View Morphemes', pre, per, post, tooltip='View Morphemes for selected note', shortcut=('Ctrl+Shift+V',) )
