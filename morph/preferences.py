# -*- coding: utf-8 -*-
import importlib

from aqt import mw


def initPreferences():
    initCfg()
    initJcfg()


cfgMod = None
dbsPath = None


def initCfg():
    global cfgMod, dbsPath
    from . import config
    importlib.reload(config)
    cfgMod = config
    dbsPath = config.default['path_dbs']

    # Redraw toolbar to update stats
    mw.toolbar.draw()


def cfg1(key, modelId=None, deckId=None):
    assert cfgMod, 'Tried to use cfgMods before profile loaded'
    profile = mw.pm.name
    model = mw.col.models.get(modelId)['name'] if modelId else None
    deck = mw.col.decks.get(deckId)['name'] if deckId else None
    if key in cfgMod.deck_overrides.get(deck, []):
        return cfgMod.deck_overrides[deck][key]
    elif key in cfgMod.model_overrides.get(model, []):
        return cfgMod.model_overrides[model][key]
    elif key in cfgMod.profile_overrides.get(profile, []):
        return cfgMod.profile_overrides[profile][key]
    else:
        return cfgMod.default[key]


def initJcfg():
    mw.col.conf.setdefault(
        'addons', {}).setdefault(
        'morphman', jcfg_default())

    # this ensures forward compatibility, because it adds new options in configuration without any notice
    jcfgAddMissing()


def jcfg_default():
    return {
        'Field_FocusMorph': 'MorphMan_FocusMorph',  # holds the unknown for k+0 sentences but goes away once m+0
        'Field_MorphManIndex': 'MorphMan_Index',
        # created an ordering to learn cards in. this is the value new card 'due' times are set to
        'Field_Unmatures': 'MorphMan_Unmatures',  # likewise for unmatures
        'Field_UnmatureMorphCount': 'MorphMan_UnmatureMorphCount',  # stores how many unmatures
        'Field_Unknowns': 'MorphMan_Unknowns',  # comma seperated list of morphemes that are unknown
        'Field_UnknownFreq': 'MorphMan_UnknownFreq',  # average of how many times the unknowns appear in your collection
        'Field_UnknownMorphCount': 'MorphMan_UnknownMorphCount',  # stores how many unknowns

        # tag names for marking the state of notes
        # the following three are mutually exclusive and erase eachother upon promotion/demotion
        'Tag_Comprehension': 'mm_comprehension',  # set once all morphs for note are mature
        'Tag_Vocab': 'mm_vocab',  # set once all but 1 morph for note is known
        'Tag_Fresh': 'mm_fresh',
        # we have no unkown words, but multiple unmature -> alternative card for vocab or original vocab card
        'Tag_NotReady': 'mm_notReady',  # set for k+2 and above cards
        'Tag_AlreadyKnown': 'mm_alreadyKnown',  # you can add this tag to a note to make anki treat it as if mature
        'Tag_Priority': 'mm_priority',  # set if note contains an unknown that exists in priority.db
        'Tag_TooShort': 'mm_tooShort',  # set if sentence is below optimal length range
        'Tag_TooLong': 'mm_tooLong',  # set if sentence is above optimal length range
        'Tag_Frequency': 'mm_frequency',  # set if sentence is above optimal length range

        # filter for cards that should be analyzed, higher entries have higher priority
        'Filter': [
            # note type (None means all note types), list of tags, list of morph fields for this note type -> morphemizer, analyze only or modify?
            {'Type': 'SubtitleMemorize', 'TypeId': None, 'Tags': ['japanese'], 'Fields': ['Expression'],
             'Morphemizer': 'MecabMorphemizer', 'Modify': True},
            {'Type': 'SubtitleMemorize', 'TypeId': None, 'Tags': [], 'Fields': ['Expression'],
             'Morphemizer': 'SpaceMorphemizer', 'Modify': True},
        ],

        # This field lets you dictate string-to-morpheme conversions. This is useful for cases
        # where the morphemizer fails or you want to ignore specific parts of sentences (e.g. character
        # annotations like "<<Thomas>> Hello Peter! <<Peter>> Hi!").
        #
        # Every entry in this list is a 3-tuple specifying a replace-rule.
        #   - the first entry is a list of tags to restrict application of the rule. For example: ['Spanish', 'NewDrama']. This list can be empty to include all notes.
        #   - the second entry is a python regex describing the string. For example '<<.*?>>' to match everything between << and >>. Capturing groups are not allowed.
        #   - the third entry is a list of strings/morphemes which are returned for the matched string; the list can be empty
        #
        # So for example:
        #   ([u'English', u'ThatSeriesTag'], u'<<.*?>>', [])  ignores character annotations in notes with the tags 'English' and 'ThatSeriesTag'
        #   ([u'English'], u'a single expression', [u'a', u'single expression'])  will group 'single expression' in 'a single expression' into one "morpheme"
        #
        # The application of the rules works as following:
        #   - find the first rule that matches the note expression field or if no rule applies, call the morphemizer
        #   - find the first match in that field
        #   - "replace" the string with the given morphems
        #   - repeat this procedure with the text left from the match, then with the text right from the match
        #
        # One important property of the application algorithm is that if the match is in the middle of a sentence, the
        # morphemizer will only see both parts of the rest-sentence separately. A morphemizer (e.g. a japanese word segmenter)
        # that heavily relies on context and grammar might not produce the best results for "broken" sentences.
        'ReplaceRules': [],

        # only set necessary tags or set all tags?
        'Option_SetNotRequiredTags': True,
        # do not set tags/remove tags that are only there for user to read/filter with
        'Option_SkipComprehensionCards': True,  # bury/skip all new cards that have 'Tag_Comprehension'
        'Option_SkipFreshVocabCards': True,  # bury/skip all new cards that have 'Tag_Fresh'
        'Option_SkipFocusMorphSeenToday': True,
        # bury/skip all new cards that have a focus morph that was reviewed today/marked as `already known`
        'Option_IgnoreBracketContents': False,
    }


def _jcfg2():
    conf = mw.col.conf['addons']['morphman']
    assert conf, 'Tried to use jcfgMods before profile loaded'
    return conf


def jcfg(name):
    return _jcfg2().get(name)


def jcfgUpdate(jcfg):
    original = mw.col.conf['addons']['morphman'].copy()
    mw.col.conf['addons']['morphman'].update(jcfg)
    if not mw.col.conf['addons']['morphman'] == original:
        mw.col.setMod()


def jcfgAddMissing():
    # this ensures forward compatibility, because it adds new options in configuration (introduced by update) without
    # any notice with default value
    current = _jcfg2().copy()
    default = jcfg_default()
    for key, value in default.items():
        if key not in current:
            current[key] = value
    jcfgUpdate(current)
