from morph.util import *

def onMorphMan():
    import morph.main
    reload( morph.main )
    morph.main.main()

# Add menu button
a = QAction( 'MorphMan', mw )
s = QShortcut( QKeySequence( 'Ctrl+m' ), mw )
mw.connect( a, SIGNAL('triggered()'), onMorphMan )
mw.connect( s, SIGNAL('activated()'), onMorphMan )
mw.form.menuTools.addAction( a )

'''
#from morph.util import mw, addHook, wrap, printf, info
from anki.lang import _
from aqt.toolbar import Toolbar
# Add toolbar button
mw.toolbar.rightIcons.append(
        ["morphman", "qrc:/icons/view-statistics.png",
            _("Run MorphMan. Shortcut key: %s") % "M"]
    )
def _linkHandler( self, l ):
    from morph.util import printf
    printf( '_linkHandler' )
    info( '_linkHandler' )
    if l == 'morphman':
        onMorphMan()

mw.toolbar._linkHandler = wrap( mw.toolbar._linkHandler, _linkHandler )
'''
