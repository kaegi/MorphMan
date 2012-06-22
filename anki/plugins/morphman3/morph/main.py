from util import printf, info, mw, memoize, cfg, clearLog
from anki.utils import splitFields, joinFields, stripHTML, intTime, fieldChecksum
import morph.morphemes as M
from morph.morphemes import MorphDb, AnkiDeck, getMorphemes, mecab, ms2str
import os, sys, time

'''TODO:
* deck/model specific cfg + disable option
* port over old lesser features (manager, morph match, manual extract, etc)
'''

@memoize
def getFieldIndex( fieldName, mid ):
    m = mw.col.models.get( mid )
    d = dict( ( f['name'], f['ord'] ) for f in m['flds'] )
    try: return d[ fieldName ]
    except KeyError: return None

def getMecabField( fname, flds, mid ):
    idx = getFieldIndex( fname, mid )
    return stripHTML( splitFields( flds )[ idx ] )

@memoize
def getSortFieldIndex( mid ):
    return mw.col.models.get( mid )[ 'sortf' ]

def setField( mid, fs, k, v ): # nop if field DNE
    idx = getFieldIndex( k, mid )
    if idx: fs[ idx ] = v

def mkAllDb( allDb=None ):
    t_0, db, TAG = time.time(), mw.col.db, mw.col.tags

    if not allDb: allDb = MorphDb()
    fidDb, locDb = allDb.fidDb(), allDb.locDb()
    N_notes = db.scalar( 'select count() from notes' )
    mp = mecab()

    for ( nid, mid, flds, guid ) in db.execute( 'select id, mid, flds, guid from notes' ):
        mats = db.list( 'select ivl from cards where nid = :nid', nid=nid )
        for fieldName in cfg['morph_fields']:
            try: # if doesn't have field, continue
                #fieldValue = normalizeFieldValue( getField( fieldName, flds, mid ) )
                fieldValue = getMecabField( fieldName, flds, mid )
            except KeyError: continue

            loc = fidDb.get( ( nid, guid, fieldName ), None )
            if not loc:
                loc = AnkiDeck( nid, fieldName, fieldValue, guid, mats )
                ms = getMorphemes( mp, fieldValue )
                if ms: #TODO: this needed? should we change below too then?
                    #printf( '    .loc for %d[%s]' % ( nid, fieldName ) )
                    locDb[ loc ] = ms
            else:
                # mats changed -> new loc (new mats), move morphs
                if loc.fieldValue == fieldValue and loc.maturities != mats:
                    printf( '    .mats for %d[%s]' % ( nid, fieldName ) )
                    newLoc = AnkiDeck( nid, fieldName, fieldValue, guid, mats )
                    locDb[ newLoc ] = locDb.pop( loc )
                # field changed -> new loc, new morphs
                elif loc.fieldValue != fieldValue:
                    printf( '    .morphs for %d[%s]' % ( nid, fieldName ) )
                    newLoc = AnkiDeck( nid, fieldName, fieldValue, guid, mats )
                    ms = getMorphemes( mp, fieldValue )
                    locDb.pop( loc )
                    locDb[ newLoc ] = ms
    mp.kill()
    printf( 'Processed all %d notes in %f sec' % ( N_notes, time.time() - t_0 ) )
    allDb.clear()
    allDb.addFromLocDb( locDb )
    allDb.save( cfg['path_all'] )
    return allDb

def filterDbByMat( db, mat ):
    db = MorphDb()
    for loc, ms in db.locDb().iteritems():
        if loc.maturity > mat:
            db.addMsL( ms, loc )
    return db

def updateNotes( allDb ):
    t_0, now, db, TAG   = time.time(), intTime(), mw.col.db, mw.col.tags
    ds, nid2mmi         = [], {}
    fidDb, locDb, popDb = allDb.fidDb(), allDb.locDb(), allDb.popDb()
    seenDb      = filterDbByMat( allDb, cfg['threshold_seen'] )
    knownDb     = filterDbByMat( allDb, cfg['threshold_known'] )
    matureDb    = filterDbByMat( allDb, cfg['threshold_mature'] )

    pops = [ len( locs ) for locs in allDb.db.values() ]
    pops = [ n for n in pops if n > 1 ]

    for ( nid, mid, flds, guid, tags ) in db.execute( 'select id, mid, flds, guid, tags from notes' ):
        # Get all morphemes for note
        ms = set()
        for fieldName in cfg['morph_fields']:
            try:
                loc = fidDb[ ( nid, guid, fieldName ) ]
                ms.update( locDb[ loc ] )
            except KeyError: continue
        ms = [ m for m in ms if m.pos not in cfg['morph_blacklist'] ]

        # Determine un-seen/known/mature and i+N
        unseens, unknowns, unmatures = set(), set(), set()
        for m in ms:
            if m not in seenDb.db:      unseens.add( m )
            if m not in knownDb.db:     unknowns.add( m )
            if m not in matureDb.db:    unmatures.add( m )

        # Determine MMI - Morph Man Index
        N, N_s, N_k, N_m = len( ms ), len( unseens ), len( unknowns ), len( unmatures )
            # average frequency of unknowns (how common and thus useful to learn)
        F_k = 0
        for focusMorph in unknowns: # focusMorph used outside loop
            F_k += len( allDb.db[ focusMorph ] )
        F_k_avg = F_k / N_k if N_k > 0 else F_k
        freq = 999 - min( 999, F_k_avg )
            # difference from optimal length (too little context vs long sentence)
        lenDiff = min( 9, abs( 4 - N ) )
            # calculate mmi
        mmi = 10000*N_k + 1000*lenDiff + freq
        nid2mmi[ nid ] = mmi

        # Fill in various fields/tags on the note based on cfg?
        ts, fs = TAG.split( tags ), splitFields( flds )
            # determine card type
        if N_m == 0:    # sentence comprehension card
            ts = [ u'comprehension' ] + [ t for t in ts if t not in [ u'vocab', u'notReady' ] ]
            setField( mid, fs, 'focusMorph', u'' )
        elif N_k == 1:  # new vocab card
            ts = [ u'vocab' ] + [ t for t in ts if t not in [ u'notReady' ] ]
            setField( mid, fs, 'focusMorph', u'%s' % focusMorph.base )
        elif N_k > 1:   # M+1+ K+2+
            ts.append( u'notReady' )
            # set type agnostic fields
        setField( mid, fs, 'k+N', u'%d' % N_k )
        setField( mid, fs, 'm+N', u'%d' % N_m )
        setField( mid, fs, 'morphManIndex', u'%d' % mmi )
        setField( mid, fs, 'unknowns', u', '.join( u.base for u in unknowns ) )
        setField( mid, fs, 'unmatures', u', '.join( u.base for u in unmatures ) )
        setField( mid, fs, 'unknownFreq', u'%d' % F_k_avg )
            # update sql db
        tags_ = TAG.join( TAG.canonify( ts ) )
        flds_ = joinFields( fs )
        csum = fieldChecksum( fs[0] )
        sfld = stripHTML( fs[ getSortFieldIndex( mid ) ] )
        ds.append( { 'now':now, 'tags':tags_, 'flds':flds_, 'sfld':sfld, 'csum':csum, 'usn':mw.col.usn(), 'nid':nid } )

    mw.col.db.executemany( 'update notes set tags=:tags, flds=:flds, sfld=:sfld, csum=:csum, mod=:now, usn=:usn where id=:nid', ds )
    TAG.register( [ u'comprehension', u'vocab', u'notReady' ] )

    # Now reorder new cards based on MMI
    ds = []
    for ( cid, nid ) in db.execute( 'select id, nid from cards where type = 0' ):
        ds.append( { 'now':now, 'due':nid2mmi[ nid ], 'usn':mw.col.usn(), 'cid':cid } )
    mw.col.db.executemany( 'update cards set due=:due, mod=:now, usn=:usn where id=:cid', ds )

    printf( 'Updated notes in %f sec' % ( time.time() - t_0 ) )

def main():
    allDb = mkAllDb( MorphDb( cfg['path_ext'], ignoreErrors=True ) )
    updateNotes( allDb )
