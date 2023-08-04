# -*- coding: utf-8 -*-
import csv
import importlib
import io
import time
import itertools

from anki.tags import TagManager

from functools import partial

import aqt.main
from anki.utils import split_fields, join_fields, strip_html, int_time, field_checksum

from .morphemes import Location, Morpheme
from . import stats
from . import util
from .morphemes import MorphDb, AnkiDeck, getMorphemes
from .morphemizer import getMorphemizerByName
from .util import printf, mw, errorMsg, getFilterByMidAndTags, getReadEnabledModels, getModifyEnabledModels
from .preferences import get_preference as cfg, get_preferences
from .util_external import memoize
from .language import *

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
    :type fields: A string containing all field data for the model (created by anki.utils.join_fields())
    :type mid: the modelId depicting the model for the "fields" data
    """
    idx = getFieldIndex(field_name, mid)
    return strip_html(split_fields(fields)[idx])


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

def notesToUpdate(last_updated, included_mids):
    # returns list of (nid, mid, flds, guid, tags, maxmat) of
    # cards to analyze
    # ignoring cards that are leeches
    # 
    # leeches are cards have tag "Leech". Anki guarantees a space before and after
    #
    # the logic of the query is:
    #   include cards in the result that are
    #     non-suspended
    #      or
    #     are suspended and are not Leeches
    #
    # we build a predicate that we append to the where clause
    if cfg('Option_IgnoreSuspendedLeeches'):
        filterSuspLeeches = "(c.queue <> -1 or (c.queue = -1 and not instr(tags, ' leech ')))"
    else:
        filterSuspLeeches = "TRUE"

    #
    # First find the cards to analyze
    #   then find the max maturity of those cards
    query = '''
        WITH notesToUpdate as (
            SELECT distinct n.id AS nid, mid, flds, guid, tags
            FROM notes n JOIN cards c ON (n.id = c.nid)
            WHERE mid IN ({0}) and (n.mod > {1} or c.mod > {1})
               and {2}) -- ignoring suspended leeches
        SELECT nid, mid, flds, guid, tags,
            max(case when ivl=0 and c.type=1 then 0.5 else ivl end) AS maxmat
        FROM notesToUpdate join cards c USING (nid)
        WHERE {2} -- ignoring suspended leeches
        GROUP by nid, mid, flds, guid, tags;
        '''.format(','.join([str(m) for m in included_mids]), last_updated, filterSuspLeeches)

    return mw.col.db.execute(query)

def mkAllDb(all_db, language):
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
        all_db = MorphDb() # Clear all db
        last_updated = 0
    else:
        last_updated = all_db.meta.get('last_updated', 0)

    fidDb = all_db.fidDb()
    locDb = all_db.locDb(recalc=False)  # fidDb() already forces locDb recalc

    included_types, include_all = getReadEnabledModels()
    included_mids = [m['id'] for m in mw.col.models.all() if include_all or m['name'] in included_types]

    notes = notesToUpdate(last_updated, included_mids)
    N_notes = len(notes)

    mw.progress.finish()
    mw.progress.start(label='Generating all.db data',
                      max=N_notes,
                      immediate=True)

    for i, (nid, mid, flds, guid, tags, maxmat) in enumerate(notes):

        if i % 500 == 0:
            mw.progress.update(value=i)

        ts = TAG.split(tags)
        mid_cfg = getFilterByMidAndTags(mid, ts)
        if mid_cfg is None:
            continue

        if 'Language' in mid_cfg:
            if (mid_cfg['Language'] != language):
                continue

        N_enabled_notes += 1

        mName = mid_cfg['Morphemizer']
        morphemizer = getMorphemizerByName(mName)

        C = partial(cfg, model_id=mid)

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
                # We need to finish the progress bar before presenting an error window or the UI will hang waiting on progress updates.
                # The proper solution here is probably to not block the main thread at all by doing the recalc in the background.
                mw.progress.finish()
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
                if loc.fieldValue == fieldValue and loc.maturity != maxmat:
                    newLoc = AnkiDeck(nid, fieldName, fieldValue, guid, maxmat)
                    locDb[newLoc] = locDb.pop(loc)
                # field changed -> new loc, new morphs
                elif loc.fieldValue != fieldValue:
                    newLoc = AnkiDeck(nid, fieldName, fieldValue, guid, maxmat)
                    ms = getMorphemes(morphemizer, fieldValue, ts)
                    locDb.pop(loc)
                    locDb[newLoc] = ms

    printf('Processed %d notes in %f sec' % (N_notes, time.time() - t_0))

    mw.progress.update(label='Creating all.db objects')
    old_meta = all_db.meta
    all_db.clear()
    all_db.addFromLocDb(locDb)
    all_db.meta = old_meta
    mw.progress.finish()
    return all_db

def filterDbByMat(db, mat):
    """Assumes safe to use cached locDb"""
    newDb = MorphDb()
    for loc, ms in db.locDb(recalc=False).items():
        if loc.maturity > mat:
            newDb.addMsL(ms, loc)
    return newDb


def updateNotes(allDb, language):
    t_0, now, db = time.time(), int_time(), mw.col.db

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
    priorityDb = MorphDb(getPathByLanguage(cfg('path_priority'),language), ignoreErrors=True)

    mw.progress.update(label='Loading frequency list')
    frequency_list = loadFrequencyListByLanguage(language)

    # prefetch cfg for fields
    field_focus_morph = cfg('Field_FocusMorph')
    field_unknown_count = cfg('Field_UnknownMorphCount')
    field_unmature_count = cfg('Field_UnmatureMorphCount')
    field_morph_man_index = cfg('Field_MorphManIndex')
    field_unknowns = cfg('Field_Unknowns')
    field_unmatures = cfg('Field_Unmatures')
    field_unknown_freq = cfg('Field_UnknownFreq')
    field_focus_morph_pos = cfg("Field_FocusMorphPos")

    skip_comprehension_cards = cfg('Option_SkipComprehensionCards')
    skip_fresh_cards = cfg('Option_SkipFreshVocabCards')
    
    # Find all morphs that changed maturity and the notes that refer to them.
    last_maturities = allDb.meta.get('last_maturities', {})
    new_maturities = {}
    refresh_notes = set()

    # Recompute everything if preferences changed.
    last_preferences = allDb.meta.get('last_preferences', {})
    if not last_preferences == get_preferences():
        print("Preferences changed.  Updating all notes...")
        last_updated = 0
    else:
        last_updated = allDb.meta.get('last_updated', 0)

    # Todo: Remove this forced 0 once we add checks for other changes like new frequency.txt files.
    last_updated = 0

    # If we're updating everything anyway, clear the notes set.
    if last_updated > 0:
        for m, locs in allDb.db.items():
            maturity_bits = 0
            if seenDb.matches(m):
                maturity_bits |= 1
            if knownDb.matches(m):
                maturity_bits |= 2
            if matureDb.matches(m):
                maturity_bits |= 4

            new_maturities[m] = maturity_bits

            if last_maturities.get(m, -1) != maturity_bits:
                for loc in locs:
                    if isinstance(loc, AnkiDeck):
                        refresh_notes.add(loc.noteId)

    included_types, include_all = getModifyEnabledModels()
    included_mids = [m['id'] for m in mw.col.models.all() if include_all or m['name'] in included_types]

    query = '''
        SELECT n.id as nid, mid, flds, guid, tags, max(c.type) AS maxtype
        FROM notes n JOIN cards c ON (n.id = c.nid)
        WHERE mid IN ({0}) and ( n.mod > {2} or n.id in ({1}) )
        GROUP by nid, mid, flds, guid, tags;
        '''.format(','.join([str(m) for m in included_mids]), ','.join([str(id) for id in refresh_notes]), last_updated)
    query_results = db.execute(query)

    N_notes = len(query_results)
    mw.progress.finish()
    mw.progress.start(label='Updating notes',
                      max=N_notes,
                      immediate=True)

    for i, (nid, mid, flds, guid, tags, maxtype) in enumerate(query_results):
        ts = TAG.split(tags)
        if i % 500 == 0:
            mw.progress.update(value=i)

        C = partial(cfg, model_id=mid)

        notecfg = getFilterByMidAndTags(mid, ts)
        if notecfg is None or not notecfg['Modify']:
            continue

        if 'Language' in notecfg:
            if (notecfg['Language'] != language):
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
            morpheme = morpheme.deinflected()
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
        if C('Option_AlwaysPrioritizeFrequencyMorphs'):
            noPriorityPenalty = C('no priority penalty')
        else:
            noPriorityPenalty = 0
        reinforceNewVocabWeight = C('reinforce new vocab weight')
        priorityDbWeight = C('priority.db weight')
        isPriority = False
        isFrequency = False

        focusMorph = None

        F_k = 0
        usefulness = 0
        for focusMorph in unknowns:
            F_k += allDb.frequency(focusMorph)

            if priorityDb.frequency(focusMorph) > 0:
                isPriority = True
                usefulness += priorityDbWeight
            
            if frequency_list.has_morphemes:
                focusMorphIndex = frequency_list.map.get(focusMorph, -1)
            else:
                focusMorphIndex = frequency_list.map.get(focusMorph.base, -1)

            if focusMorphIndex >= 0:
                isFrequency = True

                # The bigger this number, the lower mmi becomes
                usefulness += int(round( frequencyBonus * (1 - focusMorphIndex / frequency_list.len) ))

        # average frequency of unknowns (ie. how common the word is within your collection)
        F_k_avg = F_k // N_k if N_k > 0 else F_k
        usefulness += F_k_avg

        # add bonus for studying recent learned knowns (reinforce)
        for morpheme in new_knowns:
            locs = knownDb.getMatchingLocs(morpheme)
            if locs:
                ivl = min(1, max(loc.maturity for loc in locs))
                # TODO: maybe average this so it doesnt favor long sentences
                usefulness += reinforceNewVocabWeight // ivl

        if any(morpheme.pos == '動詞' for morpheme in unknowns):  # FIXME: this isn't working???
            usefulness += C('verb bonus')

        usefulness = 99999 - min(99999, usefulness)

        # difference from optimal length range (too little context vs long sentence)
        lenDiffRaw = min(N - C('min good sentence length'),
                         max(0, N - C('max good sentence length')))
        lenDiff = min(9, abs(lenDiffRaw))

        # Fill in various fields/tags on the note based on cfg
        fs = split_fields(flds)

        # clear any 'special' tags, the appropriate will be set in the next few lines
        ts = [t for t in ts if t not in (
            notReadyTag, compTag, vocabTag, freshTag)]

        # apply penalty for cards that aren't prioritized for learning
        if not (isPriority or isFrequency):
            usefulness += noPriorityPenalty

        # determine card type
        if N_m == 0:  # sentence comprehension card, m+0
            ts.append(compTag)
            if skip_comprehension_cards:
                usefulness += 1000000 # Add a penalty to put these cards at the end of the queue
        elif N_k == 1:  # new vocab card, k+1
            ts.append(vocabTag)
            if maxtype == 0: # Only update focus fields on 'new' card types.
                setField(mid, fs, field_focus_morph, focusMorph.base)
                setField(mid, fs, field_focus_morph_pos, focusMorph.pos)
        elif N_k > 1:  # M+1+ and K+2+
            ts.append(notReadyTag)
            if maxtype == 0: # Only update focus fields on 'new' card types.
                setField(mid, fs, field_focus_morph, ', '.join([u.base for u in unknowns]))
                setField(mid, fs, field_focus_morph_pos, ', '.join([u.pos for u in unknowns]))
        else:  # only case left: we have k+0, but m+1 or higher, so this card does not introduce a new vocabulary -> card for newly learned morpheme
            ts.append(freshTag)
            if skip_fresh_cards:
                usefulness += 1000000 # Add a penalty to put these cards at the end of the queue
            if maxtype == 0: # Only update focus fields on 'new' card types.
                setField(mid, fs, field_focus_morph, ', '.join([u.base for u in unmatures]))
                setField(mid, fs, field_focus_morph_pos, ', '.join([u.pos for u in unmatures]))

        # calculate mmi
        mmi = 100000 * N_k + 1000 * lenDiff + int(round(usefulness))
        if C('set due based on mmi'):
            nid2mmi[nid] = mmi
            
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
        flds_ = join_fields(fs)
        if flds != flds_ or tags != tags_:  # only update notes that have changed
            csum = field_checksum(fs[0])
            sfld = strip_html(fs[getSortFieldIndex(mid)])
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

    allDb.meta['last_preferences'] = get_preferences()
    allDb.meta['last_maturities'] = new_maturities
    allDb.meta['last_updated'] = int(time.time() + 0.5)

    printf('Updated %d notes in %f sec' % (N_notes, time.time() - t_0))

    if cfg('saveDbs'):
        mw.progress.update(label='Saving all/seen/known/mature dbs')
        allDb.save(getPathByLanguage(cfg('path_all'),language))
        seenDb.save(getPathByLanguage(cfg('path_seen'),language))
        knownDb.save(getPathByLanguage(cfg('path_known'),language))
        matureDb.save(getPathByLanguage(cfg('path_mature'),language))
        printf('Updated %d notes + saved dbs in %f sec' % (N_notes, time.time() - t_0))

    mw.progress.finish()
    return knownDb


def main():
    # begin-------------------
    if doProfile:
        pr = cProfile.Profile()
        pr.enable()

    # load existing all.db for each language (all.db for default language, all_Japanese.db for Japanese etc..)
    languages = getLanguageList()
    for language in languages:
        fname = getPathByLanguage('all%s.db', language)
        mw.progress.start(label='Loading existing %s' % fname, immediate=True)
        t_0 = time.time()
        cur = getAllDb(language) if cfg('loadAllDb') else None
        printf('Loaded %s in %f sec' % (fname, time.time() - t_0))
        mw.progress.finish()

        # update all.db
        allDb = mkAllDb(cur, language)
        # there was an (non-critical-/non-"exception"-)error but error message was already displayed
        if not allDb:
            mw.progress.finish()
        else:
 
            # merge in external.db (or external_Japanese.db, external_French.db etc)
            mw.progress.start(label='Merging ext.db', immediate=True)
            ext = MorphDb(getPathByLanguage(cfg('path_ext'),language), ignoreErrors=True)
            allDb.merge(ext)
            mw.progress.finish()

            # update notes
            knownDb = updateNotes(allDb, language)

            # update stats and refresh display
            stats.updateStats(knownDb)
            mw.toolbar.draw()


    # finish-------------------
    if doProfile:
        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
