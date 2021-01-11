# -*- coding: utf-8 -*-
import codecs

import aqt.main

from anki import sched, schedv2
from anki import hooks
from anki.hooks import wrap
from anki.lang import _
from aqt import reviewer, dialogs
import re

from aqt.utils import tooltip

from . import main
from .util import mw, allDb
from .preferences import get_preference as cfg

assert isinstance(mw, aqt.main.AnkiQt)


# 1 after answering -> skip all cards with same focus as one just answered
# 2 hotkey -> set card as already known, skip it, and all others with same focus
# 3 hotkey -> search for all cards with same focus (in browser)
# 4 in browser -> immediately learn selected cards
# 5 on show -> highlight morphemes within expression according to how well known
# 6 on fill -> pull new cards from all child decks at once instead of sequentially

# config aliases
def CN(note, key): return cfg(key, note.mid)


def focusName(): return cfg('Field_FocusMorph')


def focus(n):
    focusValue = n[focusName()].strip()
    if focusValue == '':
        return []
    return [f.strip() for f in focusValue.split(',')]


def focusQuery(fieldName, focusMorphs):
    q = ' or '.join([r'"%s:re:(^|,|\s)%s($|,|\s)"' % (fieldName, f) for f in focusMorphs])
    if len(focusMorphs) > 0:
        q = '(%s)' % q
    return q


########## 6 parent deck pulls new cards from all children instead of sequentially (ie. mostly first)
def my_fillNew(self, recursing=False, _old=None):
    """If 'new card merged fill' is enabled for the current deck, when we refill we
    pull from all child decks, sort combined pool of cards, then limit.
    If disabled, do the standard sequential fill method"""
    def C(key): return cfg(key, None, self.col.decks.active()[0])

    if not C('new card merged fill'):
        return _old(self, recursing)

    if self._newQueue:
        return True
    if not self.newCount:
        return False

    self._newQueue = self.col.db.list(
        '''select id from cards where did in %s and queue = 0 and due >= ? order by due limit ?''' % self._deckLimit(),
        C('new card merged fill min due'), self.queueLimit )
    if self._newQueue:
        self._newQueue.reverse()
        return True


sched.Scheduler._fillNew = wrap(sched.Scheduler._fillNew, my_fillNew, 'around')
schedv2.Scheduler._fillNew = wrap(schedv2.Scheduler._fillNew, my_fillNew, 'around')

########## handle skipping for 1-2
seenMorphs = set()


def markFocusSeen(self, n):
    """Mark a focusMorph as already seen so future new cards with the same focus
    will be skipped. Also prints number of cards to be skipped if enabled"""
    global seenMorphs
    try:
        focusMorphs = focus(n)
    except KeyError:
        return

    if len(focusMorphs) == 0:
        return

    seenMorphs.update(focusMorphs)
    q = focusQuery(focusName(), focusMorphs)
    num_skipped = len(self.mw.col.findNotes(q)) - 1
    if num_skipped and cfg('print number of alternatives skipped'):
        tooltip(_('%d alternatives will be skipped' % num_skipped))


def my_getNewCard(self, _old):
    """Continually call _getNewCard until we get one with a focusMorph we haven't
    seen before. Also skip bad vocab cards.

    :type self: anki.sched.Scheduler | anki.schedv2.Scheduler
    :type _old: Callable
    """

    while True:
        def C(key): return cfg(key, None, self.col.decks.active()[0])
        if not C('next new card feature'):
            return _old(self)
        if not C('new card merged fill'):
            card = _old(self)  # type: anki.cards.Card
        else:
            if not self._fillNew():
                return
            card_id = self._newQueue.pop()
            card = self.col.getCard(card_id)
            self.newCount -= 1

        if not card:
            return  # no more cards
        note = card.note()

        # find the right morphemizer for this note, so we can apply model-dependent options (modify off == disable
        # skip feature)
        from .util import getFilter
        note_filter = getFilter(note)

        # this note is not configured in any filter -> proceed like normal without MorphMan-plugin
        # the deck should not be modified -> the user probably doesn't want the 'skip mature' feature
        if note_filter is None or not note_filter['Modify']:
            return card

        # get the focus morph
        try:
            focus_morphs = focus(note)  # field contains either the focusMorph or is empty
        except KeyError:
            tooltip(_('Encountered card without the \'focus morph\' field configured in the preferences. Please check '
                      'your MorphMan settings and note models.'))
            return card  # card has no focusMorph field -> undefined behavior -> just proceed like normal

        # evaluate all conditions, on which this card might be skipped/buried
        is_comprehension_card = note.hasTag(cfg('Tag_Comprehension'))
        is_fresh_vocab = note.hasTag(cfg('Tag_Fresh'))
        is_already_known = note.hasTag(cfg('Tag_AlreadyKnown'))

        skip_comprehension = cfg('Option_SkipComprehensionCards')
        skip_fresh = cfg('Option_SkipFreshVocabCards')
        skip_focus_morph_seen_today = cfg('Option_SkipFocusMorphSeenToday')

        skip_conditions = [
            is_comprehension_card and skip_comprehension,
            is_fresh_vocab and skip_fresh,
            is_already_known,  # the user requested that the vocabulary does not have to be shown
            skip_focus_morph_seen_today and any([focus in seenMorphs for focus in focus_morphs]) ,  # we already learned that/saw that today
        ]

        if not any(skip_conditions):
            break

        # skip/bury card if any skip condition is true
        self.buryCards([card.id])

        # the card was quarried from the "new queue" so we have to increase the "new counter" back to its original value
        self.newCount += 1
    return card


sched.Scheduler._getNewCard = wrap(sched.Scheduler._getNewCard, my_getNewCard, 'around')
schedv2.Scheduler._getNewCard = wrap(schedv2.Scheduler._getNewCard, my_getNewCard, 'around')


########## 1 - after learning a new focus morph, don't learn new cards with the same focus
def my_reviewer_answerCard(self, ease):  # 1
    # type: (reviewer.Reviewer, int) -> None
    if self.mw.state != "review" or self.state != "answer" or self.mw.col.sched.answerButtons(self.card) < ease:
        return

    if CN(self.card.note(), 'auto skip alternatives'):
        markFocusSeen(self, self.card.note())


reviewer.Reviewer._answerCard = wrap(reviewer.Reviewer._answerCard, my_reviewer_answerCard, "before")


########## 2 - set current card's focus morph as already known and skip alternatives
def setKnownAndSkip(self):  # 2
    # type: (reviewer.Reviewer) -> None
    """Set card as alreadyKnown and skip along with all other cards with same focusMorph.
    Useful if you see a focusMorph you already know from external knowledge
    """

    self.mw.checkpoint(_("Set already known focus morph"))
    n = self.card.note()
    n.addTag(cfg('Tag_AlreadyKnown'))
    n.flush()
    markFocusSeen(self, n)

    # "new counter" might have been decreased (but "new card" was not answered
    # so it shouldn't) -> this function recomputes "new counter"
    self.mw.col.reset()

    # skip card
    self.nextCard()


########## 3 - search in browser for cards with same focus
def browseSameFocus(self):  # 3
    """Opens browser and displays all notes with the same focus morph.
    Useful to quickly find alternative notes to learn focus from"""
    try:
        n = self.card.note()
        focusMorphs = focus(n)
        if len(focusMorphs) == 0:
            return

        q = focusQuery(focusName(), focusMorphs)
        b = dialogs.open('Browser', self.mw)
        b.form.searchEdit.lineEdit().setText(q)
        b.onSearchActivated()
    except KeyError:
        pass


########## set keybindings for 2-3
def my_reviewer_shortcutKeys(self):
    key_browse, key_skip = cfg('browse same focus key'), cfg('set known and skip key')
    keys = original_shortcutKeys(self)
    keys.extend([
        (key_browse, lambda: browseSameFocus(self)),
        (key_skip, lambda: setKnownAndSkip(self))
    ])
    return keys


original_shortcutKeys = reviewer.Reviewer._shortcutKeys
reviewer.Reviewer._shortcutKeys = my_reviewer_shortcutKeys


########## 4 - highlight morphemes using morphHighlight

def highlight(txt: str, field, filter: str, ctx) -> str:
    """When a field is marked with the 'focusMorph' command, we format it by
    wrapping all the morphemes in <span>s with attributes set to its maturity"""

    print("morphHighlight filter %s" % filter)
    if filter != "morphHighlight":
        return txt

    from .util import getFilter
    from .morphemes import getMorphemes

    # must avoid formatting a smaller morph that is contained in a bigger morph
    # => do largest subs first and don't sub anything already in <span>
    def nonSpanSub(sub, repl, string):
        return ''.join(re.sub(sub, repl, s, flags=re.IGNORECASE) if not s.startswith('<span') else s for s in
                       re.split('(<span.*?</span>)', string))

    frequency_list_path = cfg('path_frequency')
    try:
        with codecs.open(frequency_list_path, encoding='utf-8') as f:
            frequency_list = [line.strip().split('\t')[0] for line in f.readlines()]
    except:
        frequency_list = []

    priority_db = main.MorphDb(cfg('path_priority'), ignoreErrors=True).db

    note = ctx.note()
    tags = note.stringTags()
    filter = getFilter(note)
    if filter is None:
        return txt
    morphemizer = mw.morphemizerRegistry.getMorphemizer(filter['Morphemizer'])
    if morphemizer is None:
        return txt

    ms = getMorphemes(morphemizer, txt, tags)

    proper_nouns_known = cfg('Option_ProperNounsAlreadyKnown')

    for m in sorted(ms, key=lambda x: len(x.inflected), reverse=True):  # largest subs first
        locs = allDb().getMatchingLocs(m)
        mat = max(loc.maturity for loc in locs) if locs else 0

        if proper_nouns_known and m.isProperNoun():
            mtype = 'mature'
        elif mat >= cfg('threshold_mature'):
            mtype = 'mature'
        elif mat >= cfg('threshold_known'):
            mtype = 'known'
        elif mat >= cfg('threshold_seen'):
            mtype = 'seen'
        else:
            mtype = 'unknown'

        priority = 'true' if m in priority_db else 'false'

        focus_morph_string = m.show().split()[0]
        frequency = 'true' if focus_morph_string in frequency_list else 'false'

        repl = '<span class="morphHighlight" mtype="{mtype}" priority="{priority}" frequency="{frequency}" mat="{mat}">\\1</span>'.format(
            mtype=mtype,
            priority=priority,
            frequency=frequency,
            mat=mat
        )
        txt = nonSpanSub('(%s)' % m.inflected, repl, txt)
    return txt

hooks.field_filter.append(highlight)
