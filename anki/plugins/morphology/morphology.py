from anki.hooks import addHook
from ankiqt import mw

def morphInit():
   print 'morphInit'
   import morph.util
   import morph.exportMorphemes
   import morph.setIPlusN
   import morph.setVocabRank
   import morph.setUnknowns
   import morph.viewMorphemes
   import morph.manager
   import morph.massTagger

mw.registerPlugin( 'Morphology', 20110505213517 )
addHook( 'init', morphInit )
