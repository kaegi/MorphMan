from morph.util import *

def onMorphManRecalc():
    import morph.main
    reload( morph.main )
    morph.main.main()

def onMorphManManager():
    mw.toolbar.draw()
    import morph.manager
    reload( morph.manager )
    morph.manager.main()

def main():
    # Add recalculate menu button
    a = QAction( '&MorphMan Recalc', mw )
    a.setStatusTip(_("Recalculate all.db, note fields, and new card ordering"))
    a.setShortcut(_("Ctrl+M"))
    mw.connect( a, SIGNAL('triggered()'), onMorphManRecalc )
    mw.form.menuTools.addAction( a )

    # Add gui manager menu button
    a = QAction( 'MorphMan Manager', mw )
    a.setStatusTip(_("Open gui manager to inspect, compare, and analyze MorphMan DBs"))
    mw.connect( a, SIGNAL('triggered()'), onMorphManManager )
    mw.form.menuTools.addAction( a )


    import morph.viewMorphemes
    import morph.extractMorphemes
    import morph.batchPlay
    import morph.newMorphHelper
    import morph.stats
    import morph.massTagger

main()
