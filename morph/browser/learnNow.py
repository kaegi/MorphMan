#-*- coding: utf-8 -*-
from aqt.utils import tooltip
from anki.hooks import addHook
from aqt import browser
from ..util import addBrowserCardSelectionCmd, mw, infoMsg, cfg1
from anki.lang import _

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

def runLearnNow():
    label = 'MorphMan: Learn Now'
    tooltipMsg = 'Immediately review the selected new cards'
    shortcut = cfg1('set learn now key')
    addBrowserCardSelectionCmd( label, pre, per, post, tooltip=tooltipMsg, shortcut=(shortcut,) )

addHook( 'profileLoaded', runLearnNow )
