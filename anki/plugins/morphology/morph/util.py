#-*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from anki.facts import Fact
from ankiqt import mw

import os
import morphemes

dbPath = mw.pluginsFolder() + os.sep + 'morph' + os.sep + 'dbs' + os.sep
knownDbPath = dbPath + 'known.db'

def killMecab( st ):
   try: st['mp'].kill()
   except: pass

def getBlacklist( ed, default=u'記号,助詞' ):
   bs, ok = QInputDialog.getText( ed, 'Comma delimited', 'Blacklist parts of speech', QLineEdit.Normal, default )
   if not ok: bs = default
   return bs.split(',')

def errorMsg( txt, cap='Error', p=mw ): return QMessageBox.critical( p, cap, txt )
def infoMsg( txt, cap='Note', p=mw ): return QMessageBox.information( p, cap, txt )

def requireKnownDb(): # returns false if failed
   global knownDbPath
   if os.path.exists( knownDbPath ): return True
   knownDbPath = QFileDialog.getOpenFileName( caption="Can't find known morphemes db", directory=knownDbPath )
   if not knownDbPath:
      QMessageBox.critical( None, 'ERROR!', 'Cannot proceed without a known morphemes db' )
      return False
   return True

def doOnSelection( ed, overviewMsg, progMsg, preF, perF, postF ):
   # init
   st = preF( ed )
   if st == 'BAIL': return
   ed.parent.setProgressParent( ed )
   ed.deck.setUndoStart( overviewMsg )
   fids = ed.selectedFacts()
   mw.deck.startProgress( max=len(fids) )

   # payload
   for (i, fid) in enumerate( fids ):
      mw.deck.updateProgress( label=progMsg, value=i )
      f = mw.deck.s.query( Fact ).get( fid )
      st = perF( st, f )

   # cleanup
   mw.deck.finishProgress()
   ed.deck.setUndoEnd( overviewMsg )
   ed.parent.setProgressParent( None )
   postF( st )
   ed.updateSearch()

parentMenu = None

def addDoOnSelectionBtn( btnTxt, overviewMsg, progMsg, preF, perF, postF, shortcut=None ):
   def setupMenu( ed ):
      a = QAction( btnTxt, ed )
      if shortcut: a.setShortcut( shortcut )
      ed.connect( a, SIGNAL('triggered()'), lambda e=ed: doOnSelection( e, overviewMsg, progMsg, preF, perF, postF ) )
      if not parentMenu: setupParentMenu( ed )
      parentMenu.addAction( a )
   addHook( 'editor.setupMenus', setupMenu )

def setupParentMenu( ed ):
    global parentMenu
    parentMenu = ed.dialog.menuActions.addMenu( "It's morphin time" )
addHook( 'editor.setupMenus', setupParentMenu )
