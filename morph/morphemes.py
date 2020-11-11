# -*- coding: utf-8 -*-
import codecs
import gzip
import os
import pickle as pickle
import sqlite3

from abc import ABC, abstractmethod

import re

try:
    import aqt
except:
    pass

# hack: typing is compile time anyway, so, nothing bad happens if it fails, the try is to support anki < 2.1.16
try:
    from aqt.pinnedmodules import typing  # pylint: disable=W0611 # See above hack comment
    from typing import Dict, Set
except ImportError:
    pass


# need some fallbacks if not running from anki and thus morph.util isn't available
try:
    from .util import errorMsg
except ImportError:
    def errorMsg(msg):
        pass

try:
    from .preferences import get_preference as cfg
except:
    def cfg(s):
        return None

def char_set(start, end):
    # type: (str, str) -> set
    return set(chr(c) for c in range(ord(start), ord(end) + 1))


kanji_chars = char_set('㐀', '䶵') | char_set('一', '鿋') | char_set('豈', '頻')


################################################################################
# Lexical analysis
################################################################################

class Morpheme:
    def __init__(self, norm, base, inflected, read, pos, subPos):
        """ Initialize morpheme class.

        POS means part-of-speech.

        Example morpheme infos for the expression "歩いて":

        :param str norm: 歩く [normalized base form]
        :param str base: 歩く
        :param str inflected: 歩い  [mecab cuts off all endings, so there is not て]
        :param str read: アルイ
        :param str pos: 動詞
        :param str subPos: 自立

        """
        # values are created by "mecab" in the order of the parameters and then directly passed into this constructor
        # example of mecab output:    "歩く     歩い    動詞    自立      アルイ"
        # matches to:                 "base     infl    pos     subPos    read"
        self.norm = norm if norm is not None else base
        self.base = base
        self.inflected = inflected
        self.read = read
        self.pos = pos  # type of morpheme determined by mecab tool. for example: u'動詞' or u'助動詞', u'形容詞'
        self.subPos = subPos

    def __setstate__(self, d):
        """ Override default pickle __setstate__ to initialize missing defaults in old databases
        """
        self.norm = d['norm'] if 'norm' in d else d['base']
        self.base = d['base']
        self.inflected = d['inflected']
        self.read = d['read']
        self.pos = d['pos']
        self.subPos = d['subPos']

    def __eq__(self, o):
        return all([isinstance(o, Morpheme), self.norm == o.norm, self.base == o.base, self.inflected == o.inflected,
                    self.read == o.read, self.pos == o.pos, self.subPos == o.subPos,
                    ])

    def __hash__(self):
        return hash((self.norm, self.base, self.inflected, self.read, self.pos, self.subPos))

    def base_kanji(self):
        # type: () -> set
        # todo: profile and maybe cache
        return set(self.base) & kanji_chars

    def getGroupKey(self):
        # type: () -> str

        if cfg('Option_IgnoreGrammarPosition'):
            return '%s\t%s' % (self.norm, self.read)
        else:
            return '%s\t%s\t%s\t' % (self.norm, self.read, self.pos)

    def isProperNoun(self):
        return (self.subPos == '固有名詞')

    def show(self):  # str
        return '\t'.join([self.norm, self.base, self.inflected, self.read, self.pos, self.subPos])


def ms2str(ms):  # [(Morpheme, locs)] -> Str
    return '\n'.join(['%d\t%s' % (len(m[1]), m[0].show()) for m in ms])


class MorphDBUnpickler(pickle.Unpickler):

    def find_class(self, cmodule, cname):
        # Override default class lookup for this module to allow loading databases generated with older
        # versions of the MorphMan add-on.
        if cmodule.endswith('.morph.morphemes'):
            return globals()[cname]
        return pickle.Unpickler.find_class(self, cmodule, cname)

def getMorphemes(morphemizer, expression, note_tags=None):
    expression = replaceBracketContents(expression)

    # go through all replacement rules and search if a rule (which dictates a string to morpheme conversion) can be
    # applied
    replace_rules = cfg('ReplaceRules')
    if note_tags is not None and replace_rules is not None:
        note_tags_set = set(note_tags)
        for (filter_tags, regex, morphemes) in replace_rules:
            if not set(filter_tags) <= note_tags_set:
                continue

            # find matches
            split_expression = re.split(
                regex, expression, maxsplit=1, flags=re.UNICODE)

            if len(split_expression) == 1:
                continue  # no match
            assert (len(split_expression) == 2)

            # make sure this rule doesn't lead to endless recursion
            if len(split_expression[0]) >= len(expression) or len(split_expression[1]) >= len(expression):
                continue

            a_morphs = getMorphemes(
                morphemizer, split_expression[0], note_tags)
            b_morphs = [Morpheme(mstr, mstr, mstr, mstr,
                                 'UNKNOWN', 'UNKNOWN') for mstr in morphemes]
            c_morphs = getMorphemes(
                morphemizer, split_expression[1], note_tags)

            return a_morphs + b_morphs + c_morphs

    ms = morphemizer.getMorphemesFromExpr(expression)

    return ms

square_brackets_regex = re.compile(r'\[[^\]]*\]')
round_brackets_regex = re.compile(r'（[^）]*）')
slim_round_brackets_regexp = re.compile(r'\([^\)]*\)')

def replaceBracketContents(expression):
    if cfg('Option_IgnoreBracketContents'):
        if square_brackets_regex.search(expression):
            expression = square_brackets_regex.sub('', expression)

    if cfg('Option_IgnoreRoundBracketContents'):
        if round_brackets_regex.search(expression):
            expression = round_brackets_regex.sub('', expression)

    if cfg('Option_IgnoreSlimRoundBracketContents'):
        if slim_round_brackets_regexp.search(expression):
            expression = slim_round_brackets_regexp.sub('', expression)

    return expression

################################################################################
# Morpheme db manipulation
################################################################################

class Location(ABC):
    def __init__(self, weight):
        self.weight = weight
        self.maturity = 0

    @abstractmethod
    def show(self):
        pass


class Nowhere(Location):
    def __init__(self, tag, weight=0):
        super(Nowhere, self).__init__(weight)
        self.tag = tag

    def show(self):
        return '%s@%d' % (self.tag, self.maturity)


class Corpus(Location):
    """A corpus we want to use for priority, without storing more than morpheme frequencies."""

    def __init__(self, name, weight):
        super(Corpus, self).__init__(weight)
        self.name = name

    def show(self):
        return '%s*%s@%d' % (self.name, self.weight, self.maturity)


class TextFile(Location):
    def __init__(self, filePath, lineNo, maturity, weight=1):
        super(TextFile, self).__init__(weight)
        self.filePath = filePath
        self.lineNo = lineNo
        self.maturity = maturity

    def show(self):
        return '%s:%d@%d' % (self.filePath, self.lineNo, self.maturity)


class AnkiDeck(Location):
    """ This maps to/contains information for one note and one relevant field like u'Expression'. """

    def __init__(self, noteId, fieldName, fieldValue, guid, maturity, weight=1):
        super(AnkiDeck, self).__init__(weight)
        self.noteId = noteId
        self.fieldName = fieldName  # for example u'Expression'
        self.fieldValue = fieldValue  # for example u'それだけじゃない'
        self.guid = guid
        # list of intergers, one for every card -> containg the intervals of every card for this note
        self.maturities = None
        self.maturity = maturity
        self.weight = weight

    def show(self):
        return '%d[%s]@%d' % (self.noteId, self.fieldName, self.maturity)


def altIncludesMorpheme(m, alt):
    # type: (Morpheme, Morpheme) -> bool

    return m.norm == alt.norm and (m.base == alt.base or m.base_kanji() <= alt.base_kanji())

    
class MorphDb:
    @staticmethod
    def mergeFiles(aPath, bPath, destPath=None,
                   ignoreErrors=False):  # FilePath -> FilePath -> Maybe FilePath -> Maybe Book -> IO MorphDb
        a, b = MorphDb(aPath, ignoreErrors), MorphDb(bPath, ignoreErrors)
        a.merge(b)
        if destPath:
            a.save(destPath)
        return a

    @staticmethod
    def mkFromFile(path, morphemizer, maturity=0):  # FilePath -> Maturity? -> IO Db
        """Returns None and shows error dialog if failed"""
        d = MorphDb()
        try:
            d.importFile(path, morphemizer, maturity=maturity)
        except (UnicodeDecodeError, IOError) as e:
            return errorMsg('Unable to import file. Please verify it is a UTF-8 text file and you have '
                            'permissions.\nFull error:\n%s' % e)
        return d

    def __init__(self, path=None, ignoreErrors=False):  # Maybe Filepath -> m ()
        self.db = {}  # type: Dict[Morpheme, Set[Location]]
        self.groups = {}  # Map NormMorpheme {Set(Morpheme)}
        self.meta = {}
        if path:
            try:
                self.load(path)
            except IOError:
                if not ignoreErrors:
                    raise
        self.analyze()

    # Serialization
    def show(self):  # Str
        s = ''
        for m, ls in self.db.items():
            s += '%s\n' % m.show()
            for l in ls:
                s += '  %s\n' % l.show()
        return s

    def showLocDb(self):  # m Str
        s = ''
        for l, ms in self.locDb().items():
            s += '%s\n' % l.show()
            for m in ms:
                s += '  %s\n' % m.show()
        return s

    def showMs(self):  # Str
        return ms2str(sorted(self.db.items(), key=lambda it: it[0].show()))

    def save(self, path):  # FilePath -> IO ()
        par = os.path.split(path)[0]
        if not os.path.exists(par):
            os.makedirs(par)
        f = gzip.open(path, 'wb')

        data = {'db': self.db,
                'meta': self.meta
                }
        pickle.dump(data, f, -1)
        f.close()
        if cfg('saveSQLite'):
            save_db(self.db, path)

    def load(self, path):  # FilePath -> m ()
        f = gzip.open(path)
        try:
            data = MorphDBUnpickler(f).load()
            if 'meta' in data:
                self.meta = data['meta']
                db = data['db']
            else:
                db = data
            for m, locs in db.items():
                self.addMLs1(m, locs)
        except ModuleNotFoundError as e:
            aqt.utils.showInfo(
                "ModuleNotFoundError was thrown. That probably means that you're using database files generated in "
                "the older versions of MorphMan. To fix this issue, please refer to the written guide on database "
                "migration (copy-pasteable link will appear in the next window): "
                "https://gist.github.com/InfiniteRain/1d7ca9ad307c4203397a635b514f00c2")
            raise e
        f.close()

    # Returns True if DB has variations that can match 'm'.
    def matches(self, m):  # Morpheme
        # type: (Morpheme) -> bool
        gk = m.getGroupKey()
        ms = self.groups.get(gk, None)
        if ms is None:
            return False

        # Fuzzy match to variations
        return any(altIncludesMorpheme(m, alt) for alt in ms)

    # Returns set of morph locations that can match 'm'
    def getMatchingLocs(self, m):  # Morpheme
        # type: (Morpheme) -> Set[Location]
        locs = set()
        gk = m.getGroupKey()
        ms = self.groups.get(gk, None)
        if ms is None:
            return locs

        # Fuzzy match to variations
        for variation in ms:
            if altIncludesMorpheme(m, variation):
                locs.update(self.db[variation])
        return locs

    # Adding
    def clear(self):  # m ()
        self.db = {}
        self.groups = {}
        self.meta = {}

    def addMLs(self, mls):  # [ (Morpheme,Location) ] -> m ()
        for m, loc in mls:
            if m in self.db:
                self.db[m].add(loc)
            else:
                self.db[m] = {loc}
                gk = m.getGroupKey()
                if gk not in self.groups:
                    self.groups[gk] = {m}
                else:
                    self.groups[gk].add(m)

    def addMLs1(self, m, locs):  # Morpheme -> {Location} -> m ()
        if m in self.db:
            self.db[m].update(locs)
        else:
            self.db[m] = set(locs)
            gk = m.getGroupKey()
            if gk not in self.groups:
                self.groups[gk] = {m}
            else:
                self.groups[gk].add(m)

    def addMsL(self, ms, loc):  # [Morpheme] -> Location -> m ()
        self.addMLs((m, loc) for m in ms)

    def addFromLocDb(self, ldb):  # Map Location {Morpheme} -> m ()
        for l, ms in ldb.items():
            self.addMLs([(m, l) for m in ms])

    # returns number of added entries
    def merge(self, md):  # Db -> m Int
        new = 0
        for m, locs in md.db.items():
            if m in self.db:
                new += len(locs - self.db[m])
                self.db[m].update(locs)
            else:
                new += len(locs)
                self.addMLs1(m, locs)

        return new

    # FilePath -> Morphemizer -> Maturity? -> IO ()
    def importFile(self, path, morphemizer, maturity=0):
        f = codecs.open(path, encoding='utf-8')
        inp = f.readlines()
        f.close()

        for i, line in enumerate(inp):
            ms = getMorphemes(morphemizer, line.strip())
            self.addMLs((m, TextFile(path, i + 1, maturity)) for m in ms)

    # Analysis (local)
    def frequency(self, m):  # Morpheme -> Int
        return sum(getattr(loc, 'weight', 1) for loc in self.getMatchingLocs(m))

    # Analysis (global)
    def locDb(self, recalc=True):  # Maybe Bool -> m Map Location {Morpheme}
        # type: (bool) ->  Dict[Location, Set[Morpheme]]
        if hasattr(self, '_locDb') and not recalc:
            return self._locDb  # pylint: disable=E0203 # pylint is wrong
        self._locDb = d = {}  # type: Dict[Location, Set[Morpheme]]
        for m, ls in self.db.items():
            for l in ls:
                if l in d:
                    d[l].add(m)
                else:
                    d[l] = {m}
        return d

    def fidDb(self, recalc=True):  # Maybe Bool -> m Map FactId Location
        if hasattr(self, '_fidDb') and not recalc:
            return self._fidDb  # pylint: disable=E0203 # pylint is wrong
        self._fidDb = d = {}
        for loc in self.locDb():
            try:
                d[(loc.noteId, loc.guid, loc.fieldName)] = loc
            except AttributeError:
                pass  # location isn't an anki fact
        return d

    def countByType(self):  # Map Pos Int
        d = {}
        for m in self.db.keys():
            d[m.pos] = d.get(m.pos, 0) + 1
        return d

    def analyze(self):  # m ()
        self.posBreakdown = self.countByType()
        self.kCount = len(self.groups)
        self.vCount = len(self.db)

    def analyze2str(self):  # m Str
        self.analyze()
        posStr = '\n'.join('%d\t%d%%\t%s' % (v, 100. * v / self.vCount, k)
                           for k, v in self.posBreakdown.items())
        return 'Total normalized morphemes: %d\nTotal variations: %d\nBy part of speech:\n%s' % (
            self.kCount, self.vCount, posStr)


# sqlite code

def connect_db(path):
    conn = sqlite3.connect(path)
    return conn

def drop_table(cur, name):
    sql = "drop table if exists %s;"%(name)
    cur.execute(sql)

def create_table(cur, name, fields, extra = ""):
    sql = "create table %s (%s%s);"%(name,fields, extra)
    cur.execute(sql)

# helper functions to convert morphman objectsi into sql tuples
def transcode_item(item):
    return (item.norm, item.base, item.inflected, item.read, item.pos, item.subPos)

def transcode_location(loc):
    return (loc.noteId, loc.fieldName, loc.fieldValue, loc.maturity, loc.guid, loc.weight)
    
def save_db_all_morphs(cur, db, tname):

    # we cannot use the name 'all' for a table
    # since it is a reserved word in sql
    if tname == 'all':
        # used 'morphs' instead
        tname = 'morphs'

    # fields  of table to be created
    fields = "morphid, norm, base, inflected, read, pos, subpos"

    drop_table(cur, tname)

    create_table(cur, tname,fields, ", primary key (morphid)")

    def transcode_item_pair(el):
        # el is a pair: <the morphid (an int), morph object>
        # this is a helper function for the map below
        item = el[1]
        return (el[0],)+ transcode_item(item)

    # convert the info in the db into list of tuples
    tuples = map(transcode_item_pair, enumerate(db.keys()))

    # insert them all at once
    cur.executemany("INSERT INTO %s (%s) VALUES(?,?,?,?,?,?,?);"%(tname,fields), tuples)

def read_db_all_morphs(cur):
    # read the morphs as a dictionary, where the key is the morph tuple and
    # the value is the morphid
    # see save_db_all_morphs for the schema of the morphs relation
    
    cur.execute("SELECT * FROM morphs;")
    rows = cur.fetchall()
    forDict = map(lambda x: (x[1:], x[0]), rows)
    return dict(forDict)
    
def save_db_locations(cur, db, tname='locations'):
    # save a morphman db as a table in database
    # it is usually faster to drop the table than delete/update the tuples
    # in it
    drop_table(cur, tname)

    # fields for the table
    fields = "morphid, noteid, field, fieldvalue, maturity, guid, weight"
    create_table(cur, tname,fields,
       ", primary key (morphid, noteid, field), foreign key (morphid) references morphs")

    # we need to know the morphid of each morph
    # so we can properly reference them in the table locations
    # (see foreign key constraint in the table create above)
    # in theory we have this info, but this mades the code
    # simpler and less error prone and it the time penalty
    # seems to be minimal
    
    # morphs is a dictionary that maps
    #  transcode_item(morph) to its morphid (int)
    morphs = read_db_all_morphs(cur)

    # we need to convert the db of morphs into a list of tuples
    # where the first value is the morphid (stored in the table
    # we just created)
    
    # a morph might have multiple locations
    # map each morph in db into a list [morphidlist, location info]
    locationsLists =map(lambda x: # this is a pair of morph and list of locations
               list(map(lambda y: (morphs[transcode_item(x[0])],)+transcode_location(y),x[1])),
               db.items())

    # flatten the list... because we have a list of lists (one list per morph)
    tuples = [val for sublist in locationsLists for val in sublist]

    cur.executemany("INSERT INTO %s (%s) VALUES(?,?,?,?,?,?,?);"%(tname,fields), tuples)
        

def save_db(db, path):
    # assume that the directory is already created...
    # exceptions will handle the errors

    # we need to wedge this code in here, while we refactor the code...
    # morphman stores info in a bunch of files.
    #
    # database with each "file" as a table
    # so let use the basefilename of the relation as
    tname = os.path.basename(path)
    dirName = os.path.dirname(path)
    # it ends with .db so cut it
    assert (len(tname)> 3 and tname[-3:] == '.db'), "extension is no longer .db?"

    # name of the morphs to save (all, known, etc.)
    tname = tname[:-3]
    dbName = dirName + '/morphman.sqlite'

    conn = connect_db(dbName)
    with conn:
        cur = conn.cursor()
        # it looks like we only need to save the "all" data
        # the others seem to be subsets of it (based on the
        # maturity field)
        if (tname == 'all'):
            # save morphs
            save_db_all_morphs(cur, db, tname)
            # then we need to save the locations
            # every morph in location is guaranteed in db at this point
            save_db_locations(cur, db)
        conn.commit()

    print("Saved to sqlite Tname [%s] dbname [%s]"%(tname, dbName))
