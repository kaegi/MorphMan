#-*- coding: utf-8 -*-
import os
from aqt import mw # this script isn't imported until profile is loaded

# 4th (lowest) priority
default = {
    'path_dbs': os.path.join( mw.pm.profileFolder(), 'dbs' ),
    'path_priority': os.path.join( mw.pm.profileFolder(), 'dbs', 'priority.db' ),
    'path_ext': os.path.join( mw.pm.profileFolder(), 'dbs', 'external.db' ),
    'path_all': os.path.join( mw.pm.profileFolder(), 'dbs', 'all.db' ),
    'path_mature': os.path.join( mw.pm.profileFolder(), 'dbs', 'mature.db' ),
    'path_known': os.path.join( mw.pm.profileFolder(), 'dbs', 'known.db' ),
    'path_seen': os.path.join( mw.pm.profileFolder(), 'dbs', 'seen.db' ),
    'path_log': os.path.join( mw.pm.profileFolder(), 'morphman.log' ),
    'path_stats': os.path.join( mw.pm.profileFolder(), 'morphman.stats' ),
        # change the thresholds for various stages of maturity, in days
    'threshold_mature': 21,         # 21 days is what Anki uses
    'threshold_known': 10/86400.,   # recommend a few seconds if you want to count things in learning queue or ~3 days otherwise
    'threshold_seen': 1/86400.,     # this currently isn't used outside of create seen.db for your personal usage
    'text file import maturity':22, # when you import a file via Extract Morphemes from file, they are all given this maturity
        # reviewer mode keybindings
    'browse same focus key': 'l',
    'set known and skip key': 'k',
    'auto skip alternatives': True,
    'print number of alternatives skipped': True,   # after answering or skipping a card in reviewer

    # database saving/loading. you can disable these for performance reasons but their semantics are uninitutive
        # for example: features like morphHighlight always try to load all.db and expect it to be up to date
        # so not saving all.db and having it load an out of date copy many produce strange behavior
    'loadAllDb':True,   # whether to load existing all.db when recalculating or create one from scratch
    'saveDbs':True,     # whether to save all.db, known.db, mature.db, and seen.db

    # only these can have model overrides
    'enabled':False,    # whether to analyze notes of a given model, modify their fields, and manipulate due time by Morph Man Index
    'set due based on mmi':True,    # whether to modify card Due times based on MorphManIndex. does nothing if relevant notes aren't enabled
    'ignore maturity':False,        # if True, pretends card maturity is always zero
        # field names to store various information
    'k+N':u'k+N',       # stores how many unknowns
    'm+N':u'm+N',       # stores how many unmatures
    'focusMorph':u'MorphMan_FocusMorph',         # holds the unknown for k+0 sentences but goes away once m+0
    'morphManIndex':u'MorphMan_Index',   # created an ordering to learn cards in. this is the value new card 'due' times are set to
    'unmatures':u'MorphMan_Unmatures',               # likewise for unmatures
    'unknowns':u'MorphMan_Unknowns',             # comma seperated list of morphemes that are unknown
    'unknownFreq':u'MorphMan_UnknownFreq',       # average of how many times the unknowns appear in your collection
        # analyze notes based on the morphemes in these fields
    'morph_fields': [u'ExpressionSeries'],
        # tag names for marking the state of notes
            # the following three are mutually exclusive and erase eachother upon promotion/demotion
    'tag_comprehension':u'comprehension',   # set once all morphs for note are mature
    'tag_vocab':u'vocab',                   # set once all but 1 morph for note is known
    'tag_notReady':u'notReady',             # set for k+2 and above cards
    'tag_alreadyKnown':u'alreadyKnown',     # you can add this tag to a note to make anki treat it as if mature
    'tag_priority':u'priority',             # set if note contains an unknown that exists in priority.db
    'tag_badLength':u'badLength',           # set if sentence isn't within optimal sentence length range
    'tag_tooLong':u'tooLong',               # set if sentence is above optimal sentence length

        # controls for morpheme analysis (only for japanese/mecab morphemizer)
    'mecab_blacklist': [ u'記号', u'UNKNOWN'],      # you probably don't care about punctuation and things mecab couldn't parse
    'japanese_tag': 'japanese',              # if a note has this tag, morphemes are be split with mecab, otherwise a space-based morphemizer is used

        # try playing fields in this order when using batch media player
    'batch media fields': [ u'Video', u'Sound' ],
        # configure morph man index algorithm
    'optimal sentence length': 4,           # +1000 MMI per morpheme more/less than this after the first 2
    'reinforce new vocab weight': 5.0,      # -reinforce_weight / maturity MMI per known that is not yet mature
    'verb bonus': 100,                      # -verb_bonus if at least one unknown is a verb
    'priority.db weight': 200,              # -priority_weight per unknown that exists in priority.db
        # lite update
    'only update k+2 and below': False,     # this reduces how many notes are changed and thus sync burden by not updating notes that aren't as important

    # only these can have deck overrides
    'next new card feature':True,   # skip cards with focusMorph that was already seen or aren't k+1
    'new card merged fill':False,   # fill new card queue with cards from all child decks instead of sequentially. also enforce a minimum due value
    'new card merged fill min due':10000,   # k+1 by default. this mostly is to boost performance of 'next new card feature'
}
# Can override anything. 3rd priority
profile_overrides = {
}

# Model overrides can only override the entries marked above. 2nd priority
model_overrides = {
    'subs2srs':         { 'enabled':True },
    'SubtitleMemorize': { 'enabled':True },
    'vn2srs':           { 'enabled':True },
    'JtMW':             { 'enabled':True, 'set due based on mmi': False, 'ignore maturity': True },
    'JSPfEC':           { 'enabled':True, 'set due based on mmi': False },
    'Tae Kim Cloze':    { 'enabled':True, 'set due based on mmi': False },
    'Yotsubato':        { 'enabled':True, 'set due based on mmi': True },
    'Rikaisama':        { 'enabled':True, 'set due based on mmi': False },
   #'Kore':             { 'enabled':True, 'set due based on mmi': False, 'morph_fields':[u'SentenceExpression'] },
    'Kore':             { 'enabled':True, 'set due based on mmi': False },
}

# Deck overrides can only override 'new card merged fill' options. 1st priority
deck_overrides = {
    'Sentences':            { 'new card merged fill':True },
    'Sentences::subs2srs':  { 'new card merged fill':True },
    'Sentences::vn2srs':    { 'new card merged fill':True },
    'ExtraVocab':           { 'new card merged fill':True },
    'ExtraVocab::_Yotsubato':   { 'new card merged fill':True },
    'ExtraVocab::_Kore':        { 'new card merged fill':True },
}
