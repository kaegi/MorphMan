#-*- coding: utf-8 -*-
from aqt import reviewer, dialogs
from aqt.qt import *
from aqt.utils import tooltip
from anki import sched
from .util import addBrowserNoteSelectionCmd, addBrowserCardSelectionCmd, jcfg, cfg, cfg1, wrap, tooltip, mw, addHook, allDb, partial

# only for jedi-auto-completion
import aqt.main
assert isinstance(mw, aqt.main.AnkiQt)

from . import main

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
        q = '%s:%s' % ( focusName( n ), focus( n ) )
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

        if not c: return            # no more cards
        n = c.note()

        # find the right morphemizer for this note, so we can apply model-dependent options (modify off == disable skip feature)
        from .morphemes import getMorphemes
        from .util import getFilter
        notefilter = getFilter(n)
        if notefilter is None: return c # this note is not configured in any filter -> proceed like normal without MorphMan-plugin
        if not notefilter['Modify']: return c # the deck should not be modified -> the user probably doesn't want the 'skip mature' feature

        # get the focus morph
        try: focusMorph = focus( n )        # field contains either the focusMorph or is empty
        except KeyError:
            tooltip( _( 'Encountered card without the \'focus morph\' field configured in the preferences. Please check your MorphMan settings and note models.') )
            return c    # card has no focusMorph field -> undefined behavior -> just proceed like normal

        # evaluate all conditions, on which this card might be skipped/buried
        isVocabCard = n.hasTag(jcfg('Tag_Vocab'))
        isNotReady = n.hasTag(jcfg('Tag_NotReady'))
        isComprehensionCard = n.hasTag(jcfg('Tag_Comprehension'))
        isFreshVocab = n.hasTag(jcfg('Tag_Fresh'))
        isAlreadyKnown = n.hasTag( jcfg('Tag_AlreadyKnown') )

        skipComprehension = jcfg('Option_SkipComprehensionCards')
        skipFresh = jcfg('Option_SkipFreshVocabCards')
        skipFocusMorphSeenToday = jcfg('Option_SkipFocusMorphSeenToday')

        skipCondition1 = (isComprehensionCard and skipComprehension)
        skipCondition2 = (isFreshVocab and skipFresh)
        skipCondition3 = isAlreadyKnown # the user requested that the vocabulary does not have to be shown
        skipCondition4 = (focusMorph in seenMorphs and skipFocusMorphSeenToday) # we already learned that/saw that today
        #skipCondition5 = not (isVocabCard or isNotReady) # even if it is not a good vocabulary card, we have no choice when there are no other cards available

        # skip/bury card if any skip condition is true
        if skipCondition1 or skipCondition2 or skipCondition3 or skipCondition4:
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
        q = '%s:%s' % ( focusName( n ), focus( n ) )
        b = dialogs.open( 'Browser', self.mw )
        b.form.searchEdit.lineEdit().setText( q )
        b.onSearchActivated()
    except KeyError: pass

########## set keybindings for 2-3
def my_reviewer_shortcutKeys( self ):
    key_browse, key_skip = cfg1('browse same focus key'), cfg1('set known and skip key')
    keys = original_shortcutKeys( self ) 
    keys.extend([
        (key_browse, lambda: browseSameFocus( self )),
        (key_skip, lambda: setKnownAndSkip( self ))
    ])
    return keys

original_shortcutKeys = reviewer.Reviewer._shortcutKeys
reviewer.Reviewer._shortcutKeys = my_reviewer_shortcutKeys

########## 4 - immediately review selected cards
# def pre( b ):
#     ''' :type b: aqt.browser.Browser '''
#     return { 'cards':[], 'browser':b }
# def per( st, c ):
#     st['cards'].append( c )
#     return st
# def post( st ):
#     i = len(st['cards'])
#     for c in st['cards']:
#         mw.reviewer.cardQueue.append( c )

#     # in special cases close() will already pop a new card from mw.reviewer.cardQueue
#     st['browser'].close()
#     tooltip( _( 'Immediately reviewing %d cards' % i ) )

#     # only reset and fetch a new card if it wasn't already done with close()
#     return {'__reset': len(mw.reviewer.cardQueue) == i}

# addBrowserCardSelectionCmd( 'MorphMan: Learn Now', pre, per, post, tooltip='Immediately review the selected new cards', shortcut=('Ctrl+Shift+N',) )

########## 5 - highlight morphemes using morphHighlight
import re

def isNoteSame(note, fieldDict):
    # compare fields
    same_as_note = True
    items = list(note.items())
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
    from .util import getFilterByTagsAndType
    from .morphemizer import getMorphemizerByName
    from .morphemes import getMorphemes

    # must avoid formatting a smaller morph that is contained in a bigger morph
    # => do largest subs first and don't sub anything already in <span>
    def nonSpanSub( sub, repl, string ):
        return ''.join( re.sub( sub, repl, s ) if not s.startswith('<span') else s for s in re.split( '(<span.*?</span>)', string ) )

    # find morphemizer; because no note/card information is exposed through arguments, we have to find morphemizer based on tags alone
    #from aqt.qt import debug; debug()
    #
    #if mw.reviewer.card is None: return txt
    #note = mw.reviewer.card.note()
    #if not isNoteSame(note, fieldDict): return txt
    #from aqt.qt import debug; debug()

    tags = fieldDict['Tags'].split()
    filter = getFilterByTagsAndType(fieldDict['Type'], tags)
    if filter is None:
        return txt
    morphemizer = getMorphemizerByName(filter['Morphemizer'])
    if morphemizer is None:
        return txt
    ms = getMorphemes(morphemizer, txt, tags)

    for m in sorted( ms, key=lambda x: len(x.inflected), reverse=True ): # largest subs first
        locs = allDb().db.get( m, set() )
        mat = max( loc.maturity for loc in locs ) if locs else 0

        if   mat >= cfg1( 'threshold_mature' ):  mtype = 'mature'
        elif mat >= cfg1( 'threshold_known' ):   mtype = 'known'
        elif mat >= cfg1( 'threshold_seen' ):    mtype = 'seen'
        else:                                    mtype = 'unknown'
        repl = '<span class="morphHighlight" mtype="{mtype}" mat="{mat}">{morph}</span>'.format(
                morph = m.inflected,
                mtype = mtype,
                mat = mat
                )
        txt = nonSpanSub( m.inflected, repl, txt )
    return txt
addHook( 'fmod_morphHighlight', highlight )
