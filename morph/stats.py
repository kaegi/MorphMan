#-*- coding: utf-8 -*-
import glob, gzip, os, pickle as pickle

from .util import cfg1, wrap, mw
from aqt import toolbar

from anki.lang import _

def getStatsPath(): return cfg1('path_stats')

def loadStats():
    try:
        f = gzip.open( getStatsPath(), 'rb' )
        d = pickle.load( f )
        f.close()
        return d
    except IOError:         # file DNE => create it
        return updateStats()
    except AssertionError:  # profile not loaded yet, can't do anything but wait
        return None

def saveStats( d ):
    f = gzip.open( getStatsPath(), 'wb' )
    pickle.dump( d, f, -1 )
    f.close()

def updateStats( knownDb=None ):
    mw.progress.start( label='Updating stats', immediate=True )

    from .morphemes import MorphDb
    d = {}

    # Load known.db and get total morphemes known
    if knownDb is None:
        knownDb = MorphDb( cfg1('path_known'), ignoreErrors=True )

    d['totalKnown'] = len( knownDb.db )

    saveStats( d )
    mw.progress.finish()
    return d

def getStatsLink():
    d = loadStats()
    if not d: return ( 'K ???', '????' )

    name = 'K %d' % d['totalKnown']
    details = 'Total known morphs'
    return ( name, details )

def my_centerLinks( self, _old ):
    name, details = getStatsLink()
    links = [
        ["decks", _("Decks"), _("Shortcut key: %s") % "D"],
        ["add", _("Add"), _("Shortcut key: %s") % "A"],
        ["browse", _("Browse"), _("Shortcut key: %s") % "B"],
        ["stats", _("Stats"), _("Shortcut key: %s") % "T"],
        ["sync", _("Sync"), _("Shortcut key: %s") % "Y"],
        ["morph", _(name), _(details)],
    ]
    return self._linkHTML( links )

toolbar.Toolbar._centerLinks = wrap( toolbar.Toolbar._centerLinks, my_centerLinks, 'around' )
