#-*- coding: utf-8 -*-

import os, time, datetime, gzip, pickle, stat
from ankiqt import mw
from anki.deck import DeckStorage
from anki.facts import Fact
from anki.cards import Card
from anki.hooks import addHook
from anki.utils import ids2str
from ankiqt.ui.utils import askUser, showText
import morphemes as M

'''Todo:
* notify which decks are being updated and which aren't
'''

rootDeckDbPath = os.path.join( mw.pluginsFolder(),'morph','dbs','deck' )
logPath = os.path.join( mw.pluginsFolder(),'morph','auto.log' )

# Debugging
def printf( msg, parent=None, type="text" ):
    print msg
    showText( msg, parent, type )
def log( msg ):
    txt = '%s: %s' % ( datetime.datetime.now(), msg )
    f = open( logPath, 'a' )
    f.write( txt+'\n' )
    f.close()
    print txt

# Deck load
def getDeck( dpath ):
    if not os.path.exists( dpath ):
        return log( 'deck file not found @ %s' % dpath )
    try:
        return DeckStorage.Deck( dpath )
    except Exception, e:
        if hasattr( e, 'data' ) and e.data.get('type') == 'inuse':
            log( 'deck already open @ %s. skipping' % dpath )
        else:
            printf( '!! deck is corrupted: %s\nException was: %s' % (dpath, e) )

class DeckMgr:
    def __init__( self, deck ):
        self.deck     = deck
        self.deckName = str( deck.name() )
        self.deckPath = str( deck.path )
        self.dbsPath  = rootDeckDbPath + os.sep + self.deckName
        self.cfgPath  = self.dbsPath + os.sep + 'config'
        self.allPath  = self.dbsPath + os.sep + 'all.db'
        self.maturePath  = self.dbsPath + os.sep + 'mature.db'

        self.cfg = {
            'mature threshold':21,
            'learnt threshold':3,
            'morph fields':['Expression'],
        }
        self.loadCfg()
        log( 'Loaded %s' % self.deckName )

    # Config
    def loadCfg( self ):
        try:
            f = gzip.open( self.cfgPath, 'rb' )
            d = pickle.load( f )
            self.cfg.update( d )
            f.close()
            self.saveCfg()
        except IOError:
            log( 'cfg load failed. using defaults' )

    def saveCfg( self ):
        if not os.path.exists( self.dbsPath ):
            os.makedirs( self.dbsPath )
        f = gzip.open( self.cfgPath, 'wb' )
        pickle.dump( self.cfg, f )
        f.close()

    # Clean
    def close( self ):
        self.saveCfg()
        self.deck.close()

    # Analysis
    def getFacts( self ):
        fids = self.deck.s.column0( 'select id from facts' )
        return map( self.deck.s.query( Fact ).get, fids )

    def getCardsForFacts( self, fids ):
        cis = self.deck.s.column0( 'select id from cards where factId in %s' % ids2str(fids) )
        return map( self.deck.s.query( Card ).get, cis )

    # Update DBs
    def mkAll( self ):
        db = M.MorphDb()
        mp = M.mecab()
        for f in self.getFacts():
            mats = [ c.interval for c in self.getCardsForFacts( [f.id] ) ]
            for fieldName in self.cfg['morph fields']:
                ms = M.getMorphemes( mp, f[ fieldName ] )
                loc = M.AnkiDeck( f.id, fieldName, self.deckPath, self.deckName, mats )
                db.addMsL( ms, loc )
        db.save( self.allPath )
        return db

    def getAll( self ):
        if not os.path.exists( self.allPath ):
            return self.mkAll()
        return M.MorphDb( self.allPath )

    def getMature( self ):
        if not self.isUpToDate( self.maturePath ):
            return self.mkMature()
        return M.MorphDb( self.maturePath )

    def mkMature( self ):
        matDb = M.MorphDb()
        for l,ms in self.getAll().ldb().iteritems():
            if l.maturity > self.cfg['mature threshold']:
                matDb.addMsL( ms, l )
        matDb.save( self.maturePath )
        return matDb

    def isUpToDate( self, dbPath ):
        if not os.path.exists( dbPath ): return False
        dbMod = os.stat( dbPath )[ stat.ST_MTIME ]
        if self.deck.modified - dbMod > 0:
            return False
        return True

    def updateEverything( self ):
        log( 'Updating Everything...' )
        aDb = self.getAll()
        log( '  - updated all.db [%d]' % len(aDb.db) )
        mDb = self.getMature()
        log( '  - updated mature.db [%d]' % len(mDb.db)  )
        log( '...done' )

def doDeck( dPath ):
    deck = getDeck( dPath )
    if not deck: return
    d = DeckMgr( deck )
    d.updateEverything()
    d.close()

# main
def main():
    start = time.time()
    deckPaths = mw.config['recentDeckPaths']
    for dpath in deckPaths[:2]:
        doDeck( dpath )
    end = time.time()
    dur = end - start
    log( 'Auto completed in %d sec' % dur )

addHook( 'init', main )
