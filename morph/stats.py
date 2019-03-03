#-*- coding: utf-8 -*-
import glob, gzip, os, pickle as pickle

from .util import addHook, cfg1, wrap, mw
from aqt import toolbar

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

    # Load Goal.*.db dbs, get morphemes required, and compare vs known.db
    d['goals'] = {}
    goalDbPaths = glob.glob( os.path.join( cfg1('path_dbs'), 'Goal.*.db' ) )

    for path in goalDbPaths:
        name = os.path.basename( path )[5:][:-3]
        gdb = MorphDb( path )

        # track total unique morphemes + when weighted by frequency
        # NOTE: a morpheme may occur multiple times within the same sentence, but this frequency is wrt note fields
        numUniqueReq, numUniqueKnown, numFreqReq, numFreqKnown = 0, 0, 0, 0
        for m in gdb.db.keys():
            freq = gdb.db.frequency(m)
            numUniqueReq += 1
            numFreqReq   += freq
            if m in knownDb.db:
                numUniqueKnown += 1
                numFreqKnown   += freq

        d['goals'][ name ] = { 'total':numUniqueReq, 'known':numUniqueKnown, 'freqTotal':numFreqReq, 'freqKnown':numFreqKnown }

    saveStats( d )
    mw.progress.finish()
    return d

def getStatsLink():
    d = loadStats()
    if not d: return ( 'K ???', '????' )

    name = 'K %d' % d['totalKnown']
    lines = []
    for goalName, g in sorted( d['goals'].items() ):
        #lines.append( '%s %d/%d %d%%' % ( goalName, g['known'], g['total'], 100.*g['known']/g['total'] ) )
        #lines.append( '%s %d%%' % ( goalName, 100.*g['known']/g['total'] ) )
        lines.append( '%s %d%% %d%%' % ( goalName, 100.*g['known']/g['total'], 100.*g['freqKnown']/g['freqTotal'] ) )
    details = '\n'.join( lines )
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
