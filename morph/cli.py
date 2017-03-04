from __future__ import absolute_import

import argparse
import codecs
from collections import Counter, defaultdict
import glob
import itertools
import os.path
import signal
import sys

from morph.morphemes import MorphDb
from morph.morphemizer import SpaceMorphemizer, MecabMorphemizer, CjkCharMorphemizer
import morph


def die(msg):
    print >>sys.stderr, msg
    sys.exit(1)


def warn(msg):
    print >>sys.stderr, msg


CLI_PROFILE_PATH = None


def profile_base_path():
    '''Dies if we can't find it.'''
    if CLI_PROFILE_PATH is not None:
        return os.path.dirname(CLI_PROFILE_PATH)

    # To do this right we need, at a minimum, the logic in
    # the method aqt.profiles.ProfileManager._defaultBase .
    #
    # For now it's convenient to avoid depending on Anki's code, so
    # just pick a couple of branches of that logic that suffice for
    # me and many users, with a clear error message.
    candidates = [
        os.path.expanduser('~/Anki'),
        os.path.expanduser('~/Documents/Anki'),
    ]
    for d in candidates:
        if os.path.exists(d):
            return d

    die('''\
This script is too naive to find your Anki folder.  Tried:
  %s
Try passing the profile folder explicitly with `--profile`.
''' % ('\n  '.join(candidates)))


def profile_path():
    '''Look for the Anki profile.  Dies unless it finds exactly one.'''
    if CLI_PROFILE_PATH is not None:
        path = CLI_PROFILE_PATH
        if not os.path.isdir(path):
            die('No such folder at Anki profile path (from --profile): ' + path)
        dbs_path = os.path.join(path, 'dbs')
        if not os.path.isdir(dbs_path):
            die('No MorphMan dbs folder in Anki profile (from --profile): ' + dbs_path)
        return path

    base = profile_base_path()

    pattern = os.path.join(base, '*', 'dbs', '')
    db_paths = glob.glob(pattern)
    if not db_paths:
        die('No candidate MorphMan db paths in Anki folder: %s' % (pattern,))
    if len(db_paths) > 1:
        die('Multiple possible MorphMan db paths: %s' % (' '.join(db_paths),))

    return os.path.dirname(os.path.dirname(db_paths[0]))


def db_path(db_name):
    return os.path.join(profile_path(), 'dbs', db_name + '.db')


def load_db(db_name):
    path = db_path(db_name)
    if not os.access(path, os.R_OK):
        die('can\'t read db file: %s' % (path,))
    return MorphDb(path)


MIZERS = {
    'space': SpaceMorphemizer(),
    'mecab': MecabMorphemizer(),
    'cjkchar': CjkCharMorphemizer(),
}


def cmd_dump(args):
    db_name = args.name
    inc_freq = bool(args.freq)

    db = load_db(db_name)
    for m in db.db.keys():
        m_formatted = m.show().encode('utf-8')
        if inc_freq:
            print '%d\t%s' % (db.frequency(m), m_formatted)
        else:
            print m_formatted


def cmd_count(args):
    files = args.files
    mizer = MIZERS[args.mizer]

    freqs = Counter()
    for path in files:
        with codecs.open(path, 'r', 'utf-8') as f:
            for line in f.readlines():
                freqs.update(mizer.getMorphemesFromExpr(line.strip()))

    for m, c in freqs.most_common():
        print '%d\t%s' % (c, m.show().encode('utf-8'))


def cmd_next(args):
    notes_path = args.notes
    prio_path = args.prio
    mizer = MIZERS[args.mizer]

    known = load_db('known')

    candidates = defaultdict(list)
    with codecs.open(notes_path, 'r', 'utf-8') as f:
        for line in f.readlines():
            note = line.strip()
            text = note.split('\t', 1)[0]
            unknowns = [m for m in mizer.getMorphemesFromExpr(text)
                        if m not in known.db]
            if len(unknowns) == 1:
                candidates[unknowns[0].show()].append(note)

    with codecs.open(prio_path, 'r', 'utf-8') as f:
        for line in f.readlines():
            freq, m = line.strip().split('\t', 1)
            m_cite = m.split('\t', 1)[0]
            for cand in candidates[m]:
                print (u'%s\t%s\t%s' % (freq, m_cite, cand)).encode('utf-8')


def fix_sigpipe():
    '''Set this process to exit quietly on SIGPIPE, like a good shell-pipeline citizen.'''
    # For context, see e.g. https://stevereads.com/2015/09/25/python-sigpipe/.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def main():
    '''Usage: `mm --help`.

    This function is meant to be invoked via the tiny wrapper script `mm`.
    '''
    fix_sigpipe()

    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', metavar='DIR', help='path to Anki profile (if absent, we try some guesses)')
    subparsers = parser.add_subparsers(title='subcommands')

    p_dump = subparsers.add_parser('dump', help='dump a MorphMan db in text form',
                                   description='Dump a MorphMan database to stdout in a plain-text format.')
    p_dump.set_defaults(action=cmd_dump)
    p_dump.add_argument('name', metavar='NAME', help='database to dump (all, known, ...)')
    p_dump.add_argument('--freq', action='store_true', help='include frequency as known to MorphMan')

    def add_mizer(parser):
        parser.add_argument('--mizer', default='mecab', choices=MIZERS.keys(),
                            metavar='NAME',
                            help='how to split morphemes (%s) (default %s)'
                                 % (', '.join(MIZERS.keys()), 'mecab'))

    p_count = subparsers.add_parser('count', help='count morphemes in a corpus',
                        description='Count all morphemes in the given files and emit a frequency table.')
    p_count.set_defaults(action=cmd_count)
    p_count.add_argument('files', nargs='*', metavar='FILE', help='input files of text to morphemize')
    add_mizer(p_count)

    p_next = subparsers.add_parser('next', help='find next notes to study from a corpus')
    p_next.set_defaults(action=cmd_next)
    p_next.add_argument('prio', metavar='FREQS', help='file of morphemes to study, with frequencies')
    p_next.add_argument('notes', metavar='NOTES', help='file of newline-terminated notes, each tab-separated fields starting with the text')
    add_mizer(p_next)

    args = parser.parse_args()
    global CLI_PROFILE_PATH
    if args.profile is not None:
        CLI_PROFILE_PATH = os.path.expanduser(os.path.normpath(args.profile))
    args.action(args)
