#-*- coding: utf-8 -*-
from aqt import reviewer, dialogs
from aqt.qt import *
from util import addBrowserSelectionCmd, cfg, cfg1, wrap, tooltip, mw, addHook
from util import infoMsg, printf
import util

#1 after answering -> skip all cards with same focus as one just answered
#2 hotkey -> set card as already known, skip it, and all others with same focus
#3 hotkey -> search for all cards with same focus (in browser)
#4 in browser -> immediately learn selected cards
#5 on show -> highlight morphemes within expression according to how well known

# config aliases
def CN( n, key ):   return    cfg( n.mid, None, key )
def focusName( n ): return    cfg( n.mid, None, 'focusMorph' )
def focus( n ):     return n[ cfg( n.mid, None, 'focusMorph' ) ]

def buryNotesWithSameFocus( self, n, alsoBurySelf=True ):
    '''Bury all notes that have the same focus morph as the provided note. Requires mw.reset afterwards.
    Useful when studying a new morph and wanting to avoid dupes without doing morph man recalc.
    '''
    try:
        if not focus( n ): return
        q = u'%s:%s' % ( focusName( n ), focus( n ) )
    except KeyError: return
    nids = self.mw.col.findNotes( q )

    for nid in nids:
        if alsoBurySelf or nid != n.id:
            self.mw.col.sched.buryNote( nid )
    self.mw.col.sched._resetLrn()
    tooltip( _( 'Buried %d notes with same focus morph' % (len(nids)-1) ) )

def setKnownAndSkip( self ): #2
    '''Set card as alreadyKnown and skip along with all other cards with same focusMorph.
    Useful if you see a focusMorph you already know from external knowledge'''
    self.mw.checkpoint( _("Set already known focus morph") )
    n = self.card.note()
    n.addTag( CN( n, 'tag_alreadyKnown' ) )
    n.flush()
    buryNotesWithSameFocus( self, n )
    self.nextCard()

def browseSameFocus( self ): #3
    '''Opens browser and displays all notes with the same focus morph.
    Useful to quickly find alternative notes to learn focus from'''
    try:
        n = self.card.note()
        if not focus( n ): return
        q = u'%s:%s' % ( focusName( n ), focus( n ) )
        b = dialogs.open( 'Browser', self.mw )
        b.form.searchEdit.lineEdit().setText( q )
        b.onSearch()
    except KeyError: pass

def my_reviewer_keyHandler( self, evt ):
    key = unicode( evt.text() )
    if   key == 'k':    setKnownAndSkip( self )
    elif key == 'l':    browseSameFocus( self )

def my_reviewer_answerCard( self, ease ): #1
    if self.mw.state != "review" or self.state != "answer" or self.mw.col.sched.answerButtons( self.card ) < ease: return
    buryNotesWithSameFocus( self, self.card.note(), False )

reviewer.Reviewer._keyHandler = wrap( reviewer.Reviewer._keyHandler, my_reviewer_keyHandler )
reviewer.Reviewer._answerCard = wrap( reviewer.Reviewer._answerCard, my_reviewer_answerCard, "before" )

#4
def pre( b ): return { 'notes':[], 'browser':b }
def per( st, n ):
    st['notes'].append( n )
    return st
def post( st ):
    i = 0
    for n in st['notes']:
        for c in n.cards():
            mw.reviewer.cardQueue.append( c )
            i += 1
    st['browser'].close()
    tooltip( _( 'Immediately reviewing %d cards' % i ) )

addBrowserSelectionCmd( 'Learn Now', pre, per, post, tooltip='Immediately review the selected new cards', shortcut=('Ctrl+Shift+N',) )

#5
import re
def highlight( txt, extra, fieldDict, field, mod_field ):
    # must avoid formatting a smaller morph that is contain in a bigger morph
    # => do largest subs first and don't sub anything already in <span>
    def nonSpanSub( sub, repl, string ):
        return u''.join( re.sub( sub, repl, s ) if not s.startswith('<span') else s for s in re.split( '(<span.*?</span>)', string ) )
    from morphemes import getMorphemes
    ms = getMorphemes( txt )
    for m in sorted( ms, key=lambda x: len(x.inflected), reverse=True ): # largest subs first
        locs = util.allDb().db.get( m, set() )
        mat = max( getattr( loc, 'maturity', cfg1('threshold_mature') ) for loc in locs ) if locs else 0

        if mat >= cfg1( 'threshold_mature' ):    mtype = 'mature'
        elif mat >= cfg1( 'threshold_known' ):   mtype = 'known'
        elif mat >= cfg1( 'threshold_seen' ):    mtype = 'seen'
        else:                                   mtype = 'unknown'
        repl = u'<span class="morphHighlight" mtype="{mtype}" mat="{mat}">{morph}</span>'.format(
                morph = m.inflected,
                mtype = mtype,
                mat = mat
                )
        txt = nonSpanSub( m.inflected, repl, txt )
    return txt
addHook( 'fmod_morphHighlight', highlight )
