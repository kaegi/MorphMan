from PyQt4.QtCore import *
from PyQt4.QtGui import *
import util
import morphemes as M

def pre( ed ):
   tags, ok = QInputDialog.getText( ed, 'Enter Tags', 'Tags', QLineEdit.Normal, 'myMorph' )
   if not ok: return
   msStr, ok = QInputDialog.getText( ed, 'Enter morphemes', 'Morphemes', QLineEdit.Normal, '' )
   if not ok: return
   bs = util.getBlacklist( ed )
   ms = [ tuple( row.split('\t') ) for row in msStr.split('\n') ]
   return { 'mp':M.mecab(None), 'ms':ms, 'tags':tags, 'bs':bs, 'ed':ed }
def per( st, f ):
   ms = M.getMorphemes( st['mp'], f['Expression'], bs=st['bs'] )
   #QMessageBox( None, 'Note', 'Comparing %s to %s' % (str(ms), str(st['ms']) ) )
   for x in ms:
      if x in st['ms']:
         tags = addTags( st['tags'], f.tags )
         f.tags = canonifyTags( tags )
   #      QMessageBox( None, 'Note', 'found morpheme in expr, set tag' )
   return st
def post( st ):
   st['mp'].kill()

util.addDoOnSelectionBtn( 'Mass tagging', 'Mass tagging', 'Tagging...', pre, per, post )
