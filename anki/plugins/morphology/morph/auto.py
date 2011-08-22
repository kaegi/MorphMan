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

knownDbPath = os.path.join( mw.pluginsFolder(),'morph','dbs','known.db' )
rootDeckDbPath = os.path.join( mw.pluginsFolder(),'morph','dbs','deck' )
logPath = os.path.join( mw.pluginsFolder(),'morph','tests','auto.log' )
VERBOSE = False

# Debugging
def printf( msg, parent=None, type="text" ):
    log( msg )
    showText( msg )

def debug( msg ):
    if VERBOSE: log( msg )

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

        self.cfg = {
            'mature threshold':21,
            'learnt threshold':3,
            'known threshold':3,
            'interval dbs to make':range(1,21)+[30,100,365],
            'morph fields':['Expression'],
            'last update':{}, # Map dbPath modTime
        }
        self.loadCfg()
        log( 'Loaded DeckMgr for %s' % self.deckName )

    # Clean
    def close( self ):
        self.saveCfg()
        self.deck.close()

    ###########################################################################
    ## Config
    ###########################################################################

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

    ###########################################################################
    ## DBs
    ###########################################################################

    # Update check
    def isUpToDate( self, dbPath ):
        if not os.path.exists( dbPath ):
            return False
        lastUpdate = self.cfg['last update'].get( dbPath, 0 )
        if self.deck.modified > lastUpdate:
            return False
        return True

    # Analysis utils
    def getFacts( self ):
        return self.deck.s.query(Fact).all()

    def mkFid2CardsDb( self ):
        d = self.fid2cardsDb = {}
        for c in self.deck.s.query(Card).all():
            try:
                d[ c.factId ].append( c )
            except KeyError:
                d[ c.factId ] = [c]

    # DB that stores all facts in deck
    def mkAll( self ): # uses cache, constructs by making a loc->morphs db
        log( 'Getting initial all.db...' )
        if not hasattr( self, 'allDb' ):
            try:
                self.allDb = M.MorphDb( self.allPath )
                debug( '  * Updating existing all.db' )
            except IOError:
                self.allDb = M.MorphDb()
                debug( '  * Creating new all.db from scratch' )
        allDb = self.allDb
        log( '...done' )

        self.mkFid2CardsDb()
        mp = M.mecab()

        # pre-cache lookups
        fieldNames = self.cfg['morph fields']
        fid2cardsDb = self.fid2cardsDb
        fidDb = allDb.fidDb()
        locDb = allDb.locDb()
        fs = self.getFacts()

        i, lfs = 0, len( fs )
        start = time.time()
        fstart = time.time()
        for f in fs:
            mats = [ c.interval for c in fid2cardsDb[ f.id ] ]
            for fieldName in fieldNames:
                fieldValue = f[ fieldName ]
                try: # existing location
                    loc = fidDb[ (f.id, fieldName) ]
                    # new loc only; no morpheme change
                    if loc.fieldValue == fieldValue and loc.maturities != mats:
                        debug('        .mats for %d[%s]' % ( f.id, fieldName ) )
                        newLoc = M.AnkiDeck( f.id, fieldName, fieldValue, self.deckPath, self.deckName, mats )
                        ms = locDb.pop( loc )
                        locDb[ newLoc ] = ms
                    # new loc and new morphemes
                    elif loc.fieldValue != fieldValue:
                        debug('        !morphs for %d[%s]' % ( f.id, fieldName ) )
                        newLoc = M.AnkiDeck( f.id, fieldName, fieldValue, self.deckPath, self.deckName, mats )
                        ms = M.getMorphemes( mp, fieldValue )
                        locDb.pop( loc )
                        locDb[ newLoc ] = ms
                except KeyError: # new location
                    debug('        !loc for %d[%s]' % ( f.id, fieldName ) )
                    loc = M.AnkiDeck( f.id, fieldName, fieldValue, self.deckPath, self.deckName, mats )
                    ms = M.getMorphemes( mp, fieldValue )
                    locDb[ loc ] = ms
            i += 1
            if i % 100 == 0:
                fend = time.time()
                log('    %d / %d = %d%% in %f sec' % ( i, lfs, 100.*i/lfs, fend-fstart ) )
                fstart = time.time()
        end = time.time()
        log( 'Proccessed all facts in %f sec. Now saving...' % ( end-start ) )
        allDb.clear()
        allDb.addFromLocDb( locDb )
        allDb.save( self.allPath )
        self.cfg['last update'][ self.allPath ] = time.time()
        log( '...done' )
        return self.allDb

    def getAll( self ):
        if not self.isUpToDate( self.allPath ):
            return self.mkAll()
        if not hasattr( self, 'allDb' ):
            self.allDb = M.MorphDb( self.allPath )
        return self.allDb

    # DBs filtered to only morphemes in facts of at least maturity N
    def intervalPath( self, n ):
        return self.dbsPath + os.sep + 'interval.%d.db' % n
    def mkInterval( self, n ):
        db = M.MorphDb()
        for l,ms in self.getAll().locDb().iteritems():
            if l.maturity > n:
                db.addMsL( ms, l )
        db.save( self.intervalPath(n) )
        self.cfg['last update'][ self.intervalPath(n) ] = time.time()
        return db
    def getInterval( self, n ):
        if not self.isUpToDate( self.intervalPath(n) ):
            return self.mkInterval( n )
        return M.MorphDb( self.intervalPath(n) )
    def getMature( self ):
        return self.getInterval( self.cfg['mature threshold'] )
    def getLearnt( self ):
        return self.getInterval( self.cfg['learnt threshold'] )
    def getKnown( self ):
        return self.getInterval( self.cfg['known threshold'] )

    ###########################################################################
    ## Update deck with DBs
    ###########################################################################

    def updateKnown( self ):
        if not hasattr( self, 'knownDb' ):
            try:
                self.knownDb = M.MorphDb( knownDbPath )
                debug( '  * Loading existing known.db' )
            except IOError:
                self.knownDb = M.MorphDb()
                debug( '  * Creating new known.db' )
        self.knownDb.merge( self.getKnown() )
        self.knownDb.save( knownDbPath )

    def updateEverything( self ):
        log( 'Updating everything for %s' % self.deckName )
        aDb = self.getAll()
        log( '  - updated all.db [%d]' % len(aDb.db) )

        self.updateKnown()
        log( '  - updated known.db [%d]' % len(self.knownDb.db) )

        for i in self.cfg['interval dbs to make']:
            self.getInterval( i )
        log( '  - updated interval dbs' )
        log( 'DONE' )

def doDeck( dPath ):
    deck = getDeck( dPath )
    if not deck: return
    d = DeckMgr( deck )
    log('is all.db up to date? %s' % d.isUpToDate( d.allPath ) )
    d.updateEverything()
    d.close()

# main
def main():
    start = time.time()
    deckPaths = mw.config['recentDeckPaths']
    for dpath in deckPaths:
        doDeck( dpath )
    end = time.time()
    dur = end - start
    log( 'completed in %d sec' % dur )

addHook( 'init', main )
