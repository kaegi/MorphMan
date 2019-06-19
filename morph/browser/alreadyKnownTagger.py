#-*- coding: utf-8 -*-
from aqt.utils import tooltip
from ..util import addBrowserNoteSelectionCmd, getFilter, jcfg
from .. import util

def pre( b ): # :: Browser -> State
    noteTotal = len(b.selectedNotes())
    return { 'tag':jcfg('Tag_AlreadyKnown'), 'noteTotal':noteTotal }

def per( st, n ): # :: State -> Note -> State
    notecfg = getFilter(n)
    if notecfg is None: return st
    n.addTag(st['tag'])
    n.flush()
    return st

def post( st ): # :: State -> State
    tooltip( _( '{} notes given the {} tag'.format(st['noteTotal'], st['tag']) ) )
    return st

addBrowserNoteSelectionCmd( 'MorphMan: Already Known Tagger', pre, per, post, tooltip='Tag all selected cards as already known', shortcut=("K",) )
