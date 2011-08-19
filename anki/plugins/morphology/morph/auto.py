#-*- coding: utf-8 -*-

import os
from ankiqt import mw
from anki.deck import DeckStorage

deckDbPath = os.sep.join([ mw.pluginsFolder,'morph','dbs','deck' ])

def edeck( dpath ):
    if not os.path.exists( dpath ):
        print '!! deck file not found:', dpath
        return False
    try:
        d = DeckStorage.Deck( dpath )
        d.close()
    except Exception, e:
        if hasattr( e, 'data' ) and e.data.get('type') == 'inuse':
            print '!! deck already open:', dpath
        else:
            print '!! deck is corrupted:', dpath, e

deckPaths = mw.config['recentDeckPaths']
for dpath in deckPaths:
    edeck( dpath )
