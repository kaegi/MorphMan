#-*- coding: utf-8 -*-
from aqt import reviewer, dialogs
from aqt.qt import *
from anki import sched
from util import addBrowserSelectionCmd, jcfg, cfg, cfg1, wrap, tooltip, mw, addHook, allDb, partial

# only for jedi-auto-completion
import aqt.main
assert isinstance(mw, aqt.main.AnkiQt)

import main

#1 after answering -> skip all cards with same focus as one just answered
#2 hotkey -> set card as already known, skip it, and all others with same focus
#3 hotkey -> search for all cards with same focus (in browser)
#4 in browser -> immediately learn selected cards
#5 on show -> highlight morphemes within expression according to how well known
#6 on fill -> pull new cards from all child decks at once instead of sequentially

# config aliases
def CN( n, key ):   return    cfg( n.mid, None, key )
def focusName( n ): return    jcfg('Field_FocusMorph') # TODO remove argument n
def focus( n ):     return n[ focusName(n) ]


########## 6 parent deck pulls new cards from all children instead of sequentially (ie. mostly first)
def my_fillNew( self, _old ):
    '''If 'new card merged fill' is enabled for the current deck, when we refill we
    pull from all child decks, sort combined pool of cards, then limit.
    If disabled, do the standard sequential fill method'''
    C = partial( cfg, None, self.col.decks.active()[0] )
    if not C('new card merged fill'): return _old( self )

    if self._newQueue:      return True
    if not self.newCount:   return False

    self._newQueue = self.col.db.all('''select id, due from cards where did in %s and queue = 0 and due >= ? order by due limit ?''' % self._deckLimit(), C('new card merged fill min due'), self.queueLimit )
    if self._newQueue:      return True

sched.Scheduler._fillNew = wrap( sched.Scheduler._fillNew, my_fillNew, 'around' )

########## handle skipping for 1-2
seenMorphs = set()

def markFocusSeen( self, n ):
    '''Mark a focusMorph as already seen so future new cards with the same focus
    will be skipped. Also prints number of cards to be skipped if enabled'''
    global seenMorphs
    try:
        if not focus( n ): return
        q = u'%s:%s' % ( focusName( n ), focus( n ) )
    except KeyError: return
    seenMorphs.add( focus(n) )
    numSkipped = len( self.mw.col.findNotes( q ) ) -1
    if numSkipped and cfg1('print number of alternatives skipped'):
        tooltip( _( '%d alternatives will be skipped' % numSkipped ) )

def my_getNewCard( self, _old ):
    '''Continually call _getNewCard until we get one with a focusMorph we haven't
    seen before. Also skip bad vocab cards.

    :type self: anki.sched.Scheduler
    :type _old: Callable
    '''

    while True:
        C = partial( cfg, None, self.col.decks.active()[0] )
        if not C('next new card feature'):
            return _old( self )
        if not C('new card merged fill'):
            c = _old( self )
            ''' :type c: anki.cards.Card '''
        else:   # pop from opposite direction and skip sibling spacing
            if not self._fillNew(): return
            ( id, due ) = self._newQueue.pop( 0 )
            c = self.col.getCard( id )
            self.newCount -= 1

        if not c: return			# no more cards
        n = c.note()

        try: fm = focus( n )		# fm is either the focusMorph or empty
        except KeyError: return c	# card has no focusMorph field -> assume it's good

        # determine if good vocab word based on whether k+1
        # defaults to whether has focus morph if no k+N field or disabled
        try: goodVocab = n[ jcfg('Field_UnknownMorphCount') ] == '1'
        except KeyError: goodVocab = fm

        # even if it is not a good vocabulary card, we have no choice when there are no other cards available
        if (not goodVocab and not n.hasTag(jcfg('Tag_NotReady'))) or n.hasTag( jcfg('Tag_AlreadyKnown') ) or fm in seenMorphs:
            self.buryCards( [ c.id ] )
            self.newCount += 1 # the card was quaried from the "new queue" so we have to increase the "new counter" back to its original value
            continue
        break

    return c

sched.Scheduler._getNewCard = wrap( sched.Scheduler._getNewCard, my_getNewCard, 'around' )

########## 1 - after learning a new focus morph, don't learn new cards with the same focus
def my_reviewer_answerCard( self, ease ): #1
    ''' :type self: aqt.reviewer.Reviewer '''
    if self.mw.state != "review" or self.state != "answer" or self.mw.col.sched.answerButtons( self.card ) < ease: return
    if CN(self.card.note(), 'auto skip alternatives'):
        markFocusSeen( self, self.card.note() )

reviewer.Reviewer._answerCard = wrap( reviewer.Reviewer._answerCard, my_reviewer_answerCard, "before" )

########## 2 - set current card's focus morph as already known and skip alternatives
def setKnownAndSkip( self ): #2
    '''Set card as alreadyKnown and skip along with all other cards with same focusMorph.
    Useful if you see a focusMorph you already know from external knowledge

    :type self: aqt.reviewer.Reviewer '''
    self.mw.checkpoint( _("Set already known focus morph") )
    n = self.card.note()
    n.addTag(jcfg('Tag_AlreadyKnown'))
    n.flush()
    markFocusSeen( self, n )

    # "new counter" might have been decreased (but "new card" was not answered
    # so it shouldn't) -> this function recomputes "new counter"
    self.mw.col.reset()

    # skip card
    self.nextCard()

########## 3 - search in browser for cards with same focus
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

########## set keybindings for 2-3
def my_reviewer_keyHandler( self, evt ):
    ''' :type self: aqt.reviewer.Reviewer '''
    key = unicode( evt.text() )
    key_browse, key_skip = cfg1('browse same focus key'), cfg1('set known and skip key')
    if   key == key_skip:   setKnownAndSkip( self )
    elif key == key_browse: browseSameFocus( self )

reviewer.Reviewer._keyHandler = wrap( reviewer.Reviewer._keyHandler, my_reviewer_keyHandler )

########## 4 - immediately review selected cards
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
    st['__reset'] = False
    tooltip( _( 'Immediately reviewing %d cards' % i ) )

addBrowserSelectionCmd( 'MorphMan: Learn Now', pre, per, post, tooltip='Immediately review the selected new cards', shortcut=('Ctrl+Shift+N',) )

########## 5 - highlight morphemes using morphHighlight
import re

def isNoteSame(note, fieldDict):
    # compare fields
    same_as_note = True
    items = note.items()
    for (key, value) in items:
        if key not in fieldDict or value != fieldDict[key]:
            return False

    # compare tags
    argTags = mw.col.tags.split(fieldDict['Tags'])
    noteTags = note.tags
    return set(argTags) == set(noteTags)


def highlight( txt, extra, fieldDict, field, mod_field ):
    '''When a field is marked with the 'focusMorph' command, we format it by
    wrapping all the morphemes in <span>s with attributes set to its maturity'''
    # must avoid formatting a smaller morph that is contained in a bigger morph
    # => do largest subs first and don't sub anything already in <span>
    def nonSpanSub( sub, repl, string ):
        return u''.join( re.sub( sub, repl, s ) if not s.startswith('<span') else s for s in re.split( '(<span.*?</span>)', string ) )

    # find morphemizer; because no note/card information is exposed through arguments, we have to find morphemizer based on tags alone
    #from aqt.qt import debug; debug()
    #
    #if mw.reviewer.card is None: return txt
    #note = mw.reviewer.card.note()
    #if not isNoteSame(note, fieldDict): return txt
    #from aqt.qt import debug; debug()

    from morphemes import getMorphemes
    from morphemizer import getMorphemizerForTagsAndType
    morphemizer = getMorphemizerForTagsAndType(fieldDict['Type'], fieldDict['Tags'].split())
    if morphemizer is None: return txt
    ms = getMorphemes(morphemizer, txt )

    for m in sorted( ms, key=lambda x: len(x.inflected), reverse=True ): # largest subs first
        locs = allDb().db.get( m, set() )
        mat = max( loc.maturity for loc in locs ) if locs else 0

        if   mat >= cfg1( 'threshold_mature' ):  mtype = 'mature'
        elif mat >= cfg1( 'threshold_known' ):   mtype = 'known'
        elif mat >= cfg1( 'threshold_seen' ):    mtype = 'seen'
        else:                                    mtype = 'unknown'
        repl = u'<span class="morphHighlight" mtype="{mtype}" mat="{mat}">{morph}</span>'.format(
                morph = m.inflected,
                mtype = mtype,
                mat = mat
                )
        txt = nonSpanSub( m.inflected, repl, txt )
    return txt
addHook( 'fmod_morphHighlight', highlight )
