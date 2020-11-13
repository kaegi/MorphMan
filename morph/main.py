# -*- coding: utf-8 -*-
import csv
import importlib
import io
import time
import itertools

from anki.tags import TagManager

from functools import partial

import aqt.main
from anki.utils import splitFields, joinFields, stripHTML, intTime, fieldChecksum

from .morphemes import Location, Morpheme
from . import stats
from . import util
from .morphemes import MorphDb, AnkiDeck, getMorphemes
from .morphemizer import getMorphemizerByName
from .util import printf, mw, errorMsg, getFilterByMidAndTags, getReadEnabledModels, getModifyEnabledModels
from .preferences import get_preference as cfg, get_preferences
from .util_external import memoize

# hack: typing is compile time anyway, so, nothing bad happens if it fails, the try is to support anki < 2.1.16
try:
    from aqt.pinnedmodules import typing  # pylint: disable=W0611 # See above hack comment
    from typing import Dict, Set
except ImportError:
    pass

# not all anki verions have profiling features
doProfile = False
try:
    import cProfile, pstats
    from pstats import SortKey
except:
    pass


# only for jedi-auto-completion
assert isinstance(mw, aqt.main.AnkiQt)


@memoize
def getFieldIndex(fieldName, mid):
    """
    Returns the index of a field in a model by its name.
    For example: we have the modelId of the card "Basic".
    The return value might be "1" for fieldName="Front" and
    "2" for fieldName="Back".
    """
    m = mw.col.models.get(mid)
    return next((f['ord'] for f in m['flds'] if f['name'] == fieldName), None)


def extractFieldData(field_name, fields, mid):
    # type: (str, str, str) -> str
    """
    :type field_name: The field name (like u'Expression')
    :type fields: A string containing all field data for the model (created by anki.utils.joinFields())
    :type mid: the modelId depicting the model for the "fields" data
    """
    idx = getFieldIndex(field_name, mid)
    return stripHTML(splitFields(fields)[idx])


@memoize
def getSortFieldIndex(mid):
    return mw.col.models.get(mid)['sortf']


def setField(mid, fs, k, v):  # nop if field DNE
    # type: (int, [str], str, str) -> None
    """
    :type mid: modelId
    :type fs: a list of all field data
    :type k: name of field to modify (for example u'Expression')
    :type v: new value for field
    """
    idx = getFieldIndex(k, mid)
    if idx:
        fs[idx] = v



def mkAllDb(all_db=None):
    from . import config
    importlib.reload(config)
    t_0, db, TAG = time.time(), mw.col.db, mw.col.tags
    mw.progress.start(label='Prep work for all.db creation',
                      immediate=True)
    # for providing an error message if there is no note that is used for processing
    N_enabled_notes = 0


    if not all_db:
        all_db = MorphDb()

    # Recompute everything if preferences changed.
    last_preferences = all_db.meta.get('last_preferences', {})
    if not last_preferences == get_preferences():
        print("Preferences changed.  Recomputing all_db...")
        last_updated = 0
        should_rebuild_ms = True
    else:
        last_updated = all_db.meta.get('last_updated', 0)
        should_rebuild_ms = False

    fidDb = all_db.fidDb()
    locDb = all_db.locDb(recalc=False)  # fidDb() already forces locDb recalc

    included_types, include_all = getReadEnabledModels()
    included_mids = [m['id'] for m in mw.col.models.all() if include_all or m['name'] in included_types]

# 
# First find the cards to analyze
#   then find the max maturity of those cards
    query = '''
WITH notesToUpdate as (
   SELECT distinct n.id AS nid, mid, flds, guid, tags 
     FROM notes n JOIN cards c ON (n.id = c.nid)
     WHERE mid IN (%s) and (n.mod > %s or c.mod > %s ))
SELECT nid, mid, flds, guid, tags, 
       max(case when ivl=0 and c.type=1 then 0.5 else ivl end) AS maxmat 
FROM notesToUpdate join cards c USING (nid)
GROUP by nid, mid, flds, guid, tags;
'''%(','.join([str(m) for m in included_mids]), last_updated, last_updated)

    query_results = db.execute(query)
    N_notes = len(query_results)

    mw.progress.finish()
    mw.progress.start(label='Generating all.db data',
                      max=N_notes,
                      immediate=True)

    for i, (nid, mid, flds, guid, tags, maxmat) in enumerate(query_results):

        if i % 500 == 0:
            mw.progress.update(value=i)

        C = partial(cfg, model_id=mid)


        mid_cfg = getFilterByMidAndTags(mid, tags)
        if mid_cfg is None:
            continue

        mName = mid_cfg['Morphemizer']

        morphemizer = getMorphemizerByName(mName)

        N_enabled_notes += 1

        if C('ignore maturity'):
            maxmat = 0
        ts, alreadyKnownTag = TAG.split(tags), cfg('Tag_AlreadyKnown')
        if alreadyKnownTag in ts:
            maxmat = max(maxmat, C('threshold_mature') + 1)

        for fieldName in mid_cfg['Fields']:
            try:  # if doesn't have field, continue
                fieldValue = extractFieldData(fieldName, flds, mid)
            except KeyError:
                continue
            except TypeError:
                mname = mw.col.models.get(mid)['name']
                errorMsg('Failed to get field "{field}" from a note of model "{model}". Please fix your Note Filters '
                         'under MorphMan > Preferences to match your collection appropriately.'.format(
                             model=mname, field=fieldName))
                return
            assert maxmat!=None, "Maxmat should not be None"

            loc = fidDb.get((nid, guid, fieldName), None)
            if not loc:
                loc = AnkiDeck(nid, fieldName, fieldValue, guid, maxmat)
                ms = getMorphemes(morphemizer, fieldValue, ts)
                if ms:  # TODO: this needed? should we change below too then?
                    locDb[loc] = ms
            else:
                # mats changed -> new loc (new mats), move morphs
                if loc.fieldValue == fieldValue and loc.maturity != maxmat and not should_rebuild_ms:
                    newLoc = AnkiDeck(nid, fieldName, fieldValue, guid, maxmat)
                    locDb[newLoc] = locDb.pop(loc)
                # field changed -> new loc, new morphs
                elif loc.fieldValue != fieldValue or should_rebuild_ms:
                    newLoc = AnkiDeck(nid, fieldName, fieldValue, guid, maxmat)
                    ms = getMorphemes(morphemizer, fieldValue, ts)
                    locDb.pop(loc)
                    locDb[newLoc] = ms

    printf('Processed %d notes in %f sec' % (N_notes, time.time() - t_0))

    mw.progress.update(label='Creating all.db objects')
    all_db.clear()
    all_db.addFromLocDb(locDb)
    all_db.meta['last_updated'] = int(time.time() + 0.5)
    all_db.meta['last_preferences'] = get_preferences()
    mw.progress.finish()
    return all_db


def filterDbByMat(db, mat):
    """Assumes safe to use cached locDb"""
    newDb = MorphDb()
    for loc, ms in db.locDb(recalc=False).items():
        if loc.maturity > mat:
            newDb.addMsL(ms, loc)
    return newDb


def updateNotes(allDb):
    t_0, now, db = time.time(), intTime(), mw.col.db

    TAG = mw.col.tags  # type: TagManager
    ds, nid2mmi = [], {}
    mw.progress.start(label='Updating data', immediate=True)
    fidDb = allDb.fidDb(recalc=True)
    loc_db = allDb.locDb(recalc=False)  # type: Dict[Location, Set[Morpheme]]

    # read tag names
    compTag, vocabTag, freshTag, notReadyTag, alreadyKnownTag, priorityTag, tooShortTag, tooLongTag, frequencyTag = tagNames = cfg(
        'Tag_Comprehension'), cfg('Tag_Vocab'), cfg('Tag_Fresh'), cfg('Tag_NotReady'), cfg(
        'Tag_AlreadyKnown'), cfg('Tag_Priority'), cfg('Tag_TooShort'), cfg('Tag_TooLong'), cfg('Tag_Frequency')
    TAG.register(tagNames)
    badLengthTag = cfg('Tag_BadLength')

    # handle secondary databases
    mw.progress.update(label='Creating seen/known/mature from all.db')
    seenDb = filterDbByMat(allDb, cfg('threshold_seen'))
    knownDb = filterDbByMat(allDb, cfg('threshold_known'))
    matureDb = filterDbByMat(allDb, cfg('threshold_mature'))
    mw.progress.update(label='Loading priority.db')
    priorityDb = MorphDb(cfg('path_priority'), ignoreErrors=True).db

    mw.progress.update(label='Loading frequency.txt')
    frequencyListPath = cfg('path_frequency')
    frequency_map = {}
    frequency_has_morphemes = False

    try:
        with io.open(frequencyListPath, encoding='utf-8-sig') as csvfile:
            csvreader = csv.reader(csvfile, delimiter="\t")
            rows = [row for row in csvreader]

            if rows[0][0] == "#study_plan_frequency":
                frequency_has_morphemes = True
                frequency_map = dict(
                    zip([Morpheme(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows[1:]],
                        itertools.count(0)))
            else:
                frequency_map = dict(zip([row[0] for row in rows], itertools.count(0)))

    except FileNotFoundError:
        pass

    frequencyListLength = len(frequency_map)

    # prefetch cfg for fields
    field_focus_morph = cfg('Field_FocusMorph')
    field_unknown_count = cfg('Field_UnknownMorphCount')
    field_unmature_count = cfg('Field_UnmatureMorphCount')
    field_morph_man_index = cfg('Field_MorphManIndex')
    field_unknowns = cfg('Field_Unknowns')
    field_unmatures = cfg('Field_Unmatures')
    field_unknown_freq = cfg('Field_UnknownFreq')
    field_focus_morph_pos = cfg("Field_FocusMorphPos")
    
    included_types, include_all = getModifyEnabledModels()
    included_mids = [m['id'] for m in mw.col.models.all() if include_all or m['name'] in included_types]

    query = 'select id, mid, flds, guid, tags from notes WHERE mid IN (%s)' % (','.join([str(m) for m in included_mids]))
    query_results = db.execute(query)

    N_notes = len(query_results)
    mw.progress.finish()
    mw.progress.start(label='Updating notes',
                      max=N_notes,
                      immediate=True)

    for i, (nid, mid, flds, guid, tags) in enumerate(query_results):
        ts = TAG.split(tags)
        if i % 500 == 0:
            mw.progress.update(value=i)

        C = partial(cfg, model_id=mid)

        notecfg = getFilterByMidAndTags(mid, ts)
        if notecfg is None or not notecfg['Modify']:
            continue

        # Get all morphemes for note
        morphemes = set()
        for fieldName in notecfg['Fields']:
            try:
                loc = fidDb[(nid, guid, fieldName)]
                morphemes.update(loc_db[loc])
            except KeyError:
                continue

        proper_nouns_known = cfg('Option_ProperNounsAlreadyKnown')

        # Determine un-seen/known/mature and i+N
        unseens, unknowns, unmatures, new_knowns = set(), set(), set(), set()
        for morpheme in morphemes:
            if proper_nouns_known and morpheme.isProperNoun():
                continue
            if not seenDb.matches(morpheme):
                unseens.add(morpheme)
            if not knownDb.matches(morpheme):
                unknowns.add(morpheme)
            if not matureDb.matches(morpheme):
                unmatures.add(morpheme)
                if knownDb.matches(morpheme):
                    new_knowns.add(morpheme)

        # Determine MMI - Morph Man Index
        N, N_s, N_k, N_m = len(morphemes), len(
            unseens), len(unknowns), len(unmatures)

        # Bail early for lite update
        if N_k > 2 and C('only update k+2 and below'):
            continue

        # add bonus for morphs in priority.db and frequency.txt
        frequencyBonus = C('frequency.txt bonus')
        isPriority = False
        isFrequency = False

        focusMorph = None

        F_k = 0
        usefulness = 0
        for focusMorph in unknowns:
            F_k += allDb.frequency(focusMorph)
            if focusMorph in priorityDb:
                isPriority = True
                usefulness += C('priority.db weight')
            
            if frequency_has_morphemes:
                focusMorphIndex = frequency_map.get(focusMorph, -1)
            else:
                focusMorphIndex = frequency_map.get(focusMorph.base, -1)

            if focusMorphIndex >= 0:
                isFrequency = True

                # The bigger this number, the lower mmi becomes
                usefulness += int(round( frequencyBonus * (1 - focusMorphIndex / frequencyListLength) ))

        # average frequency of unknowns (ie. how common the word is within your collection)
        F_k_avg = F_k // N_k if N_k > 0 else F_k
        usefulness += F_k_avg

        # add bonus for studying recent learned knowns (reinforce)
        for morpheme in new_knowns:
            locs = knownDb.getMatchingLocs(morpheme)
            if locs:
                ivl = min(1, max(loc.maturity for loc in locs))
                # TODO: maybe average this so it doesnt favor long sentences
                usefulness += C('reinforce new vocab weight') // ivl

        if any(morpheme.pos == '動詞' for morpheme in unknowns):  # FIXME: this isn't working???
            usefulness += C('verb bonus')

        usefulness = 99999 - min(99999, usefulness)

        # difference from optimal length range (too little context vs long sentence)
        lenDiffRaw = min(N - C('min good sentence length'),
                         max(0, N - C('max good sentence length')))
        lenDiff = min(9, abs(lenDiffRaw))

        # calculate mmi
        mmi = 100000 * N_k + 1000 * lenDiff + int(round(usefulness))
        if C('set due based on mmi'):
            nid2mmi[nid] = mmi

        # Fill in various fields/tags on the note based on cfg
        fs = splitFields(flds)

        # clear any 'special' tags, the appropriate will be set in the next few lines
        ts = [t for t in ts if t not in (
            notReadyTag, compTag, vocabTag, freshTag)]

        # determine card type
        if N_m == 0:  # sentence comprehension card, m+0
            ts.append(compTag)
        elif N_k == 1:  # new vocab card, k+1
            ts.append(vocabTag)
            setField(mid, fs, field_focus_morph, focusMorph.base)
            setField(mid, fs, field_focus_morph_pos, focusMorph.pos)
        elif N_k > 1:  # M+1+ and K+2+
            ts.append(notReadyTag)
        elif N_m == 1:  # we have k+0, and m+1, so this card does not introduce a new vocabulary -> card for newly learned morpheme
            ts.append(freshTag)
            focusMorph = next(iter(unmatures))
            setField(mid, fs, field_focus_morph, focusMorph.base)
            setField(mid, fs, field_focus_morph_pos, focusMorph.pos)

        else:  # only case left: we have k+0, but m+2 or higher, so this card does not introduce a new vocabulary -> card for newly learned morpheme
            ts.append(freshTag)

        # set type agnostic fields
        setField(mid, fs, field_unknown_count, '%d' % N_k)
        setField(mid, fs, field_unmature_count, '%d' % N_m)
        setField(mid, fs, field_morph_man_index, '%d' % mmi)
        setField(mid, fs, field_unknowns, ', '.join(u.base for u in unknowns))
        setField(mid, fs, field_unmatures,
                 ', '.join(u.base for u in unmatures))
        setField(mid, fs, field_unknown_freq, '%d' % F_k_avg)

        # remove deprecated tag
        if badLengthTag is not None and badLengthTag in ts:
            ts.remove(badLengthTag)

        # other tags
        if priorityTag in ts:
            ts.remove(priorityTag)
        if isPriority:
            ts.append(priorityTag)

        if frequencyTag in ts:
            ts.remove(frequencyTag)
        if isFrequency:
            ts.append(frequencyTag)

        if tooShortTag in ts:
            ts.remove(tooShortTag)
        if lenDiffRaw < 0:
            ts.append(tooShortTag)

        if tooLongTag in ts:
            ts.remove(tooLongTag)
        if lenDiffRaw > 0:
            ts.append(tooLongTag)

        # remove unnecessary tags
        if not cfg('Option_SetNotRequiredTags'):
            unnecessary = [priorityTag, tooShortTag, tooLongTag]
            ts = [tag for tag in ts if tag not in unnecessary]

        # update sql db
        tags_ = TAG.join(TAG.canonify(ts))
        flds_ = joinFields(fs)
        if flds != flds_ or tags != tags_:  # only update notes that have changed
            csum = fieldChecksum(fs[0])
            sfld = stripHTML(fs[getSortFieldIndex(mid)])
            ds.append(
                (tags_, flds_, sfld, csum, now, mw.col.usn(), nid))

    mw.progress.update(label='Updating anki database...')
    mw.col.db.executemany(
        'update notes set tags=?, flds=?, sfld=?, csum=?, mod=?, usn=? where id=?', ds)

    # Now reorder new cards based on MMI
    mw.progress.update(label='Updating new card ordering...')
    ds = []

    # "type = 0": new cards
    # "type = 1": learning cards [is supposed to be learning: in my case no learning card had this type]
    # "type = 2": review cards
    for (cid, nid, due) in db.execute('select id, nid, due from cards where type = 0'):
        if nid in nid2mmi:  # owise it was disabled
            due_ = nid2mmi[nid]
            if due != due_:  # only update cards that have changed
                ds.append((due_, now,
                           mw.col.usn(), cid))

    mw.col.db.executemany(
        'update cards set due=?, mod=?, usn=? where id=?', ds)

    mw.reset()

    printf('Updated notes in %f sec' % (time.time() - t_0))

    if cfg('saveDbs'):
        mw.progress.update(label='Saving all/seen/known/mature dbs')
        allDb.meta['last_updated'] = int(time.time() + 0.5)
        allDb.save(cfg('path_all'))
        seenDb.save(cfg('path_seen'))
        knownDb.save(cfg('path_known'))
        matureDb.save(cfg('path_mature'))
        printf('Updated notes + saved dbs in %f sec' % (time.time() - t_0))

    mw.progress.finish()
    return knownDb


def main():
    # begin-------------------
    global doProfile
    if doProfile:
        pr = cProfile.Profile()
        pr.enable()

    # load existing all.db
    mw.progress.start(label='Loading existing all.db', immediate=True)
    t_0 = time.time()
    cur = util.allDb() if cfg('loadAllDb') else None
    printf('Loaded all.db in %f sec' % (time.time() - t_0))
    mw.progress.finish()

    # update all.db
    allDb = mkAllDb(cur)
    # there was an (non-critical-/non-"exception"-)error but error message was already displayed
    if not allDb:
        mw.progress.finish()
        return

    # merge in external.db
    mw.progress.start(label='Merging ext.db', immediate=True)
    ext = MorphDb(cfg('path_ext'), ignoreErrors=True)
    allDb.merge(ext)
    mw.progress.finish()

    # update notes
    knownDb = updateNotes(allDb)

    # update stats and refresh display
    stats.updateStats(knownDb)
    mw.toolbar.draw()

    # set global allDb
    util._allDb = allDb

    # finish-------------------
    if doProfile:
        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
