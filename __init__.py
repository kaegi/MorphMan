from .morph.util import *
from PyQt5.QtWidgets import *
import anki.stats
from anki.hooks import wrap

import importlib

try:
    from anki.lang import _
except:
    pass


def onMorphManRecalc():
    from .morph import main
    importlib.reload(main)
    main.main()


def onMorphManManager():
    mw.toolbar.draw()
    from .morph import manager
    importlib.reload(manager)
    manager.main()


def onMorphManReadability():
    mw.toolbar.draw()
    from .morph import readability
    importlib.reload(readability)
    readability.main()


def onMorphManPreferences():
    from .morph import preferencesDialog
    importlib.reload(preferencesDialog)
    preferencesDialog.main()

def morphGraphsWrapper(*args, **kwargs):
    from .morph import graphs
    importlib.reload(graphs)
    return graphs.morphGraphs(args, kwargs)


def main():
    # Add MorphMan submenu
    morphmanSubMenu = QMenu("MorphMan", mw)
    mw.form.menuTools.addMenu(morphmanSubMenu)

    # Add recalculate menu button
    a = QAction('&Recalc', mw)
    a.setStatusTip(_("Recalculate all.db, note fields, and new card ordering"))
    a.setShortcut(_("Ctrl+M"))
    a.triggered.connect(onMorphManRecalc)
    morphmanSubMenu.addAction(a)

    # Add gui preferences menu button
    a = QAction('&Preferences', mw)
    a.setStatusTip(_("Change inspected cards, fields and tags"))
    a.setShortcut(_("Ctrl+O"))
    a.triggered.connect(onMorphManPreferences)
    morphmanSubMenu.addAction(a)

    # Add gui manager menu button
    a = QAction('&Database Manager', mw)
    a.setStatusTip(
        _("Open gui manager to inspect, compare, and analyze MorphMan DBs"))
    a.setShortcut(_("Ctrl+D"))
    a.triggered.connect(onMorphManManager)
    morphmanSubMenu.addAction(a)

    # Add readability tool menu button
    a = QAction('Readability &Analyzer', mw)
    a.setStatusTip(_("Check readability and build frequency lists"))
    a.setShortcut(_("Ctrl+A"))
    a.triggered.connect(onMorphManReadability)
    morphmanSubMenu.addAction(a)

    # ToDo: remove this pylint disable. These imports are here because they have Anki
    #   addHooks to initialize the UI. It would be better to initialize all Anki UI
    #   in one single place with explicit call to reveal true intention.
    # pylint: disable=W0611
    from .morph.browser import viewMorphemes
    from .morph.browser import extractMorphemes
    from .morph.browser import batchPlay
    from .morph.browser import massTagger
    from .morph.browser import learnNow
    from .morph.browser import boldUnknowns
    from .morph.browser import browseMorph
    from .morph.browser import alreadyKnownTagger
    from .morph import newMorphHelper
    from .morph import stats


    anki.stats.CollectionStats.easeGraph = \
        wrap(anki.stats.CollectionStats.easeGraph, morphGraphsWrapper, pos="")


main()
