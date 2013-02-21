# -*- coding: utf-8 -*-
import subprocess, re, urllib, urllib2

#### Get gloss data
def url( term ): return 'http://www.csse.monash.edu.au/~jwb/cgi-bin/wwwjdic.cgi?9ZIH%s' % urllib.quote( term.encode('utf-8') )
def fetchGloss( term ): return urllib.urlopen( url( term ) ).read()
def gloss( expr ):
   if type( expr ) != unicode: expr = unicode( expr )
   print 'glossing:',expr
   x = fetchGloss( expr )
   u = unicode( x, 'utf-8', errors='ignore' )
   ls = re.findall( '<li>(.*?)</li>', u )
   return u'<br>\n'.join( ls )

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from anki.facts import Fact
from ankiqt import mw

mw.registerPlugin( 'jmrGloss', 2011012917 )

#### Update facts with gloss
def glossFact( f ):
   if f[ 'Gloss' ]: return
   f[ 'Gloss' ] = gloss( f['Expression'] )

def setupMenu( ed ):
   a = QAction( 'Regenerate Glosses', ed )
   ed.connect( a, SIGNAL('triggered()'), lambda e=ed: onRegenGlosses( e ) )
   ed.dialog.menuActions.addSeparator()
   ed.dialog.menuActions.addAction( a )

def onRegenGlosses( ed ):
   n = "Regenerate Glosses"
   ed.parent.setProgressParent( ed )
   ed.deck.setUndoStart( n )
   regenGlosses( ed.selectedFacts() )
   ed.deck.setUndoEnd( n )
   ed.parent.setProgressParent( None )
   ed.updateSearch()

def regenGlosses( fids ):
   mw.deck.startProgress( max= len( fids ) )
   for (i,fid) in enumerate( fids ):
      mw.deck.updateProgress( label='Generating glosses...', value=i )
      f = mw.deck.s.query(Fact).get( fid )
      try: glossFact( f )
      except:
         import traceback
         print 'gloss failed:'
         traceback.print_exc()
   try: mw.deck.refreshSession() #mw.deck.refreshReadings()
   except: mw.deck.refresh()
   mw.deck.updateCardQACacheFromIds( fids, type='facts' )
   mw.deck.finishProgress()

addHook( 'editor.setupMenus', setupMenu )
