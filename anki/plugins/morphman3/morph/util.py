# -*- coding: utf-8 -*-
import codecs, datetime
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from aqt.qt import *

from aqt import mw
from aqt.utils import showCritical, showInfo, showWarning, tooltip
from anki.hooks import addHook, wrap

###############################################################################
## Global data
###############################################################################
_allDb = None
def allDb():
    global _allDb
    if not _allDb:
        from morphemes import MorphDb
        _allDb = MorphDb( cfg1('path_all'), ignoreErrors=True )
    return _allDb

###############################################################################
## Config
###############################################################################
cfgMod = None
def initCfg():
    global cfgMod, dbsPath
    import config
    cfgMod = config
    dbsPath = config.default['path_dbs']

addHook( 'profileLoaded', initCfg )

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
## Functional tools
###############################################################################
class memoize(object):
   '''Decorator that memoizes a function'''
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      try:
         return self.cache[args]
      except KeyError:
         value = self.func(*args)
         self.cache[args] = value
         return value
      except TypeError: # uncachable -- for instance, passing a list as an argument. Better to not cache than to blow up entirely.
         return self.func(*args)
   def __repr__(self):
      """Return the function's docstring"""
      return self.func.__doc__
   def __get__(self, obj, objtype):
      """Support instance methods"""
      return functools.partial(self.__call__, obj)

###############################################################################
## Mplayer settings
###############################################################################
from anki import sound
sound.mplayerCmd += [ '-fs' ]
