#-*- coding: utf-8 -*-
import os
from aqt import mw # this script isn't imported until profile is loaded

default = {
    'path_dbs': os.path.join( mw.pm.profileFolder(), 'dbs' ),
    'path_ext': os.path.join( mw.pm.profileFolder(), 'dbs', 'external.db' ),
    'path_all': os.path.join( mw.pm.profileFolder(), 'dbs', 'all.db' ),
    'path_known': os.path.join( mw.pm.profileFolder(), 'dbs', 'known.db' ),
    'path_mature': os.path.join( mw.pm.profileFolder(), 'dbs', 'mature.db' ),
    'path_log': os.path.join( mw.pm.profileFolder(), 'morphman.log' ),
    'threshold_mature': 21,
    'threshold_known': 3,
    'threshold_seen': 1,

    # speed tests show its faster to 100% recalc all.db rather than load the
    # existing one for 9000 fact collections
    'loadAllDb':False,
    'saveAllDb':True,

    # only these can have model/deck overrides
    'enabled':True,
        # field names to store various information
    'k+N':u'k+N',
    'm+N':u'm+N',
    'morphManIndex':u'morphManIndex',
    'unknowns':u'unknowns',
    'unmatures':u'unmatures',
    'unknownFreq':u'unknownFreq',
        # analyze notes based on the morphemes in these fields
    'morph_fields': [u'Expression'],
        # tag names for marking the state of notes
    'tagNames':[u'comprehension', u'vocab', u'notReady', u'focusMorph'],
        # controls for morpheme analysis
    'morph_blacklist': [ u'記号', u'UNKNOWN'],
}
# Can override anything
profile_overrides = {
}

# Models and decks can only override 'enabled' and later entries
model_overrides = {
}

# Currently this is unimplemented
deck_overrides = {
}
