#-*- coding: utf-8 -*-

import os, time, gzip, pickle, threading, ctypes
from anki.deck import DeckStorage
from anki.facts import Fact
from anki.cards import Card
from ankiqt import mw
from anki.hooks import addHook
import morphemes as M
import rankVocab as R
from util import log, debug, knownDbPath, deckDbPath, deckPaths, sigterm, updater, clearLog

REPEAT_INTERVAL = 5 # sec
CARD_CREATION_TIME_INC = 10

#TODOS:
# gui for configuration and checking last sync
# more morphs before schema freeze?

# Deck load
def getDeck( dpath ): # AnkiDeckPath -> Maybe Deck
    if not os.path.exists( dpath ):
        return log( '! deck file not found @ %s' % dpath )
    try:
        return DeckStorage.Deck( dpath )
    except Exception, e:
        if hasattr( e, 'data' ) and e.data.get('type') == 'inuse':
            log( '! deck already open @ %s. skipping' % dpath )
        else:
            log( '!!! deck is corrupted: %s\nException was: %s' % (dpath, e) )

# custom version that doesn't run deckClosed hook since that has erroneous effects
# in the main thread (like facteditor sets self.fact = None)
def closeDeck( deck ):
   if deck.s:
      deck.s.rollback()
      deck.s.clear()
      deck.s.close()
   deck.engine.dispose()

class DeckMgr:
    def __init__( self, deck ):
        self.deck     = deck
        self.deckName = str( deck.name() )
        self.deckPath = str( deck.path )
        self.dbsPath  = deckDbPath + os.sep + self.deckName
        self.cfgPath  = self.dbsPath + os.sep + 'config'
        self.allPath  = self.dbsPath + os.sep + 'all.db'

        self.cfg = {
            # user configurable
            'mature threshold':21,
            'learnt threshold':3,
            'known threshold':3,
            'interval dbs to make':range(1,21)+[30,100,365],
            'morph fields':['Expression'],
            'i+N field':'iPlusN',
            'unknowns field':'unknowns',
            'vocab rank field':'vocabRank',
            'morph man index field':'morphManIndex',

            # internal
            'last deck update':0, # TimeStamp
            'last deck update took':0, # Seconds
            'last all.db update took':0, # Seconds
            'last db update':{}, # Map DbPath TimeStamp
        }
        self.loadCfg()
        debug( 'Loaded DeckMgr for %s' % self.deckName )

    # Clean
    def close( self ):
        self.saveCfg()
        deck.close()

    ###########################################################################
    ## Config
    ###########################################################################

    def loadCfg( self ):
        try:
            f = gzip.open( self.cfgPath, 'rb' )
            d = pickle.load( f )
            f.close()

            self.cfg.update( d )
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
    def isDbUpToDate( self, dbPath ):
        if not os.path.exists( dbPath ):
            return False
        lastUpdate = self.cfg['last db update'].get( dbPath, 0 )
        if self.deck.modified > lastUpdate:
            return False
        return True

    # Analysis utils
    def getFacts( self ):
        return self.deck.s.query(Fact).all()

    def fid2cardsDb( self ):
        if not hasattr( self, '_fid2cardsDb' ):
            d = self._fid2cardsDb = {}
            for c in self.deck.s.query(Card).all():
                try:
                    d[ c.factId ].append( c )
                except KeyError:
                    d[ c.factId ] = [c]
        return self._fid2cardsDb

    # DB that stores all facts in deck
    def mkAll( self ): # uses cache, constructs by making a loc->morphs db
        log( 'Getting initial all.db...' )
        if not hasattr( self, '_allDb' ):
            try:
                self._allDb = M.MorphDb( self.allPath )
                debug( '  * Updating existing all.db' )
            except IOError:
                self._allDb = M.MorphDb()
                debug( '  * Creating new all.db from scratch' )
        allDb = self._allDb
        log( '...done' )

        mp = M.mecab()

        # pre-cache lookups
        fieldNames = self.cfg['morph fields']
        fid2cardsDb = self.fid2cardsDb()
        fidDb = allDb.fidDb()
        locDb = allDb.locDb()
        fs = self.getFacts()

        i, lfs = 0, len( fs )
        start = time.time()
        last = time.time()
        for f in fs:
            mats = [ c.interval for c in fid2cardsDb[ f.id ] ]
            for fieldName in fieldNames:
                try:
                    fieldValue = f[ fieldName ]
                except KeyError: # if fact doesn't have the field just skip it
                    continue
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
                        debug('        .morphs for %d[%s]' % ( f.id, fieldName ) )
                        newLoc = M.AnkiDeck( f.id, fieldName, fieldValue, self.deckPath, self.deckName, mats )
                        ms = M.getMorphemes( mp, fieldValue )
                        locDb.pop( loc )
                        locDb[ newLoc ] = ms
                except KeyError: # new location
                    loc = M.AnkiDeck( f.id, fieldName, fieldValue, self.deckPath, self.deckName, mats )
                    ms = M.getMorphemes( mp, fieldValue )
                    if ms:
                        debug('        .loc for %d[%s]' % ( f.id, fieldName ) )
                        locDb[ loc ] = ms
            i += 1
            if i % 100 == 0:
                log('    %d / %d = %d%% in %f sec' % ( i, lfs, 100.*i/lfs, time.time()-last ) )
                last = time.time()
        log( 'Proccessed all facts in %f sec. Now saving...' % ( time.time()-start ) )
        allDb.clear()
        allDb.addFromLocDb( locDb )
        allDb.save( self.allPath )
        self.cfg['last db update'][ self.allPath ] = time.time()
        self.cfg['last all.db update took'] = time.time() - start
        log( '...done' )
        sigterm( mp )
        return self._allDb

    def allDb( self, doLoad=True ): # Maybe Bool -> m Maybe Db
        if not self.isDbUpToDate( self.allPath ):
            return self.mkAll()
        if doLoad:
            if not hasattr( self, '_allDb' ):
                self._allDb = M.MorphDb( self.allPath )
            return self._allDb

    # DBs filtered to only morphemes in facts of at least maturity N
    def intervalPath( self, n ):
        return self.dbsPath + os.sep + 'interval.%d.db' % n
    def mkIntervalDb( self, n ):
        db = M.MorphDb()
        for l,ms in self.allDb().locDb().iteritems():
            if l.maturity > n:
                db.addMsL( ms, l )
        db.save( self.intervalPath(n) )
        self.cfg['last db update'][ self.intervalPath(n) ] = time.time()
        return db
    def intervalDb( self, n, doLoad=True ): # Int -> Maybe Bool -> m Maybe Db
        if not self.isDbUpToDate( self.intervalPath(n) ):
            return self.mkIntervalDb( n )
        if doLoad:
            return M.MorphDb( self.intervalPath(n) )
    def deckMatureDb( self, doLoad=True ):
        return self.intervalDb( self.cfg['mature threshold'], doLoad )
    def deckLearntDb( self, doLoad=True ):
        return self.intervalDb( self.cfg['learnt threshold'], doLoad )
    def deckKnownDb( self, doLoad=True ):
        return self.intervalDb( self.cfg['known threshold'], doLoad )

    ###########################################################################
    ## Update deck with DBs
    ###########################################################################

    # known.db
    def addToKnownDb( self ):
        self.knownDb().merge( self.deckKnownDb() )
        self.knownDb().save( knownDbPath )

    def knownDb( self ):
        if not hasattr( self, '_knownDb' ):
            try:
                self._knownDb = M.MorphDb( knownDbPath )
                debug( '  * Loaded existing known.db' )
            except IOError:
                self._knownDb = M.MorphDb()
                self._knownDb.save( knownDbPath )
                debug( '  * Created new known.db' )
        return self._knownDb

    # update our dbs via the deck
    def updateDbs( self ):
        #NOTE: we (dangerously?) assume that if all.db wasn't updated then known.db doesn't need to be
        log( 'Updating dbs for %s' % self.deckName )
        aDb = self.allDb( doLoad=False )
        if aDb:
            log( '  - updated all.db [%d]' % len(aDb.db) )
            self.addToKnownDb()
            log( '  - updated known.db [%d]' % len(self.knownDb().db) )
        else:
            log( '  - updated all.db [no-op]' )
            log( '  - updated known.db [no-op]' )

        for i in self.cfg['interval dbs to make']:
            self.intervalDb( i, doLoad=False )
        log( '  - updated interval dbs' )

    # update our deck via the dbs
    def updateDeck( self ):
        log( 'Updating deck for %s' % self.deckName )
        self.allDb( doLoad=False ) # force update for timestamp below to be correct
        if self.cfg['last db update'][ self.allPath ] > self.cfg['last deck update']:
            try:
                self.doDeckUpdate()
                log( '  - updated morph metadata fields' )
            finally:
                self.cfg['last db update'][ self.allPath ] = self.cfg['last deck update']
        else:
            log( '  - updated morph metadata fields [no-op]' )

    def doDeckUpdate( self ):
        fidDb = self.allDb().fidDb()
        fid2cardsDb = self.fid2cardsDb()
        locDb = self.allDb().locDb()
        rankDb = R.mkRankDb( self.knownDb() )
        knownDbDb = self.knownDb().db
        fs = self.getFacts()

        # cache lookups
        fieldNames = self.cfg['morph fields']
        ipnField = self.cfg['i+N field']
        unknownsField = self.cfg['unknowns field']
        vrField = self.cfg['vocab rank field']
        mmiField = self.cfg['morph man index field']

        i, lfs = 0, len(fs)
        start = time.time()
        fstart = time.time()
        for f in fs:
            # first get all morphems for this fact
            ms = set()
            for fieldName in fieldNames:
                try:
                    loc = fidDb[ (f.id, fieldName) ]
                    ms.update( locDb[ loc ] )
                except KeyError:
                    continue
            # now determine unknowns and iPlusN
            unknowns, N = set(), 0
            for m in ms:
                if m not in knownDbDb:
                    N += 1
                    unknowns.add( m )
            # determine vocab rank and morph man overall difficulty index
            vr = R.rankMorphemes( rankDb, ms )
            mmi = N*10000 + len(ms)*1000 + vr

            try: f[ ipnField ] = u'%d' % N
            except KeyError: pass
            try: f[ mmiField ] = u'%d' % mmi
            except KeyError: pass
            try: f[ vrField ] = u'%d' % vr
            except KeyError: pass
            try: f[ unknownsField ] = u','.join( u.base for u in unknowns )
            except KeyError: pass

            # now display progress
            i += 1
            if i % 100 == 0:
                fend = time.time()
                log('    %d / %d = %d%% in %f sec' % ( i, lfs, 100.*i/lfs, fend-fstart ) )
                fstart = time.time()

        debug( 'Set fact fields, now changing card creation times for ordering' )
        newtime = 0.0
        try:
            for f in sorted( fs, key=lambda x: int(x[ mmiField ]) ):
                for c in fid2cardsDb[ f.id ]:
                    c.created = newtime
                    newtime += CARD_CREATION_TIME_INC
        except KeyError:
            log( '! no morph man index field for sorting' )

        # save deck and timestamps
        self.deck.save()
        end = time.time()
        log( 'Proccessed all facts in %f sec' % ( end-start ) )
        self.cfg['last deck update'] = time.time()
        self.cfg['last deck update took'] = end-start


################################################################################
## Main
################################################################################

def run():
    start = time.time()
    # update DBs
    for dPath in deckPaths:
        deck = getDeck( dPath )
        if not deck: continue
        try:
            dm = DeckMgr( deck )
            dm.updateDbs()
            dm.saveCfg()
        finally:
            closeDeck( deck )
    upDbTime = time.time()
    log( 'Dbs updated in %f' % (upDbTime-start) )

    # update decks
    for dPath in deckPaths:
        deck = getDeck( dPath )
        if not deck: continue
        try:
            dm = DeckMgr( deck )
            dm.updateDeck()
            dm.saveCfg()
        finally:
            closeDeck( deck )
    upDeckTime = time.time()
    log( 'Decks updated in %f' % (upDeckTime-upDbTime) )
    log( 'Full update completed in %d sec' % (upDeckTime-start) )

def asyncRaise( tid, excObjType ): # ThreadId -> ExceptionObjType
   res = ctypes.pythonapi.PyThreadState_SetAsyncExc( tid, ctypes.py_object( excObjType ) )
   if res == 0:
      raise ValueError( 'Non-existent thread id' )
   elif res > 1:
      ctypes.pythonapi.PyThreadState_SetAsyncExc( tid, 0 )
      raise SystemError( 'PyThreadState_SetAsyncExc failed' )

class Updater( threading.Thread ):
    def __init__( self ):
        threading.Thread.__init__( self )
        self.daemon = True

    def term( self ):
        if not self.isAlive():
            raise threading.ThreadError( 'Thread not active' )
        asyncRaise( self.ident, SystemExit )

    def run( self ):
        while True:
            time.sleep( REPEAT_INTERVAL )
            run()

def main():
    clearLog()

    # run forever in background daemon thread
    u = Updater()
    global updater
    updater = u
    u.start()

addHook( 'init', main )
