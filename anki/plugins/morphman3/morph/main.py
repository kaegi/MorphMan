from functools import partial
import time

from anki.utils import splitFields, joinFields, stripHTML, intTime, fieldChecksum
from morphemes import MorphDb, AnkiDeck, getMorphemes
from util import printf, mw, memoize, cfg, cfg1

'''TODO:
* config option to disable memoization
* config deck overrides
* button to save interval dbs like seen.db, known.db, mature.db
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
    N_notes = db.scalar( 'select count() from notes' )
    mw.progress.start( label='Generating all.db', max=N_notes )

    if not allDb: allDb = MorphDb()
    fidDb, locDb = allDb.fidDb(), allDb.locDb()

    for i,( nid, mid, flds, guid ) in enumerate( db.execute( 'select id, mid, flds, guid from notes' ) ):
        if i % 500 == 0:    mw.progress.update( value=i )
        C = partial( cfg, mid, None ) #TODO: get correct did
        if not C('enabled'): continue
        mats = db.list( 'select ivl from cards where nid = :nid', nid=nid )
        for fieldName in C('morph_fields'):
            try: # if doesn't have field, continue
                #fieldValue = normalizeFieldValue( getField( fieldName, flds, mid ) )
                fieldValue = getMecabField( fieldName, flds, mid )
            except KeyError: continue

            loc = fidDb.get( ( nid, guid, fieldName ), None )
            if not loc:
                loc = AnkiDeck( nid, fieldName, fieldValue, guid, mats )
                ms = getMorphemes( fieldValue )
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
                    ms = getMorphemes( fieldValue )
                    locDb.pop( loc )
                    locDb[ newLoc ] = ms
    printf( 'Processed all %d notes in %f sec' % ( N_notes, time.time() - t_0 ) )
    mw.progress.update( value=i, label='Saving all.db...' )
    allDb.clear()
    allDb.addFromLocDb( locDb )
    if cfg1('saveAllDb'):
        allDb.save( cfg1('path_all') )
        printf( 'Processed all %d notes + saved all.db in %f sec' % ( N_notes, time.time() - t_0 ) )
    mw.progress.finish()
    return allDb

def filterDbByMat( db, mat ):
    newDb = MorphDb()
    for loc, ms in db.locDb().iteritems():
        if loc.maturity > mat:
            newDb.addMsL( ms, loc )
    return newDb

def updateNotes( allDb ):
    t_0, now, db, TAG   = time.time(), intTime(), mw.col.db, mw.col.tags
    N_notes = db.scalar( 'select count() from notes' )
    mw.progress.start( label='Updating notes from all.db', max=N_notes )
    ds, nid2mmi         = [], {}
    fidDb, locDb, popDb = allDb.fidDb(), allDb.locDb(), allDb.popDb()
    seenDb      = filterDbByMat( allDb, cfg1('threshold_seen') )
    knownDb     = filterDbByMat( allDb, cfg1('threshold_known') )
    matureDb    = filterDbByMat( allDb, cfg1('threshold_mature') )

    pops = [ len( locs ) for locs in allDb.db.values() ]
    pops = [ n for n in pops if n > 1 ]

    for i,( nid, mid, flds, guid, tags ) in enumerate( db.execute( 'select id, mid, flds, guid, tags from notes' ) ):
        if i % 500 == 0:    mw.progress.update( value=i )
        C = partial( cfg, mid, None ) #TODO: get correct did
        if not C('enabled'): continue
        # Get all morphemes for note
        ms = set()
        for fieldName in C('morph_fields'):
            try:
                loc = fidDb[ ( nid, guid, fieldName ) ]
                ms.update( locDb[ loc ] )
            except KeyError: continue
        ms = [ m for m in ms if m.pos not in C('morph_blacklist') ]

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

        # Fill in various fields/tags on the note based on cfg
        ts, fs = TAG.split( tags ), splitFields( flds )
            # determine card type
        compTag, vocabTag, notReadyTag, focusMorphTag = tagNames = C('tagNames')
        if N_m == 0:    # sentence comprehension card
            ts = [ compTag ] + [ t for t in ts if t not in [ vocabTag, notReadyTag ] ]
            setField( mid, fs, focusMorphTag, u'' )
        elif N_k == 1:  # new vocab card
            ts = [ vocabTag ] + [ t for t in ts if t not in [ notReadyTag ] ]
            setField( mid, fs, focusMorphTag, u'%s' % focusMorph.base )
        elif N_k > 1:   # M+1+ K+2+
            ts.append( notReadyTag )
            # set type agnostic fields
        setField( mid, fs, C('k+N'), u'%d' % N_k )
        setField( mid, fs, C('m+N'), u'%d' % N_m )
        setField( mid, fs, C('morphManIndex'), u'%d' % mmi )
        setField( mid, fs, C('unknowns'), u', '.join( u.base for u in unknowns ) )
        setField( mid, fs, C('unmatures'), u', '.join( u.base for u in unmatures ) )
        setField( mid, fs, C('unknownFreq'), u'%d' % F_k_avg )
            # update sql db
        tags_ = TAG.join( TAG.canonify( ts ) )
        flds_ = joinFields( fs )
        csum = fieldChecksum( fs[0] )
        sfld = stripHTML( fs[ getSortFieldIndex( mid ) ] )
        ds.append( { 'now':now, 'tags':tags_, 'flds':flds_, 'sfld':sfld, 'csum':csum, 'usn':mw.col.usn(), 'nid':nid } )

    mw.progress.update( value=i, label='Updating anki database...' )
    mw.col.db.executemany( 'update notes set tags=:tags, flds=:flds, sfld=:sfld, csum=:csum, mod=:now, usn=:usn where id=:nid', ds )
    TAG.register( tagNames )

    # Now reorder new cards based on MMI
    mw.progress.update( value=i, label='Updating new card ordering...' )
    ds = []
    for ( cid, nid ) in db.execute( 'select id, nid from cards where type = 0' ):
        if nid in nid2mmi: # owise it was disabled
            ds.append( { 'now':now, 'due':nid2mmi[ nid ], 'usn':mw.col.usn(), 'cid':cid } )
    mw.col.db.executemany( 'update cards set due=:due, mod=:now, usn=:usn where id=:cid', ds )
    mw.col.updateFieldCache( nid2mmi.keys() )
    mw.reset()

    printf( 'Updated notes in %f sec' % ( time.time() - t_0 ) )
    mw.progress.finish()

def main():
    # load existing all.db
    mw.progress.start( label='Loading existing all.db' )
    t_0 = time.time()
    cur = MorphDb( cfg1('path_all') ) if cfg1('loadAllDb') else None
    printf( 'Loaded all.db in %f sec' % ( time.time() - t_0 ) )
    mw.progress.finish()

    # update all.db
    allDb = mkAllDb( cur )

    # merge in external.db
    mw.progress.start( label='Merging ext.db' )
    ext = MorphDb( cfg1('path_ext'), ignoreErrors=True )
    allDb.merge( ext )
    mw.progress.finish()

    # update notes
    updateNotes( allDb )
