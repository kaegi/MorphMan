# -*- coding: utf-8 -*-
import gzip
import pickle as pickle

from anki.hooks import wrap
from anki.lang import _
from aqt import toolbar

from .util import mw
from .preferences import cfg1


def getStatsPath(): return cfg1('path_stats')


def loadStats():
    try:
        f = gzip.open(getStatsPath())
        d = pickle.load(f)
        f.close()
        return d
    except IOError:  # file DNE => create it
        return updateStats()
    except AssertionError:  # profile not loaded yet, can't do anything but wait
        return None


def saveStats(d):
    f = gzip.open(getStatsPath(), 'wb')
    pickle.dump(d, f, -1)
    f.close()


def updateStats(known_db=None):
    mw.progress.start(label='Updating stats', immediate=True)

    from .morphemes import MorphDb

    # Load known.db and get total morphemes known
    if known_db is None:
        known_db = MorphDb(cfg1('path_known'), ignoreErrors=True)

    d = {'totalVariations': len(known_db.db), 'totalKnown': len(known_db.groups)}

    saveStats(d)
    mw.progress.finish()
    return d


def getStatsLink():
    d = loadStats()
    if not d:
        return 'K ???', '????'

    total_known = d.get('totalKnown', 0)
    total_variations = d.get('totalVariations', total_known)

    name = 'K %d V %d' % (total_known, total_variations)
    details = 'Total known morphs'
    return name, details


def my_centerLinks(self, _old):
    name, details = getStatsLink()
    links = [
        ["decks", _("Decks"), _("Shortcut key: %s") % "D"],
        ["add", _("Add"), _("Shortcut key: %s") % "A"],
        ["browse", _("Browse"), _("Shortcut key: %s") % "B"],
        ["stats", _("Stats"), _("Shortcut key: %s") % "T"],
        ["sync", _("Sync"), _("Shortcut key: %s") % "Y"],
        ["morph", _(name), _(details)],
    ]
    return self._linkHTML(links)


toolbar.Toolbar._centerLinks = wrap(toolbar.Toolbar._centerLinks, my_centerLinks, 'around')
