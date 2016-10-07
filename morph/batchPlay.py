#-*- coding: utf-8 -*-
from util import addBrowserSelectionCmd, cfg, cfg1
import anki.sound
import re

def pre( b ): return { 'vid2nid':{} }

def per( st, n ):
    for f in cfg( n.mid, None, 'batch media fields' ):
        try:
            r = re.search( anki.sound._soundReg, n[ f ] )
            if r:
                st['vid2nid'][ r.group(1) ] = n.id
                break
        except KeyError: pass
    return st

def post( st ):
    #TODO: queue all the files in a big list with `loadfile {filename} 1` so you can skip back and forth easily
    # when user chooses, use `get_file_name`
    for vid, nid in st['vid2nid'].iteritems():
        anki.sound.play( vid )
    st['__reset'] = False
    return st

addBrowserSelectionCmd( 'Batch Play', pre, per, post, tooltip='Play all the videos for the selected cards', shortcut=('Ctrl+Alt+P',) )
