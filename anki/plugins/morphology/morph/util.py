#-*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from anki.facts import Fact
from ankiqt import mw

import datetime, os
import morphemes

VERBOSE = False

logPath = os.path.join( mw.pluginsFolder(),'morph','tests','auto.log' )
dbPath = mw.pluginsFolder() + os.sep + 'morph' + os.sep + 'dbs' + os.sep
knownDbPath = os.path.join( mw.pluginsFolder(),'morph','dbs','known.db' )
deckDbPath = os.path.join( mw.pluginsFolder(),'morph','dbs','deck' )
deckPaths = mw.config['recentDeckPaths']
updater = None # updater thread

def sigterm( p ):
   try: p.terminate()
   except AttributeError: pass
def killMecab( st ): sigterm( st['mp'] )

def getBlacklist( ed, default=u'記号,助詞' ):
   bs, ok = QInputDialog.getText( ed, 'Comma delimited', 'Blacklist parts of speech', QLineEdit.Normal, default )
   if not ok: bs = default
   return bs.split(',')

def requireKnownDb(): # returns false if failed
   global knownDbPath
   if os.path.exists( knownDbPath ): return True
   knownDbPath = QFileDialog.getOpenFileName( caption="Can't find known morphemes db", directory=knownDbPath )
   if not knownDbPath:
      QMessageBox.critical( None, 'ERROR!', 'Cannot proceed without a known morphemes db' )
      return False
   return True

################################################################################
## Log / inform system
################################################################################
def errorMsg( txt, cap='Error', p=mw ): return QMessageBox.critical( p, cap, txt )
def infoMsg( txt, cap='Note', p=mw ): return QMessageBox.information( p, cap, txt )

def debug( msg ):
    if VERBOSE: log( msg )

def log( msg ):
    txt = '%s: %s' % ( datetime.datetime.now(), msg )
    f = open( logPath, 'a' )
    f.write( txt+'\n' )
    f.close()
    print txt

def clearLog():
   f = open( logPath, 'w' )
   f.close()

################################################################################
## GUI helpers
################################################################################
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
