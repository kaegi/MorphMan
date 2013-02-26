#-*- coding: utf-8 -*-
import os
from aqt import mw # this script isn't imported until profile is loaded

# 4th (lowest) priority
default = {
    'path_dbs': os.path.join( mw.pm.profileFolder(), 'dbs' ),
    'path_ext': os.path.join( mw.pm.profileFolder(), 'dbs', 'external.db' ),
    'path_all': os.path.join( mw.pm.profileFolder(), 'dbs', 'all.db' ),
    'path_known': os.path.join( mw.pm.profileFolder(), 'dbs', 'known.db' ),
    'path_mature': os.path.join( mw.pm.profileFolder(), 'dbs', 'mature.db' ),
    'path_log': os.path.join( mw.pm.profileFolder(), 'morphman.log' ),
    'threshold_mature': 21,
    'threshold_known': 10/86400.,
    'threshold_seen': 1/86400.,
    'browse same focus key': 'l',
    'set known and skip key': 'k',
    'print number of alternatives skipped': True,

    # speed tests show its faster to 100% recalc all.db rather than load the
    # existing one for 9000 fact collections
    'loadAllDb':False,
    'saveAllDb':True,

    # only these can have model overrides
    'enabled':False,
        # field names to store various information
    'k+N':u'k+N',
    'm+N':u'm+N',
    'morphManIndex':u'morphManIndex',
    'focusMorph':u'focusMorph', # holds the unknown for k+0 sentences but goes away once m+0
    'unknowns':u'unknowns',
    'unmatures':u'unmatures',
    'unknownFreq':u'unknownFreq',
        # analyze notes based on the morphemes in these fields
    'morph_fields': [u'Expression'],
        # tag names for marking the state of notes
    'tag_comprehension':u'comprehension',
    'tag_vocab':u'vocab',
    'tag_notReady':u'notReady',
    'tag_alreadyKnown':u'alreadyKnown',
        # controls for morpheme analysis
    'morph_blacklist': [ u'記号', u'UNKNOWN'],
    'batchMediaFields': [ u'Video', u'Sound' ],
    'optimal sentence length': 4,

    # only these can have deck overrides
    'new card merged fill':True,
}
# Can override anything. 3rd priority
profile_overrides = {
}

# Model overrides can only override the entries marked above. 2nd priority
model_overrides = {
    'subs2srs': { 'enabled':True },
}

# Deck overrides can only override 'new card merged fill'. 1st priority
deck_overrides = {
    'subs2srs': { 'new card merged fill':True },
}
