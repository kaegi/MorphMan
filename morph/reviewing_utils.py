# -*- coding: utf-8 -*-
import codecs
import re
from typing import List, Optional

from aqt import dialogs
from aqt.reviewer import Reviewer
from aqt.utils import tooltip

from anki.notes import Note
from anki.consts import CARD_TYPE_NEW

from . import main
from .util import get_all_db, get_filter
from .preferences import get_preference

from .morphemizer import getMorphemizerByName
from .morphemes import getMorphemes

seen_morphs = set()


# 1 after answering -> skip all cards with same focus as one just answered
# 2 hotkey -> set card as already known, skip it, and all others with same focus
# 3 hotkey -> search for all cards with same focus (in browser)
# 4 in browser -> immediately learn selected cards
# 5 on show -> highlight morphemes within expression according to how well known
# 6 on fill -> pull new cards from all child decks at once instead of sequentially


def try_to_get_focus_morphs(note: Note) -> Optional[List[str]]:
    try:
        focus_value = note[get_preference('Field_FocusMorph')].strip()
        if focus_value == '':
            return []
        return [f.strip() for f in focus_value.split(',')]
    except KeyError:
        return None


def focus_query(field_name, focus_morphs):
    q = ' or '.join([r'"%s:re:(^|,|\s)%s($|,|\s)"' % (field_name, re.escape(f)) for f in focus_morphs])
    if len(focus_morphs) > 0:
        q = '(%s)' % q
    return q


def mark_morph_seen(note: Note) -> None:
    focus_morphs = try_to_get_focus_morphs(note)

    if focus_morphs is not None and len(focus_morphs) > 0:
        seen_morphs.update(focus_morphs)


def my_next_card(self: Reviewer, _old) -> None:
    skipped_cards = SkippedCards()

    self.previous_card = self.card
    self.card = None
    self._v3 = None

    # NB! If the deck you are studying has sub-decks then new cards will by default only be gathered from the first
    # sub-deck until it is empty before looking for new cards in the next sub-deck. If you instead want to get
    # new i+1 cards from all sub-decks do the following:
    # 1. Activate the v3 scheduler in: Tools -> Review -> Scheduler -> V3 scheduler
    # 2. Deck that has sub-decks: Deck options -> Display Order -> New card gather order -> Ascending position

    if self.mw.col.sched.version < 3:
        self._get_next_v1_v2_card()
    else:
        self._get_next_v3_card()

    self._previous_card_info.set_card(self.previous_card)
    self._card_info.set_card(self.card)

    if not self.card:
        self.mw.moveToState("overview")
        return

    while True:
        if self.card.type != CARD_TYPE_NEW:
            break  # ignore non-new cards

        note: Note = self.card.note()
        note_filter = get_filter(note)  # Note filters from preferences GUI

        if note_filter is None:
            break  # card did not match (note type and tags) set in preferences GUI

        if not note_filter['Modify']:
            break  # modify is not set in preferences GUI

        focus_morphs = try_to_get_focus_morphs(note)

        if focus_morphs is None:
            tooltip(
                ('Encountered card without the \'focus morph\' field configured in the preferences. Please check '
                 'your MorphMan settings and note models.'))
            break

        skipped_card = skipped_cards.process_skip_conditions_of_card(note, focus_morphs)

        if not skipped_card:
            break  # card did not meet any skip criteria

        self.mw.col.sched.buryCards([self.card.id], manual=False)

        if self.mw.col.sched.version < 3:
            self._get_next_v1_v2_card()
        else:
            self._get_next_v3_card()

    if self._reps is None:
        self._initWeb()

    self._showQuestion()

    # TODO: add option to preferences GUI
    if skipped_cards.skipped_at_least_one_card() and get_preference('print number of alternatives skipped'):
        skipped_cards.show_tooltip_of_skipped_cards()


def set_known_and_skip(self):  # 2
    # type: (Reviewer) -> None
    """Set card as alreadyKnown and skip along with all other cards with same focusMorph.
    Useful if you see a focusMorph you already know from external knowledge
    """
    assert self.card is not None

    self.mw.checkpoint(("Set already known focus morph"))
    note = self.card.note()
    note.add_tag(get_preference('Tag_AlreadyKnown'))
    note.flush()
    mark_morph_seen(note)

    # "new counter" might have been decreased (but "new card" was not answered
    # so it shouldn't) -> this function recomputes "new counter"
    self.mw.col.reset()  # TODO: Is this still necessary?

    # skip card
    self.nextCard()


########## 3 - search in browser for cards with same focus
def browse_same_focus(self):  # 3
    """Opens browser and displays all notes with the same focus morph.
    Useful to quickly find alternative notes to learn focus from"""
    try:
        n = self.card.note()
        focus_morphs = try_to_get_focus_morphs(n)
        if len(focus_morphs) == 0:
            return

        q = focus_query(get_preference('Field_FocusMorph'), focus_morphs)
        b = dialogs.open('Browser', self.mw)
        b.form.searchEdit.lineEdit().setText(q)
        b.onSearchActivated()
    except KeyError:
        pass


########## set keybindings for 2-3
def my_reviewer_shortcutKeys(self):
    key_browse, key_skip = get_preference('browse same focus key'), get_preference('set known and skip key')
    keys = original_shortcutKeys(self)
    keys.extend([
        (key_browse, lambda: browse_same_focus(self)),
        (key_skip, lambda: set_known_and_skip(self))
    ])
    return keys


original_shortcutKeys = Reviewer._shortcutKeys  # TODO: move to init file
Reviewer._shortcutKeys = my_reviewer_shortcutKeys


########## 4 - highlight morphemes using morphHighlight

def highlight(txt: str, field, filter: str, ctx) -> str:
    """When a field is marked with the 'focusMorph' command, we format it by
    wrapping all the morphemes in <span>s with attributes set to its maturity"""

    print("morphHighlight filter %s" % filter)
    if filter != "morphHighlight":
        return txt

    # must avoid formatting a smaller morph that is contained in a bigger morph
    # => do largest subs first and don't sub anything already in <span>
    def nonSpanSub(sub, repl, string):
        return ''.join(re.sub(sub, repl, s, flags=re.IGNORECASE) if not s.startswith('<span') else s for s in
                       re.split('(<span.*?</span>)', string))

    frequency_list_path = get_preference('path_frequency')
    try:
        with codecs.open(frequency_list_path, encoding='utf-8') as f:
            frequency_list = [line.strip().split('\t')[0] for line in f.readlines()]
    except:
        frequency_list = []

    priority_db = main.MorphDb(get_preference('path_priority'), ignoreErrors=True).db

    note = ctx.note()
    tags = note.stringTags()
    filter = get_filter(note)
    if filter is None:
        return txt
    morphemizer = getMorphemizerByName(filter['Morphemizer'])
    if morphemizer is None:
        return txt

    ms = getMorphemes(morphemizer, txt, tags)

    proper_nouns_known = get_preference('Option_ProperNounsAlreadyKnown')

    for m in sorted(ms, key=lambda x: len(x.inflected), reverse=True):  # largest subs first
        locs = get_all_db().getMatchingLocs(m)
        mat = max(loc.maturity for loc in locs) if locs else 0

        if proper_nouns_known and m.isProperNoun():
            mtype = 'mature'
        elif mat >= get_preference('threshold_mature'):
            mtype = 'mature'
        elif mat >= get_preference('threshold_known'):
            mtype = 'known'
        elif mat >= get_preference('threshold_seen'):
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


class SkippedCards:

    def __init__(self):
        self.skipped_cards = {'comprehension': 0, 'fresh': 0, 'known': 0, 'today': 0}
        self.skip_comprehension = get_preference('Option_SkipComprehensionCards')
        self.skip_fresh = get_preference('Option_SkipFreshVocabCards')
        self.skip_focus_morph_seen_today = get_preference('Option_SkipFocusMorphSeenToday')

    def process_skip_conditions_of_card(self, note: Note, focus_morphs: list[str]) -> bool:
        # skip conditions set in preferences GUI
        is_comprehension_card = note.has_tag(get_preference('Tag_Comprehension'))
        is_fresh_vocab = note.has_tag(get_preference('Tag_Fresh'))
        is_already_known = note.has_tag(get_preference('Tag_AlreadyKnown'))

        if is_comprehension_card:
            if self.skip_comprehension:
                self.skipped_cards['comprehension'] += 1
                return True
        elif is_fresh_vocab:
            if self.skip_fresh:
                self.skipped_cards['fresh'] += 1
                return True
        elif is_already_known:  # the user requested that the vocabulary does not have to be shown
            self.skipped_cards['known'] += 1
            return True
        elif self.skip_focus_morph_seen_today and any([focus in seen_morphs for focus in focus_morphs]):
            self.skipped_cards['today'] += 1
            return True

        return False

    def skipped_at_least_one_card(self):
        for key in self.skipped_cards.keys():
            if self.skipped_cards[key] > 0:
                return True
        return False

    def show_tooltip_of_skipped_cards(self):
        skipped_string = ''

        if self.skipped_cards['comprehension'] > 0:
            skipped_string += f"Skipped <b>{self.skipped_cards['comprehension']}</b> comprehension cards"
        if self.skipped_cards['fresh'] > 0:
            if skipped_string != '':
                skipped_string += '<br>'
            skipped_string += f"Skipped <b>{self.skipped_cards['fresh']}</b> cards with fresh vocab"
        if self.skipped_cards['known'] > 0:
            if skipped_string != '':
                skipped_string += '<br>'
            skipped_string += f"Skipped <b>{self.skipped_cards['known']}</b> already known vocab cards"
        if self.skipped_cards['today'] > 0:
            if skipped_string != '':
                skipped_string += '<br>'
            skipped_string += f"Skipped <b>{self.skipped_cards['today']}</b> cards with focus morph already seen today"

        tooltip(skipped_string)
