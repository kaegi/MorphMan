# -*- coding: utf-8 -*-
import codecs
import importlib
import time
from anki.tags import TagManager

from functools import partial

import aqt.main
from anki.utils import splitFields, joinFields, stripHTML, intTime, fieldChecksum

from .morphemes import Location, Morpheme
from . import stats
from . import util
from .morphemes import MorphDb, AnkiDeck, getMorphemes
from .morphemizer import getMorphemizerByName
from .util import printf, mw, cfg, cfg1, errorMsg, jcfg, jcfg2, getFilter, getFilterByMidAndTags
from .util_external import memoize

# hack: typing is compile time anyway, so, nothing bad happens if it fails, the try is to support anki < 2.1.16
try:
    from aqt.pinnedmodules import typing
    from typing import Any, Dict, Set
except ImportError:
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
    N_notes = db.scalar('select count() from notes')
    N_enabled_notes = 0  # for providing an error message if there is no note that is used for processing
    mw.progress.start(label='Prep work for all.db creation', max=N_notes, immediate=True)

    if not all_db:
        all_db = MorphDb()
    fidDb = all_db.fidDb()
    locDb = all_db.locDb(recalc=False)  # fidDb() already forces locDb recalc

    mw.progress.update(label='Generating all.db data')
    for i, (nid, mid, flds, guid, tags) in enumerate(db.execute('select id, mid, flds, guid, tags from notes')):
        if i % 500 == 0:
            mw.progress.update(value=i)
        C = partial(cfg, mid, None)

        note = mw.col.getNote(nid)
        note_cfg = getFilter(note)
        if note_cfg is None:
            continue
        morphemizer = getMorphemizerByName(note_cfg['Morphemizer'])

        N_enabled_notes += 1

        mats = [(0.5 if ivl == 0 and ctype == 1 else ivl) for ivl, ctype in
                db.execute('select ivl, type from cards where nid = :nid', nid=nid)]
        if C('ignore maturity'):
            mats = [0 for mat in mats]
        ts, alreadyKnownTag = TAG.split(tags), jcfg('Tag_AlreadyKnown')
        if alreadyKnownTag in ts:
            mats += [C('threshold_mature') + 1]

        for fieldName in note_cfg['Fields']:
            try:  # if doesn't have field, continue
                fieldValue = extractFieldData(fieldName, flds, mid)
            except KeyError:
                continue
            except TypeError:
                mname = mw.col.models.get(mid)['name']
                errorMsg('Failed to get field "{field}" from a note of model "{model}". Please fix your config.py '
                         'file to match your collection appropriately and ignore the following error.'.format(
                          model=mname, field=fieldName))
                raise

            loc = fidDb.get((nid, guid, fieldName), None)
            if not loc:
                loc = AnkiDeck(nid, fieldName, fieldValue, guid, mats)
                ms = getMorphemes(morphemizer, fieldValue, ts)
                if ms:  # TODO: this needed? should we change below too then?
                    locDb[loc] = ms
            else:
                # mats changed -> new loc (new mats), move morphs
                if loc.fieldValue == fieldValue and loc.maturities != mats:
                    newLoc = AnkiDeck(nid, fieldName, fieldValue, guid, mats)
                    locDb[newLoc] = locDb.pop(loc)
                # field changed -> new loc, new morphs
                elif loc.fieldValue != fieldValue:
                    newLoc = AnkiDeck(nid, fieldName, fieldValue, guid, mats)
                    ms = getMorphemes(morphemizer, fieldValue, ts)
                    locDb.pop(loc)
                    locDb[newLoc] = ms

    if N_enabled_notes == 0:
        mw.progress.finish()
        errorMsg('There is no card that can be analyzed or be moved. Add cards or (re-)check your configuration under '
                 '"Tools -> MorhpMan Preferences" or in "Anki/addons/morph/config.py" for mistakes.')
        return None

    printf('Processed all %d notes in %f sec' % (N_notes, time.time() - t_0))
    mw.progress.update(value=i, label='Creating all.db object')
    all_db.clear()
    all_db.addFromLocDb(locDb)
    if cfg1('saveDbs'):
        mw.progress.update(value=i, label='Saving all.db to disk')
        all_db.save(cfg1('path_all'))
        printf('Processed all %d notes + saved all.db in %f sec' % (N_notes, time.time() - t_0))
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
    N_notes = db.scalar('select count() from notes')
    mw.progress.start(label='Updating data', max=N_notes, immediate=True)
    fidDb = allDb.fidDb(recalc=True)
    loc_db = allDb.locDb(recalc=False)  # type: Dict[Location, Set[Morpheme]]

    # read tag names
    compTag, vocabTag, freshTag, notReadyTag, alreadyKnownTag, priorityTag, tooShortTag, tooLongTag, frequencyTag = tagNames = jcfg(
        'Tag_Comprehension'), jcfg('Tag_Vocab'), jcfg('Tag_Fresh'), jcfg('Tag_NotReady'), jcfg(
        'Tag_AlreadyKnown'), jcfg('Tag_Priority'), jcfg('Tag_TooShort'), jcfg('Tag_TooLong'), jcfg('Tag_Frequency')
    TAG.register(tagNames)
    badLengthTag = jcfg2().get('Tag_BadLength')

    # handle secondary databases
    mw.progress.update(label='Creating seen/known/mature from all.db')
    seenDb = filterDbByMat(allDb, cfg1('threshold_seen'))
    knownDb = filterDbByMat(allDb, cfg1('threshold_known'))
    matureDb = filterDbByMat(allDb, cfg1('threshold_mature'))
    mw.progress.update(label='Loading priority.db')
    priorityDb = MorphDb(cfg1('path_priority'), ignoreErrors=True).db

    mw.progress.update(label='Loading frequency.txt')
    frequencyListPath = cfg1('path_frequency')
    try:
        with codecs.open(frequencyListPath, encoding='utf-8') as f:
            frequency_list = [line.strip().split('\t')[0] for line in f.readlines()]
    except FileNotFoundError:
        frequency_list = []
        pass  # User does not have a frequency.txt

    frequencyListLength = len(frequency_list)

    if cfg1('saveDbs'):
        mw.progress.update(label='Saving seen/known/mature dbs')
        seenDb.save(cfg1('path_seen'))
        knownDb.save(cfg1('path_known'))
        matureDb.save(cfg1('path_mature'))

    mw.progress.update(label='Updating notes')

    # prefetch jcfg for fields
    field_focus_morph = jcfg('Field_FocusMorph')
    field_unknown_count = jcfg('Field_UnknownMorphCount')
    field_unmature_count = jcfg('Field_UnmatureMorphCount')
    field_morph_man_index = jcfg('Field_MorphManIndex')
    field_unknowns = jcfg('Field_Unknowns')
    field_unmatures = jcfg('Field_Unmatures')
    field_unknown_freq = jcfg('Field_UnknownFreq')

    for i, (nid, mid, flds, guid, tags) in enumerate(db.execute('select id, mid, flds, guid, tags from notes')):
        ts = TAG.split(tags)
        if i % 500 == 0:
            mw.progress.update(value=i)
        C = partial(cfg, mid, None)

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

        # Determine un-seen/known/mature and i+N
        unseens, unknowns, unmatures, new_knowns = set(), set(), set(), set()
        for morpheme in morphemes:
            if not seenDb.matches(morpheme):
                unseens.add(morpheme)
            if not knownDb.matches(morpheme):
                unknowns.add(morpheme)
            if not matureDb.matches(morpheme):
                unmatures.add(morpheme)
                if knownDb.matches(morpheme):
                    new_knowns.add(morpheme)

        # Determine MMI - Morph Man Index
        N, N_s, N_k, N_m = len(morphemes), len(unseens), len(unknowns), len(unmatures)

        # Bail early for lite update
        if N_k > 2 and C('only update k+2 and below'):
            continue

        # add bonus for morphs in priority.db and frequency.txt
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
            focusMorphString = focusMorph.base
            try:
                focusMorphIndex = frequency_list.index(focusMorphString)
                isFrequency = True
                frequencyWeight = C('frequency.txt weight scale')

                # The bigger this number, the lower mmi becomes
                usefulness += (frequencyListLength - focusMorphIndex) * frequencyWeight
            except ValueError:
                pass

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
        mmi = 100000 * N_k + 1000 * lenDiff + usefulness
        if C('set due based on mmi'):
            nid2mmi[nid] = mmi

        # Fill in various fields/tags on the note based on cfg
        fs = splitFields(flds)

        # clear any 'special' tags, the appropriate will be set in the next few lines
        ts = [t for t in ts if t not in (notReadyTag, compTag, vocabTag, freshTag)]

        # determine card type
        if N_m == 0:  # sentence comprehension card, m+0
            ts.append(compTag)
        elif N_k == 1:  # new vocab card, k+1
            ts.append(vocabTag)
            setField(mid, fs, field_focus_morph, focusMorph.base)
        elif N_k > 1:  # M+1+ and K+2+
            ts.append(notReadyTag)
            setField(mid, fs, field_focus_morph, '')
        elif N_m == 1:  # we have k+0, and m+1, so this card does not introduce a new vocabulary -> card for newly learned morpheme
            ts.append(freshTag)
            setField(mid, fs, field_focus_morph, next(iter(unmatures)).base)
        else:  # only case left: we have k+0, but m+2 or higher, so this card does not introduce a new vocabulary -> card for newly learned morpheme
            ts.append(freshTag)
            setField(mid, fs, field_focus_morph, '')

        # set type agnostic fields
        setField(mid, fs, field_unknown_count, '%d' % N_k)
        setField(mid, fs, field_unmature_count, '%d' % N_m)
        setField(mid, fs, field_morph_man_index, '%d' % mmi)
        setField(mid, fs, field_unknowns, ', '.join(u.base for u in unknowns))
        setField(mid, fs, field_unmatures, ', '.join(u.base for u in unmatures))
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
        if not jcfg('Option_SetNotRequiredTags'):
            unnecessary = [priorityTag, tooShortTag, tooLongTag]
            ts = [tag for tag in ts if tag not in unnecessary]

        # update sql db
        tags_ = TAG.join(TAG.canonify(ts))
        flds_ = joinFields(fs)
        if flds != flds_ or tags != tags_:  # only update notes that have changed
            csum = fieldChecksum(fs[0])
            sfld = stripHTML(fs[getSortFieldIndex(mid)])
            ds.append(
                {'now': now, 'tags': tags_, 'flds': flds_, 'sfld': sfld, 'csum': csum, 'usn': mw.col.usn(), 'nid': nid})

    mw.progress.update(value=i, label='Updating anki database...')
    mw.col.db.executemany(
        'update notes set tags=:tags, flds=:flds, sfld=:sfld, csum=:csum, mod=:now, usn=:usn where id=:nid', ds)

    # Now reorder new cards based on MMI
    mw.progress.update(value=i, label='Updating new card ordering...')
    ds = []

    # "type = 0": new cards
    # "type = 1": learning cards [is supposed to be learning: in my case no learning card had this type]
    # "type = 2": review cards
    for (cid, nid, due) in db.execute('select id, nid, due from cards where type = 0'):
        if nid in nid2mmi:  # owise it was disabled
            due_ = nid2mmi[nid]
            if due != due_:  # only update cards that have changed
                ds.append({'now': now, 'due': due_, 'usn': mw.col.usn(), 'cid': cid})

    mw.col.db.executemany('update cards set due=:due, mod=:now, usn=:usn where id=:cid', ds)
    mw.reset()

    printf('Updated notes in %f sec' % (time.time() - t_0))
    mw.progress.finish()
    return knownDb


def main():
    # load existing all.db
    mw.progress.start(label='Loading existing all.db', immediate=True)
    t_0 = time.time()
    cur = util.allDb(reload=True) if cfg1('loadAllDb') else None
    printf('Loaded all.db in %f sec' % (time.time() - t_0))
    mw.progress.finish()

    # update all.db
    allDb = mkAllDb(cur)
    if not allDb:  # there was an (non-critical-/non-"exception"-)error but error message was already displayed
        mw.progress.finish()
        return

    # merge in external.db
    mw.progress.start(label='Merging ext.db', immediate=True)
    ext = MorphDb(cfg1('path_ext'), ignoreErrors=True)
    allDb.merge(ext)
    mw.progress.finish()

    # update notes
    knownDb = updateNotes(allDb)

    # update stats and refresh display
    stats.updateStats(knownDb)
    mw.toolbar.draw()

    # set global allDb
    util._allDb = allDb
