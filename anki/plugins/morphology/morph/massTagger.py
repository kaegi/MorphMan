from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.utils import addTags, canonifyTags
import util
from util import infoMsg, errorMsg
import morphemes as M

def pre( ed ):
   tags, ok = QInputDialog.getText( ed, 'Enter Tags', 'Tags', QLineEdit.Normal, 'myMorph' )
   if not ok or not tags: return 'BAIL'
   path = QFileDialog.getOpenFileName( caption='Open db', directory=util.knownDbPath )
   if not path: return 'BAIL'
   bs = util.getBlacklist( ed )

   db = M.loadDb( path )
   return { 'mp':M.mecab(None), 'db':db, 'tags':unicode(tags), 'bs':bs, 'ed':ed }

def per( st, f ):
   ms = M.getMorphemes( st['mp'], f['Expression'], bs=st['bs'] )
   for m in ms:
      if m in st['db']:
         #tags = addTags( st['tags'], f.tags )
         #f.tags = canonifyTags( tags )
         st['ed'].deck.addTags( [f.id], st['tags'] )
         return st
   return st

def post( st ):
   util.killMecab( st )
   st['ed'].deck.reset()

util.addDoOnSelectionBtn( 'Mass tagging', 'Mass tagging', 'Tagging...', pre, per, post )
