# -*- coding: utf-8 -*-
import gzip
import pickle as pickle

from anki.hooks import wrap
from anki.lang import _
from aqt import toolbar, gui_hooks
from aqt.utils import tooltip

from .util import mw
from .preferences import get_preference as cfg


def getStatsPath(): return cfg('path_stats')


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
        known_db = MorphDb(cfg('path_known'), ignoreErrors=True)

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


def on_morph_link_clicked():
    tooltip("Total known morphs")


def on_top_toolbar_did_init_links(links, toolbar):
    name, details = getStatsLink()
    links.append(
        toolbar.create_link(
            "morph", _(name), on_morph_link_clicked, tip=_(details), id="morph"
        )
    )


gui_hooks.top_toolbar_did_init_links.append(on_top_toolbar_did_init_links)
