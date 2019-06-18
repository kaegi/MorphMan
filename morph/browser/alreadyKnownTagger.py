#-*- coding: utf-8 -*-
from aqt.utils import tooltip
from ..util import addBrowserNoteSelectionCmd, getFilter, jcfg
from .. import util

def pre( b ): # :: Browser -> State
    return { 'tag':jcfg('Tag_AlreadyKnown') }

def per( st, n ): # :: State -> Note -> State
    #n.delTag( st['tags'] ) # clear tags if they already exist?

    notecfg = getFilter(n)
    if notecfg is None: return st
    n.addTag(st['tag'])
    n.flush()
    return st

def post( st ): # :: State -> State
    tooltip( _( 'Selected notes given the %s tag' % st['tag'] ) )
    return st

addBrowserNoteSelectionCmd( 'MorphMan: Already Known Tagger', pre, per, post, tooltip='Tag all selected cards as already known', shortcut=('K',) )
