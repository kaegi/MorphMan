# -*- coding: utf-8 -*-
import time

from anki.utils import splitFields, joinFields, stripHTML, intTime, fieldChecksum
from anki.hooks import wrap, runHook
from aqt.addons import AddonManager

from .morphemes import MorphDb, AnkiDeck, getMorphemes
from .morphemizer import getMorphemizerByName
from . import stats
from .util import printf, mw, errorMsg, jcfg, jcfg2, getFilter, acfg, acfg_path
from . import util
from .util_external import memoize
import codecs

# only for jedi-auto-completion
import aqt.main
assert isinstance(mw, aqt.main.AnkiQt)

@memoize
def getFieldIndex( fieldName, mid ):
    """
    Returns the index of a field in a model by its name.
    For example: we have the modelId of the card "Basic".
    The return value might be "1" for fieldName="Front" and
    "2" for fieldName="Back".
    """
    m = mw.col.models.get( mid )
    d = dict( ( f['name'], f['ord'] ) for f in m['flds'] )
    try: return d[ fieldName ]
    except KeyError: return None

def extractFieldData( fname, flds, mid ):
    """
    :type str fname: The field name (like u'Expression')
    :type str flds: A string containing all field data for the model (created by anki.utils.joinFields())
    :type int mid: the modelId depicing the model for the "flds" data
    """
    idx = getFieldIndex( fname, mid )
    return stripHTML( splitFields( flds )[ idx ] )

@memoize
def getSortFieldIndex( mid ):
    return mw.col.models.get( mid )[ 'sortf' ]

def setField( mid, fs, k, v ): # nop if field DNE
    """
    :type int mid: modelId
    :type [str] fs: a list of all field data :type str k: name of field to modify (for example u'Expression')
    :type str v: new value for field
    """
    idx = getFieldIndex( k, mid )
    if idx: fs[ idx ] = v

def mkAllDb( allDb=None ):
    t_0, db, TAG = time.time(), mw.col.db, mw.col.tags
    N_notes = db.scalar( 'select count() from notes' )
    N_enabled_notes = 0 # for providing an error message if there is no note that is used for processing
    mw.progress.start( label='Prep work for all.db creation', max=N_notes, immediate=True )

    if not allDb: allDb = MorphDb()
    fidDb   = allDb.fidDb()
    locDb   = allDb.locDb( recalc=False )   # fidDb() already forces locDb recalc

    mw.progress.update( label='Generating all.db data' )
    for i,( nid, mid, flds, guid, tags ) in enumerate( db.execute( 'select id, mid, flds, guid, tags from notes' ) ):
        if i % 500 == 0:    mw.progress.update( value=i )

        note = mw.col.getNote(nid)
        notecfg = getFilter(note)
        if notecfg is None: continue
        morphemizer = getMorphemizerByName(notecfg['Morphemizer'])

        N_enabled_notes += 1

        mats = [ ( 0.5 if ivl == 0 and ctype == 1 else ivl ) for ivl, ctype in db.execute( 'select ivl, type from cards where nid = :nid', nid=nid ) ]
        if acfg('updates', 'ignoreMaturity', mid):
            mats = [ 0 for mat in mats ]
        ts, alreadyKnownTag = TAG.split( tags ), jcfg('Tag_AlreadyKnown')
        if alreadyKnownTag in ts:
            mats += [ acfg('thresholds', 'mature')+1 ]

        for fieldName in notecfg['Fields']:
            try: # if doesn't have field, continue
                fieldValue = extractFieldData( fieldName, flds, mid )
            except KeyError: continue
            except TypeError:
                mname = mw.col.models.get( mid )[ 'name' ]
                errorMsg( 'Failed to get field "{field}" from a note of model "{model}". Please fix your config.py file to match your collection appropriately and ignore the following error.'.format( model=mname, field=fieldName ) )
                raise

            loc = fidDb.get( ( nid, guid, fieldName ), None )
            if not loc:
                loc = AnkiDeck( nid, fieldName, fieldValue, guid, mats )
                ms = getMorphemes(morphemizer, fieldValue, ts)
                if ms: #TODO: this needed? should we change below too then?
                    locDb[ loc ] = ms
            else:
                # mats changed -> new loc (new mats), move morphs
                if loc.fieldValue == fieldValue and loc.maturities != mats:
                    newLoc = AnkiDeck( nid, fieldName, fieldValue, guid, mats )
                    locDb[ newLoc ] = locDb.pop( loc )
                # field changed -> new loc, new morphs
                elif loc.fieldValue != fieldValue:
                    newLoc = AnkiDeck( nid, fieldName, fieldValue, guid, mats )
                    ms = getMorphemes(morphemizer, fieldValue, ts)
                    locDb.pop( loc )
                    locDb[ newLoc ] = ms

    if N_enabled_notes == 0:
        mw.progress.finish()
        errorMsg('There is no card that can be analyzed or be moved. Add cards or (re-)check your configuration under "Tools -> MorhpMan Preferences" or in "Anki/addons/morph/config.py" for mistakes.')
        return None

    printf( 'Processed all %d notes in %f sec' % ( N_notes, time.time() - t_0 ) )
    mw.progress.update( value=i, label='Creating all.db object' )
    allDb.clear()
    allDb.addFromLocDb( locDb )
    if acfg('dbs', 'saveDbs'):
        mw.progress.update( value=i, label='Saving all.db to disk' )
        allDb.save(acfg_path('all'))
        printf( 'Processed all %d notes + saved all.db in %f sec' % ( N_notes, time.time() - t_0 ) )
    mw.progress.finish()
    return allDb

def filterDbByMat( db, mat ):
    '''Assumes safe to use cached locDb'''
    newDb = MorphDb()
    for loc, ms in db.locDb( recalc=False ).items():
        if loc.maturity > mat:
            newDb.addMsL( ms, loc )
    return newDb

def updateNotes( allDb ):
    t_0, now, db, TAG   = time.time(), intTime(), mw.col.db, mw.col.tags
    ds, nid2mmi         = [], {}
    N_notes             = db.scalar( 'select count() from notes' )
    mw.progress.start( label='Updating data', max=N_notes, immediate=True )
    fidDb   = allDb.fidDb()
    locDb   = allDb.locDb( recalc=False ) # fidDb() already forces locDb recalc

    # read tag names
    compTag, vocabTag, freshTag, notReadyTag, alreadyKnownTag, priorityTag, tooShortTag, tooLongTag, frequencyTag = tagNames = jcfg('Tag_Comprehension'), jcfg('Tag_Vocab'), jcfg('Tag_Fresh'), jcfg('Tag_NotReady'), jcfg('Tag_AlreadyKnown'), jcfg('Tag_Priority'), jcfg('Tag_TooShort'), jcfg('Tag_TooLong'), jcfg('Tag_Frequency')
    TAG.register( tagNames )
    badLengthTag = jcfg2().get('Tag_BadLength')

    # handle secondary databases
    mw.progress.update( label='Creating seen/known/mature from all.db' )
    seenDb      = filterDbByMat(allDb, acfg('thresholds', 'seen'))
    knownDb     = filterDbByMat(allDb, acfg('thresholds', 'known'))
    matureDb    = filterDbByMat(allDb, acfg('thresholds', 'mature'))
    mw.progress.update( label='Loading priority.db' )
    priorityDb  = MorphDb( acfg_path('priority'), ignoreErrors=True ).db

    mw.progress.update(label='Loading frequency.txt')
    frequencyListPath = acfg_path('frequency')
    try:
	    with codecs.open( frequencyListPath, 'r', 'utf-8' ) as f:
	        frequencyList = [line.strip().split('\t')[0] for line in f.readlines()]
	        frequencyListLength = len(frequencyList)
    except FileNotFoundError:
        pass # User does not have a frequency.txt

    if acfg('dbs', 'saveDbs'):
        mw.progress.update(label='Saving seen/known/mature dbs')
        seenDb.save(acfg_path('seen'))
        knownDb.save(acfg_path('known'))
        matureDb.save(acfg_path('mature'))

    mw.progress.update( label='Updating notes' )
    for i,( nid, mid, flds, guid, tags ) in enumerate( db.execute( 'select id, mid, flds, guid, tags from notes' ) ):
        if i % 500 == 0:    mw.progress.update( value=i )

        note = mw.col.getNote(nid)
        notecfg = getFilter(note)
        if notecfg is None or not notecfg['Modify']: continue

        # Get all morphemes for note
        morphemes = set()
        for fieldName in notecfg['Fields']:
            try:
                loc = fidDb[ ( nid, guid, fieldName ) ]
                morphemes.update( locDb[ loc ] )
            except KeyError: continue

        # Determine un-seen/known/mature and i+N
        unseens, unknowns, unmatures, newKnowns = set(), set(), set(), set()
        for morpheme in morphemes:
            if not seenDb.matches(morpheme):   unseens.add( morpheme )
            if not knownDb.matches(morpheme):   unknowns.add( morpheme )
            if not matureDb.matches(morpheme):   unmatures.add( morpheme )
            if not matureDb.matches(morpheme) and knownDb.matches(morpheme):
                newKnowns.add( morpheme )

        # Determine MMI - Morph Man Index
        N, N_s, N_k, N_m = len( morphemes ), len( unseens ), len( unknowns ), len( unmatures )

        # Bail early for lite update
        if N_k > 2 and acfg('updates', 'only2TAndBelowCards', mid): continue

        # average frequency of unknowns (ie. how common the word is within your collection)
        F_k = 0
        for focusMorph in unknowns: # focusMorph used outside loop
            F_k += allDb.frequency(focusMorph)
        F_k_avg = F_k // N_k if N_k > 0 else F_k
        usefulness = F_k_avg

        priority_db_weight = acfg('weights', 'priorityDb', mid)
        frequency_text_scale = acfg('weights', 'frequencyTxtScale')

        # add bonus for morphs in priority.db and frequency.txt
        isPriority = False
        isFrequency = False
        for focusMorph in unknowns:
            if focusMorph in priorityDb:
                isPriority = True
                usefulness += priority_db_weight
            focusMorphString = focusMorph.base
            try:
                focusMorphIndex = frequencyList.index(focusMorphString)
                isFrequency = True

                # The bigger this number, the lower mmi becomes
                usefulness += (frequencyListLength - focusMorphIndex) * frequency_text_scale
            except:
                pass

        reinforce_new_volcab_weight = acfg('weights', 'reinforceNewVolcab', mid)

        # add bonus for studying recent learned knowns (reinforce)
        for morpheme in newKnowns:
            locs = knownDb.getMatchingLocs(morpheme)
            if locs:
                ivl = min(1, max(loc.maturity for loc in locs))
                usefulness += reinforce_new_volcab_weight // ivl #TODO: maybe average this so it doesnt favor long sentences

        verb_bonus = acfg('weights', 'verbBonus', mid)

        if any(morpheme.pos == '動詞' for morpheme in unknowns): #FIXME: this isn't working???
            usefulness += verb_bonus

        usefulness = 99999 - min(99999, usefulness)

        # difference from optimal length range (too little context vs long sentence)
        lenDiffRaw = min(N - acfg('goodSentenceLength', 'minimum'),
                         max(0, N - acfg('goodSentenceLength', 'maximum')))
        lenDiff = min(9, abs(lenDiffRaw))

        # calculate mmi
        mmi = 100000 * N_k + 1000 * lenDiff + usefulness
        if acfg('updates', 'setDueBasedOnMMI', mid):
            nid2mmi[ nid ] = mmi

        # Fill in various fields/tags on the note based on cfg
        ts, fs = TAG.split( tags ), splitFields( flds )

        # clear any 'special' tags, the appropriate will be set in the next few lines
        ts = [ t for t in ts if t not in [ notReadyTag, compTag, vocabTag, freshTag ] ]

        # determine card type
        if N_m == 0:    # sentence comprehension card, m+0
            ts = ts + [ compTag ]
        elif N_k == 1:  # new vocab card, k+1
            ts = ts + [ vocabTag ]
            setField( mid, fs, jcfg('Field_FocusMorph'), '%s' % focusMorph.base )
        elif N_k > 1:   # M+1+ and K+2+
            ts = ts + [ notReadyTag ]
            setField( mid, fs, jcfg('Field_FocusMorph'), '')
        elif N_m == 1: # we have k+0, and m+1, so this card does not introduce a new vocabulary -> card for newly learned morpheme
            ts = ts + [ freshTag ]
            setField( mid, fs, jcfg('Field_FocusMorph'), '%s' % list(unmatures)[0].base)
        else: # only case left: we have k+0, but m+2 or higher, so this card does not introduce a new vocabulary -> card for newly learned morpheme
            ts = ts + [ freshTag ]
            setField( mid, fs, jcfg('Field_FocusMorph'), '')


        # set type agnostic fields
        setField( mid, fs, jcfg('Field_UnknownMorphCount'), '%d' % N_k )
        setField( mid, fs, jcfg('Field_UnmatureMorphCount'), '%d' % N_m )
        setField( mid, fs, jcfg('Field_MorphManIndex'), '%d' % mmi )
        setField( mid, fs, jcfg('Field_Unknowns'), ', '.join( u.base for u in unknowns ) )
        setField( mid, fs, jcfg('Field_Unmatures'), ', '.join( u.base for u in unmatures ) )
        setField( mid, fs, jcfg('Field_UnknownFreq'), '%d' % F_k_avg )

        # remove deprecated tag
        if badLengthTag is not None and badLengthTag in ts:
            ts.remove( badLengthTag )

        # other tags
        if priorityTag in ts:   ts.remove( priorityTag )
        if isPriority:          ts.append( priorityTag )

        if frequencyTag in ts:   ts.remove( frequencyTag )
        if isFrequency:          ts.append( frequencyTag )

        if tooShortTag in ts:   ts.remove( tooShortTag )
        if lenDiffRaw < 0:      ts.append( tooShortTag )

        if tooLongTag in ts:    ts.remove( tooLongTag )
        if lenDiffRaw > 0:      ts.append( tooLongTag )

        # remove unnecessary tags
        if not jcfg('Option_SetNotRequiredTags'):
            unnecessary = [priorityTag, tooShortTag, tooLongTag]
            ts = [tag for tag in ts if tag not in unnecessary]

        # update sql db
        tags_ = TAG.join( TAG.canonify( ts ) )
        flds_ = joinFields( fs )
        if flds != flds_ or tags != tags_:  # only update notes that have changed
            csum = fieldChecksum( fs[0] )
            sfld = stripHTML( fs[ getSortFieldIndex( mid ) ] )
            ds.append( { 'now':now, 'tags':tags_, 'flds':flds_, 'sfld':sfld, 'csum':csum, 'usn':mw.col.usn(), 'nid':nid } )

    mw.progress.update( value=i, label='Updating anki database...' )
    mw.col.db.executemany( 'update notes set tags=:tags, flds=:flds, sfld=:sfld, csum=:csum, mod=:now, usn=:usn where id=:nid', ds )

    # Now reorder new cards based on MMI
    mw.progress.update( value=i, label='Updating new card ordering...' )
    ds = []

    # "type = 0": new cards
    # "type = 1": learning cards [is supposed to be learning: in my case no learning card had this type]
    # "type = 2": review cards
    for ( cid, nid, due ) in db.execute( 'select id, nid, due from cards where type = 0' ):
        if nid in nid2mmi: # owise it was disabled
            due_ = nid2mmi[ nid ]
            if due != due_: # only update cards that have changed
                ds.append( { 'now':now, 'due':due_, 'usn':mw.col.usn(), 'cid':cid } )
    mw.col.db.executemany( 'update cards set due=:due, mod=:now, usn=:usn where id=:cid', ds )
    mw.reset()

    printf( 'Updated notes in %f sec' % ( time.time() - t_0 ) )
    mw.progress.finish()
    return knownDb


def write_config_hook(self, module, conf):
    runHook('writeAddonConfig')


def main():

    AddonManager.writeConfig = wrap(AddonManager.writeConfig, write_config_hook)

    # load existing all.db
    mw.progress.start( label='Loading existing all.db', immediate=True )
    t_0 = time.time()
    cur = util.allDb(reload=True) if acfg('dbs', 'loadAllDb') else None
    printf( 'Loaded all.db in %f sec' % ( time.time() - t_0 ) )
    mw.progress.finish()

    # update all.db
    allDb = mkAllDb( cur )
    if not allDb: # there was an (non-critical-/non-"exception"-)error but error message was already displayed
        mw.progress.finish()
        return

    # merge in external.db
    mw.progress.start( label='Merging ext.db', immediate=True )
    ext = MorphDb( acfg_path('external'), ignoreErrors=True )
    allDb.merge( ext )
    mw.progress.finish()

    # update notes
    knownDb = updateNotes( allDb )

    # update stats and refresh display
    stats.updateStats( knownDb )
    mw.toolbar.draw()

    # set global allDb
    util._allDb = allDb
