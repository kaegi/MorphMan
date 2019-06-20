#-*- coding: utf-8 -*-
from aqt.utils import tooltip
from aqt import browser
from ..util import addBrowserCardSelectionCmd, mw, infoMsg

def pre( b ): return { 'cards':[], 'browser':b }

def per( st, c ):
    st['cards'].append( c )
    return st

def post( st ):
    for c in st['cards']:
        mw.reviewer.cardQueue.append( c )
    st['browser'].close()
    infoMsg("") # Prevents an AttributeError directly above
    tooltip( _( 'Immediately reviewing {} cards'.format(len(st['cards'])) ) )
    return st

addBrowserCardSelectionCmd( 'MorphMan: Learn Now', pre, per, post, tooltip='Immediately review the selected new cards', shortcut=None )
