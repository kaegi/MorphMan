# -*- coding: utf-8 -*-
from anki.hooks import addHook
from anki.lang import _
from aqt.utils import tooltip

from ..util import addBrowserCardSelectionCmd, mw, infoMsg
from ..preferences import get_preference as cfg


def pre(b): return {'cards': [], 'browser': b}


def per(st, c):
    st['cards'].append(c)
    return st


def post(st):
    for c in st['cards']:
        mw.reviewer.cardQueue.append(c)

    browser = st['browser']
    mw.progress.timer(100, lambda: browser.close(), False)

    tooltip(_('Immediately reviewing {} cards'.format(len(st['cards']))))
    return st


def runLearnNow():
    label = 'MorphMan: Learn Now'
    tooltip_msg = 'Immediately review the selected new cards'
    shortcut = cfg('set learn now key')
    addBrowserCardSelectionCmd(label, pre, per, post, tooltip=tooltip_msg, shortcut=(shortcut,))


addHook('profileLoaded', runLearnNow)
