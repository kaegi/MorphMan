# -*- coding: utf-8 -*-
from anki.hooks import addHook
from aqt.sound import av_player
from ..util import addBrowserNoteSelectionCmd, runOnce
from ..preferences import get_preference as cfg
import re

soundReg = r"\[sound:(.+?)\]"

def pre(b): return {'vid2nid': {}}


def per(st, n):
    for f in cfg('batch media fields', n.mid):
        try:
            r = re.search(soundReg, n[f])
            if r:
                st['vid2nid'][r.group(1)] = n.id
                break
        except KeyError:
            pass
    return st


def post(st):
    # TODO: queue all the files in a big list with `loadfile {filename} 1` so you can skip back and forth easily
    # when user chooses, use `get_file_name`
    av_player.clear_queue_and_maybe_interrupt()
    for vid, nid in st['vid2nid'].items():
        av_player.insert_file(vid)
    st['__reset'] = False
    return st


@runOnce
def runBatchPlay():
    label = 'MorphMan: Batch Play'
    tooltipMsg = 'Play all the videos for the selected cards'
    shortcut = cfg('set batch play key')
    addBrowserNoteSelectionCmd(label, pre, per, post, tooltip=tooltipMsg, shortcut=(shortcut,))


addHook('profileLoaded', runBatchPlay)
