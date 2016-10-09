# -*- coding: utf-8 -*-
import codecs, datetime
from functools import partial
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from aqt.qt import *

from aqt import mw
from aqt.utils import showCritical, showInfo, showWarning, tooltip
from anki.hooks import addHook, wrap
from util_external import memoize

###############################################################################
## Global data
###############################################################################
_allDb = None
def allDb():
    global _allDb
    if _allDb is None:
        from morphemes import MorphDb
        _allDb = MorphDb( cfg1('path_all'), ignoreErrors=True )
    return _allDb

###############################################################################
## Config
###############################################################################
cfgMod = None
dbsPath = None
def initCfg():
    global cfgMod, dbsPath
    import config
    cfgMod = config
    dbsPath = config.default['path_dbs']

    # Redraw toolbar to update stats
    mw.toolbar.draw()

def initJcfg():
    global jcfgMod, dbsPath
    import json
    try:
        f = codecs.open( cfg1('path_json'), 'r', 'utf-8' )
        jcfgMod = json.load(f.read())
        f.close()
    except IOError:
        jcfgMod = jcfg_default()


addHook( 'profileLoaded', initCfg )
addHook( 'profileLoaded', initJcfg )

def cfg1( key, mid=None, did=None ): return cfg( mid, did, key )
def cfg( modelId, deckId, key ):
    assert cfgMod, 'Tried to use cfgMods before profile loaded'
    profile = mw.pm.name
    model = mw.col.models.get( modelId )[ 'name' ] if modelId else None
    deck = mw.col.decks.get( deckId )[ 'name' ] if deckId else None
    if key in cfgMod.deck_overrides.get( deck, [] ):
        return cfgMod.deck_overrides[ deck ][ key ]
    elif key in cfgMod.model_overrides.get( model, [] ):
        return cfgMod.model_overrides[ model ][ key ]
    elif key in cfgMod.profile_overrides.get( profile, [] ):
        return cfgMod.profile_overrides[ profile ][ key ]
    else:
        return cfgMod.default[ key ]

# --------------------
# configuration from .json file
jcfgMod = None
def jcfg_default():
    return {
        'Field_FocusMorph':u'MorphMan_FocusMorph',         # holds the unknown for k+0 sentences but goes away once m+0
        'Field_MorphManIndex':u'MorphMan_Index',   # created an ordering to learn cards in. this is the value new card 'due' times are set to
        'Field_Unmatures':u'MorphMan_Unmatures',               # likewise for unmatures
        'Field_UnmatureMorphCount':u'MorphMan_UnmatureMorphCount',       # stores how many unmatures
        'Field_Unknowns':u'MorphMan_Unknowns',             # comma seperated list of morphemes that are unknown
        'Field_UnknownFreq':u'MorphMan_UnknownFreq',       # average of how many times the unknowns appear in your collection
        'Field_UnknownMorphCount':u'MorphMan_UnknownMorphCount',       # stores how many unknowns

        # tag names for marking the state of notes
        # the following three are mutually exclusive and erase eachother upon promotion/demotion
        'Tag_Comprehension':u'mm_comprehension',   # set once all morphs for note are mature
        'Tag_Vocab':u'mm_vocab',                   # set once all but 1 morph for note is known
        'Tag_NotReady':u'mm_notReady',             # set for k+2 and above cards
        'Tag_AlreadyKnown':u'mm_alreadyKnown',     # you can add this tag to a note to make anki treat it as if mature
        'Tag_Priority':u'mm_priority',             # set if note contains an unknown that exists in priority.db
        'Tag_BadLength':u'mm_badLength',           # set if sentence isn't within optimal sentence length range
        'Tag_TooLong':u'mm_tooLong',               # set if sentence is above optimal sentence length

        # filter for cards that should be analyzed, higher entries have higher priority
        'Filter': [
            # note type (None means all note types), list of tags, list of morph fields for this note type -> morphemizer, analyze only or modify?
            {'Type': 'SubtitleMemorize', 'Tags': ['japanese'], 'Fields': ['Expression'], 'Morphemizer': 'MecabMorphemizer', 'Modify': True},
            {'Type': 'SubtitleMemorize', 'Tags': [          ], 'Fields': ['Expression'], 'Morphemizer': 'SpaceMorphemizer', 'Modify': True},
        ]
    }

def jcfg():
    assert jcfgMod, 'Tried to use jcfgMods before profile loaded'
    return jcfgMod

def jcfgUpdate(jcfg):
    print jcfg
    for key, value in jcfg.items():
        assert key in jcfgMod, "jcfgUpdate(): key is is not in jcfgMod"
        jcfgMod[key] = value


###############################################################################
## Parsing
###############################################################################
def parseWhitelist( wstr ):
    ustr = unicode( wstr )
    return ustr.split( u',' ) if ustr else []

###############################################################################
## Fact browser utils
###############################################################################
def doOnSelection( b, preF, perF, postF, progLabel ):
    st = preF( b )
    if not st: return

    nids = b.selectedNotes()
    mw.progress.start( label=progLabel, max=len( nids ) )
    for i,nid in enumerate( nids ):
        mw.progress.update( value=i )
        n = mw.col.getNote( nid )
        st = perF( st, n )
    mw.progress.finish()

    st = postF( st )
    mw.col.updateFieldCache( nids )
    if not st or st.get( '__reset', True ):
        mw.reset()

def addBrowserSelectionCmd( menuLabel, preF, perF, postF, tooltip=None, shortcut=None, progLabel='Working...' ):
    def setupMenu( b ):
        a = QAction( menuLabel, b )
        if tooltip:     a.setStatusTip( tooltip )
        if shortcut:    a.setShortcut( QKeySequence( *shortcut ) )
        b.connect( a, SIGNAL('triggered()'), lambda b=b: doOnSelection( b, preF, perF, postF, progLabel ) )
        b.form.menuEdit.addAction( a )
    addHook( 'browser.setupMenus', setupMenu )

###############################################################################
## Logging and MsgBoxes
###############################################################################
def errorMsg( msg ):
    showCritical( msg )
    printf( msg )
def infoMsg( msg ):
    showInfo( msg )
    printf( msg )

def printf( msg ):
    txt = '%s: %s' % ( datetime.datetime.now(), msg )
    f = codecs.open( cfg1('path_log'), 'a', 'utf-8' )
    f.write( txt+'\r\n' )
    f.close()
    print txt

def clearLog():
    f = codecs.open( cfg1('path_log'), 'w', 'utf-8' )
    f.close()

###############################################################################
## Qt helper functions
###############################################################################
def mkBtn( txt, f, conn, parent ):
    b = QPushButton( txt )
    conn.connect( b, SIGNAL('clicked()'), f )
    parent.addWidget( b )
    return b

###############################################################################
## Mplayer settings
###############################################################################
from anki import sound
#sound.mplayerCmd += [ '-fs' ]
