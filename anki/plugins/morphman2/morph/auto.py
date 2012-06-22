#-*- coding: utf-8 -*-

import os, time, gzip, pickle, threading, ctypes, stat
from anki.deck import DeckStorage
from anki.facts import Fact
from anki.cards import Card
from ankiqt import mw
from anki.hooks import addHook
from anki.utils import deleteTags, addTags, canonifyTags, stripHTML
import morphemes as M
import rankVocab as R
from util import log, debug, matureDbPath, knownDbPath, deckDbPath, deckPaths, sigterm, updater, clearLog
import util

REPEAT_INTERVAL = 10 # sec
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

# custom version that doesn't run deckClosed hook since that has erroneous
# effects in the main thread (like facteditor sets self.fact = None)
def closeDeck( deck ): # Deck -> IO ()
   if deck.s:
      deck.s.rollback()
      deck.s.clear()
      deck.s.close()
   deck.engine.dispose()

# strip html and stuff like that
def normalizeFieldValue( s ):
    s = stripHTML( s )
    return s

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
            'i+N known field':'iPlusN',
            'i+N mature field':'iPlusNmature',
            'unknowns field':'unknowns',
            'unmatures field':'unmatures',
            'vocab rank field':'vocabRank',
            'morph man index field':'morphManIndex',
            'copy i+1 known to':'vocabExpression',
            'copy i+0 mature to':'sentenceExpression',
            'whitelist':u'',
            'blacklist':u'記号,UNKNOWN',
            'enabled':'no',

            # internal
            'last deck update':0, # TimeStamp
            'last deck update took':0, # Seconds
            'last all.db update took':0, # Seconds
            'last db update':{}, # Map DbPath TimeStamp
        }
        self.loadCfg()
        debug( 'Loaded DeckMgr for %s' % self.deckName )

    # Clean
    def close( self ): # m ()
        self.saveCfg()
        deck.close()

    ###########################################################################
    ## Config
    ###########################################################################

    def loadCfg( self ): # m ()
        try:
            f = gzip.open( self.cfgPath, 'rb' )
            d = pickle.load( f )
            f.close()
            self.cfg.update( d )
        except IOError:
            log( 'cfg load failed. using defaults' )
        finally:
            self.saveCfg()

    def saveCfg( self ): # m ()
        if not os.path.exists( self.dbsPath ):
            os.makedirs( self.dbsPath )
        f = gzip.open( self.cfgPath, 'wb' )
        pickle.dump( self.cfg, f )
        f.close()

    ###########################################################################
    ## DBs
    ###########################################################################

    # Update check
    def isDbUpToDate( self, dbPath ): # DbPath -> IO Bool
        if not os.path.exists( dbPath ):
            return False
        lastUpdate = self.cfg['last db update'].get( dbPath, 0 )
        if self.deck.modified > lastUpdate:
            return False
        return True

    # Analysis utils
    def getFacts( self ): # m LazyList Fact
        return self.deck.s.query(Fact).all()

    def fid2cardsDb( self ): # m Map FactId {Card}
        if not hasattr( self, '_fid2cardsDb' ):
            d = self._fid2cardsDb = {}
            for c in self.deck.s.query(Card).all():
                try:
                    d[ c.factId ].append( c )
                except KeyError:
                    d[ c.factId ] = [c]
        return self._fid2cardsDb

    # DB that stores all facts in deck; constructs by making loc->morphs db
    def mkAll( self ): # IO ()
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
        whitelist, blacklist = self.cfg['whitelist'], self.cfg['blacklist']
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
                    fieldValue = normalizeFieldValue( f[ fieldName ] )
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
                        ms = M.getMorphemes( mp, fieldValue, ws=whitelist, bs=blacklist )
                        locDb.pop( loc )
                        locDb[ newLoc ] = ms
                except KeyError: # new location
                    loc = M.AnkiDeck( f.id, fieldName, fieldValue, self.deckPath, self.deckName, mats )
                    ms = M.getMorphemes( mp, fieldValue, ws=whitelist, bs=blacklist )
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

    def allDb( self, doLoad=True ): # Maybe Bool -> IO Maybe Db
        if not self.isDbUpToDate( self.allPath ):
            return self.mkAll()
        if doLoad:
            if not hasattr( self, '_allDb' ):
                self._allDb = M.MorphDb( self.allPath )
            return self._allDb

    # DBs filtered to only morphemes in facts of at least maturity N
    def intervalPath( self, n ): # Interval -> IO Db
        return self.dbsPath + os.sep + 'interval.%d.db' % n
    def mkIntervalDb( self, n ): # Interval -> IO Db
        db = M.MorphDb()
        for l,ms in self.allDb().locDb().iteritems():
            if l.maturity > n:
                db.addMsL( ms, l )
        db.save( self.intervalPath(n) )
        self.cfg['last db update'][ self.intervalPath(n) ] = time.time()
        return db
    def intervalDb( self, n, doLoad=True ): # Int -> Maybe Bool -> IO Maybe Db
        if not self.isDbUpToDate( self.intervalPath(n) ):
            return self.mkIntervalDb( n )
        if doLoad:
            return M.MorphDb( self.intervalPath(n) )
    def deckMatureDb( self, doLoad=True ): # Maybe Bool -> IO Maybe Db
        return self.intervalDb( self.cfg['mature threshold'], doLoad )
    def deckLearntDb( self, doLoad=True ): # Maybe Bool -> IO Maybe Db
        return self.intervalDb( self.cfg['learnt threshold'], doLoad )
    def deckKnownDb( self, doLoad=True ): # Maybe Bool -> IO Maybe Db
        return self.intervalDb( self.cfg['known threshold'], doLoad )

    ###########################################################################
    ## Update deck with DBs
    ###########################################################################

    # known.db and mature.db
    def updateKnownDb( self ): # IO Int
        new = self.delLocsInDb( self.knownDb() ).merge( self.deckKnownDb() )
        if new:
            debug( '  Saving %d modifications to known.db' % new )
            self.knownDb().save( knownDbPath )
        return new

    def updateMatureDb( self ): # IO Int
        new = self.delLocsInDb( self.matureDb() ).merge( self.deckMatureDb() )
        if new:
            debug( ' Saving %d modifications to mature.db' % new )
            self.matureDb().save( matureDbPath )
        return new

    def knownDb( self ): # IO Db
        if not hasattr( self, '_knownDb' ):
            try:
                self._knownDb = M.MorphDb( knownDbPath )
                debug( '  * Loaded existing known.db' )
            except IOError:
                self._knownDb = M.MorphDb()
                self._knownDb.save( knownDbPath )
                debug( '  * Created new known.db' )
        return self._knownDb

    def matureDb( self ): # IO Db
        if not hasattr( self, '_matureDb' ):
            try:
                self._matureDb = M.MorphDb( matureDbPath )
                debug( '  * Loaded existing mature.db' )
            except IOError:
                self._matureDb = M.MorphDb()
                self._matureDb.save( matureDbPath )
                debug( '   * Created new mature.db' )
        return self._matureDb

    def delLocsInDb( self, morphDb ): # Db -> Db
        locDb_ = dict( (loc,ms) for loc,ms in morphDb.locDb().iteritems() if loc.deckName != self.deckName )
        morphDb.clear()
        morphDb.addFromLocDb( locDb_ )
        return morphDb

    # update our dbs via the deck
    def updateDbs( self ): # IO ()
        #NOTE: we (dangerously?) assume that if all.db wasn't updated then known.db doesn't need to be
        log( 'Updating dbs for %s' % self.deckName )
        aDb = self.allDb( doLoad=False )
        if aDb:
            log( '  - updated all.db [%d]' % len(aDb.db) )
            newK = self.updateKnownDb()
            log( '  - updated known.db [%d, +%d]' % ( len(self.knownDb().db), newK ) )
            newM = self.updateMatureDb()
            log( '  - updated mature.db [%d, +%d]' % ( len(self.matureDb().db), newM ) )
        else:
            log( '  - updated all.db [no-op]' )
            log( '  - updated known.db [no-op]' )
            log( '  - updated mature.db [no-op]' )

        for i in self.cfg['interval dbs to make']:
            self.intervalDb( i, doLoad=False )
        log( '  - updated interval dbs' )

    # update our deck via the dbs
    def updateDeck( self ): # IO ()
        log( 'Updating deck for %s' % self.deckName )
        self.allDb( doLoad=False ) # force update for timestamp below to be correct
        knownDbMod = os.stat( knownDbPath )[ stat.ST_MTIME ]
        matureDbMod = os.stat( matureDbPath )[ stat.ST_MTIME ]
        allDbMod = self.cfg['last db update'][ self.allPath ]
        lastMod = max( knownDbMod, matureDbMod, allDbMod )
        if lastMod > self.cfg['last deck update']:
            try:
                self.doDeckUpdate()
                log( '  - updated morph metadata fields' )
            finally:
                self.cfg['last db update'][ self.allPath ] = self.cfg['last deck update']
        else:
            log( '  - updated morph metadata fields [no-op]' )

    def doDeckUpdate( self ): # IO ()
        fidDb = self.allDb().fidDb()
        fid2cardsDb = self.fid2cardsDb()
        locDb = self.allDb().locDb()
        rankDb = R.mkRankDb( self.knownDb() )
        knownDbDb = self.knownDb().db
        matureDbDb = self.matureDb().db
        fs = self.getFacts()

        # cache lookups
        fieldNames = self.cfg['morph fields']
        ipnKnownField = self.cfg['i+N known field']
        ipnMatureField = self.cfg['i+N mature field']
        unknownsField = self.cfg['unknowns field']
        unmaturesField = self.cfg['unmatures field']
        vrField = self.cfg['vocab rank field']
        mmiField = self.cfg['morph man index field']
        ip1knownField = self.cfg['copy i+1 known to']
        ip0matField = self.cfg['copy i+0 mature to']

        i, lfs = 0, len(fs)
        start = time.time()
        fstart = time.time()
        mmiDict = {} # Map Fact -> MorphManIndex
        for f in fs:
            # first get all morphems for this fact
            ms = set()
            for fieldName in fieldNames:
                try:
                    loc = fidDb[ (f.id, fieldName) ]
                    ms.update( locDb[ loc ] )
                except KeyError:
                    continue
            # now determine unknowns and iPlusN - don't count multiple instances
            # of a morpheme as an increase in difficulty, so use a set
            unknowns = set()
            for m in ms:
                if m not in knownDbDb:
                    unknowns.add( m )
            N_k = len( unknowns )

            unmatures = set()
            for m in ms:
                if m not in matureDbDb:
                    unmatures.add( m )
            N_m = len( unmatures )
            # determine vocab rank and morph man overall difficulty index
            vr = R.rankMorphemes( rankDb, ms )
            mmi = N_k*10000 + len(ms)*1000 + vr
	    mmiDict[ f ] = mmi

            try: f[ ipnKnownField ] = u'%d' % N_k
            except KeyError: pass
            try: f[ ipnMatureField ] = u'%d' % N_m
            except KeyError: pass
            try: f[ mmiField ] = u'%d' % mmi
            except KeyError: pass
            try: f[ vrField ] = u'%d' % vr
            except KeyError: pass
            try: f[ unknownsField ] = u','.join( u.base for u in unknowns )
            except KeyError: pass
            try: f[ unmaturesField ] = u','.join( u.base for u in unmatures )
            except KeyError: pass

            if len(ms) == 0:
                f.tags = canonifyTags( addTags( u'noMorphemes', f.tags ) )

            # Help automate vocab card -> sentence card promotion
            try: f[ ip0matField ] = u''
            except KeyError: pass
            try: f[ ip1knownField ] = u''
            except KeyError: pass
            f.tags = canonifyTags( deleteTags( u'ip0mature ip1known notReady', f.tags ) )

            if N_m == 0: # is i+0 mature, make it a sentence card
                f.tags = canonifyTags( addTags( u'ip0mature ip0matureEver', f.tags ) )
                try: f[ ip0matField ] = u' '.join( f[ name ] for name in fieldNames )
                except KeyError: pass
            elif N_k == 1: # is i+1 known, make it a vocab card
                f.tags = canonifyTags( addTags( u'ip1known ip1knownEver', f.tags ) )
                try: f[ ip1knownField ] = u'%s' % unknowns.pop().base
                except KeyError: pass
            else: # is neither, make it a neither card
                f.tags = canonifyTags( addTags( u'notReady', f.tags ) )

            #f.setModified( textChanged=True, deck=self.deck )

            # now display progress
            i += 1
            if i % 100 == 0:
                fend = time.time()
                log('    %d / %d = %d%% in %f sec' % ( i, lfs, 100.*i/lfs, fend-fstart ) )
                fstart = time.time()

        # rebuild tags
        self.deck.updateFactTags( ( f.id for f in fs ) )

        # sort new cards by Morph Man Index
        debug( 'Set fact fields, now changing card creation times for ordering' )
        newtime = 0.0
	try:
            for f in sorted( fs, key=lambda x: mmiDict[ x ] ):
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
            if dm.cfg['enabled'] == 'yes':
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
            if dm.cfg['enabled'] == 'yes':
               dm.updateDeck()
               dm.saveCfg()
        finally:
            closeDeck( deck )
    util.lastUpdate = upDeckTime = time.time()
    log( 'Decks updated in %f' % (upDeckTime-upDbTime) )
    log( 'Full update completed in %d sec' % (upDeckTime-start) )

def asyncRaise( tid, excObjType ): # ThreadId -> ExceptionObjType -> IO ()
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
    util.updater = Updater()
    util.updater.start()

addHook( 'init', main )
