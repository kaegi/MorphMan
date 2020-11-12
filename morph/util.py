# -*- coding: utf-8 -*-
import codecs
import datetime
from os import path

from anki.hooks import addHook
from anki.notes import Note
from aqt import mw
from aqt.browser import Browser
from aqt.qt import *
from aqt.utils import showCritical, showInfo
from .preferences import get_preference, init_preferences

# hack: typing is compile time anyway, so, nothing bad happens if it fails, the try is to support anki < 2.1.16
try:
    from aqt.pinnedmodules import typing  # pylint: disable=W0611 # See above hack comment
    from typing import Any, Dict, List, Optional, Callable, TypeVar

    T = TypeVar('T')

except ImportError:
    pass

###############################################################################
# Global data
###############################################################################
_allDb = None


def allDb():
    global _allDb

    # Force reload if all.db got deleted
    all_db_path = get_preference('path_all')
    reload = not path.isfile(all_db_path)

    if reload or (_allDb is None):
        from .morphemes import MorphDb
        _allDb = MorphDb(all_db_path, ignoreErrors=True)
    return _allDb


###############################################################################
# Preferences
###############################################################################


addHook('profileLoaded', init_preferences)
# ToDo: - move this hook to better home


def getFilter(note):
    # type: (Note) -> Optional[dict]
    return getFilterByTagsAndType(note.model()['name'], note.tags)


def getFilterByMidAndTags(mid, tags):
    # type: (Any, List[str]) -> Optional[Dict[...]]
    return getFilterByTagsAndType(mw.col.models.get(mid)['name'], tags)


def getFilterByTagsAndType(type, tags):
    # type: (str, List[str]) -> Optional[Dict[...]]
    for f in get_preference('Filter'):
        if type != f['Type'] and f['Type'] is not None: # None means all note types are ok
            continue
        if not set(f['Tags']) <= set(tags):
            continue  # required tags have to be subset of actual tags
        return f
    return None

def getReadEnabledModels():
    included_types = set()
    include_all = False
    for f in get_preference('Filter'):
        if f.get('Read', True):
            if f['Type'] is not None:
                included_types.add(f['Type'])
            else:
                include_all = True
                break
    return included_types, include_all

def getModifyEnabledModels():
    included_types = set()
    include_all = False
    for f in get_preference('Filter'):
        if f.get('Modify', True):
            if f['Type'] is not None:
                included_types.add(f['Type'])
            else:
                include_all = True
                break
    return included_types, include_all

###############################################################################
# Fact browser utils
###############################################################################
def doOnNoteSelection(b, preF, perF, postF, progLabel):
    # type: (Browser, Callable[[Browser], T], Callable[[T, Note], T], Callable[[T], T], str) -> None
    st = preF(b)
    if not st:
        return

    nids = b.selectedNotes()
    mw.progress.start(label=progLabel, max=len(nids))
    for i, nid in enumerate(nids):
        mw.progress.update(value=i)
        n = mw.col.getNote(nid)
        st = perF(st, n)
    mw.progress.finish()

    st = postF(st)
    mw.col.updateFieldCache(nids)
    if not st or st.get('__reset', True):
        mw.reset()


def doOnCardSelection(b, preF, perF, postF):
    st = preF(b)
    if not st:
        return

    cids = b.selectedCards()
    for i, cid in enumerate(cids):
        card = mw.col.getCard(cid)
        st = perF(st, card)

    st = postF(st)
    if not st or st.get('__reset', True):
        mw.reset()


def addBrowserItem(menuLabel, func_triggered, tooltip=None, shortcut=None):
    def setupMenu(b):
        a = QAction(menuLabel, b)
        if tooltip:
            a.setStatusTip(tooltip)
        if shortcut:
            a.setShortcut(QKeySequence(*shortcut))
        a.triggered.connect(lambda l: func_triggered(b))
        b.form.menuEdit.addAction(a)

    addHook('browser.setupMenus', setupMenu)


def addBrowserNoteSelectionCmd(menuLabel, preF, perF, postF, tooltip=None, shortcut=None, progLabel='Working...'):
    # type: (str, Callable[[Browser], T], Callable[[T, Note], T], Callable[[T], T], Optional[str], Optional[Any], str) -> None
    """ This function sets up a menu item in the Anki browser. On being clicked, it will call one time `preF`, for
    every selected note `perF` and after everything `postF`. """
    addBrowserItem(menuLabel, lambda b: doOnNoteSelection(
        b, preF, perF, postF, progLabel), tooltip, shortcut)


def addBrowserCardSelectionCmd(menuLabel, preF, perF, postF, tooltip=None, shortcut=None):
    """ This function sets up a menu item in the Anki browser. On being clicked, it will call one time `preF`, for
    every selected card `perF` and after everything `postF`. """
    addBrowserItem(menuLabel, lambda b: doOnCardSelection(
        b, preF, perF, postF), tooltip, shortcut)


###############################################################################
# Logging and MsgBoxes
###############################################################################
def errorMsg(msg):
    showCritical(msg)
    printf(msg)


def infoMsg(msg):
    showInfo(msg)
    printf(msg)


def printf(msg):
    txt = '%s: %s' % (datetime.datetime.now(), msg)
    f = codecs.open(get_preference('path_log'), 'a', 'utf-8')
    f.write(txt + '\r\n')
    f.close()
    print(txt.encode('utf-8'))


def clearLog():
    f = codecs.open(get_preference('path_log'), 'w', 'utf-8')
    f.close()


###############################################################################
# Qt helper functions
###############################################################################
def mkBtn(txt, f, parent):
    b = QPushButton(txt)
    b.clicked.connect(f)
    parent.addWidget(b)
    return b

###############################################################################
# Mplayer settings
###############################################################################
# sound.mplayerCmd += [ '-fs' ]
