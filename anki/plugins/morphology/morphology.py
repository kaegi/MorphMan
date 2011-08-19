from anki.hooks import addHook
from ankiqt import mw

def morphInit():
   import morph.util
   import morph.exportMorphemes
   import morph.setIPlusN
   import morph.setVocabRank
   import morph.setUnknowns
   import morph.viewMorphemes
   import morph.manager
   import morph.massTagger
   import morph.setMatch
   import morph.auto

mw.registerPlugin( 'Morphology', 17201108172228 )
addHook( 'init', morphInit )
