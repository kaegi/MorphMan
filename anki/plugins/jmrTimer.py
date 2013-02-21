#!/usr/bin/env python
from ankiqt import mw
from ankiqt.ui.main import AnkiQt
from anki.hooks import wrap
from anki import sound
import os
from threading import Timer

d = { 6.0:'SuperMarioBrothers-OutOfTime.mp3'
    , 10.0:'GameshowBellDing3.mp3'
    }
basePath = mw.pluginsFolder() + os.sep + 'timerSounds'
ts = []

# :: FilePath -> Audio ()
def play( sPath ):
   path = basePath + os.sep + sPath
   path = path.replace( os.sep, os.sep*2 ) # fix for windows
   print 'playing:', path
   sound.play( path )

# :: AnkiQt -> Response -> m ()
def onPreCardAnswered( self, r ):
   print 'resetting timers'
   global ts
   [ t.cancel() for t in ts ]
   ts = [ Timer( dur, play, args=[path] ) for dur,path in d.items() ]
   [ t.start() for t in ts ]

AnkiQt.cardAnswered = wrap(AnkiQt.cardAnswered, onPreCardAnswered, pos="before")
mw.registerPlugin( 'jmrTimer', 2011012918 )
