from .morph.util import *
from PyQt5.QtWidgets import *
import importlib

def onMorphManRecalc():
    from .morph import main
    importlib.reload( main )
    main.main()

def onMorphManManager():
    mw.toolbar.draw()
    from .morph import manager
    importlib.reload( manager )
    manager.main()

def onMorphManPreferences():
    from .morph import preferencesDialog
    importlib.reload( preferencesDialog )
    preferencesDialog.main()


def main():
    # Add recalculate menu button
    a = QAction( '&MorphMan Recalc', mw )
    a.setStatusTip(_("Recalculate all.db, note fields, and new card ordering"))
    a.setShortcut(_("Ctrl+M"))
    a.triggered.connect(onMorphManRecalc)
    mw.form.menuTools.addAction( a )

    # Add gui preferences menu button
    a = QAction( 'MorphMan &Preferences', mw )
    a.setStatusTip(_("Change inspected cards, fields and tags"))
    a.setShortcut(_("Ctrl+O"))
    a.triggered.connect(onMorphManPreferences)
    mw.form.menuTools.addAction( a )

    # Add gui manager menu button
    a = QAction( 'MorphMan &Database Manager', mw )
    a.setStatusTip(_("Open gui manager to inspect, compare, and analyze MorphMan DBs"))
    a.triggered.connect(onMorphManManager)
    mw.form.menuTools.addAction( a )


    from .morph.browser import viewMorphemes
    from .morph.browser import extractMorphemes
    from .morph.browser import batchPlay
    from .morph.browser import massTagger
    from .morph.browser import alreadyKnownTagger
    from .morph import newMorphHelper
    from .morph import stats

main()
