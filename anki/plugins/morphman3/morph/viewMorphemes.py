#-*- coding: utf-8 -*-
from morphemes import getMorphemes, ms2str
from util import addBrowserSelectionCmd, cfg, cfg1, infoMsg

def pre( b ): return { 'txt':'' }

def per( st, n ):
    for f in cfg( n.mid, None, 'morph_fields' ):
        st['txt'] += n[ f ] + '  '
    return st

def post( st ):
    ms = getMorphemes( st['txt'], None, cfg1('morph_blacklist') )
    s = ms2str( ms )
    infoMsg( '----- All -----\n' + s )

addBrowserSelectionCmd( 'View Morphemes', pre, per, post, tooltip='View Morphemes for selected note', shortcut=('Ctrl+Shift+V',) )
