from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from anki.facts import Fact
from ankiqt import mw

import morphemes as m

def export( fids ):
    mw.deck.startProgress( max=len(fids) )

    mp = m.mecab( None ) # expect jap plugin to have already fixed win/osx issues
    ms = []
    for (i, fid) in enumerate( fids ):
        mw.deck.updateProgress( label='Exporting morphemes...', value=i )
        f = mw.deck.s.query( Fact ).get( fid )
        ms.extend( m.getMorphemes( mp, f[ 'Expression' ] ) )

    m.saveDb( m.ms2db( ms ), r'anki.morphdb' )
    mw.deck.finishProgress()

def onExport( ed ):
    txt = 'Analyzing and exporting morphemes'
    ed.parent.setProgressParent( ed )
    ed.deck.setUndoStart( txt )
    export( ed.selectedFacts() )
    ed.deck.setUndoEnd( txt )
    ed.parent.setProgressParent( None )
    ed.updateSearch()

def setupMenu( ed ):
    a = QAction( 'Export Morphemes', ed )
    ed.connect( a, SIGNAL('triggered()'), lambda e=ed: onExport(e) )
    ed.dialog.menuActions.addAction( a )

addHook( 'editor.setupMenus', setupMenu )
