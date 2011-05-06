from anki.hooks import addHook
from ankiqt import mw

def morphInit():
   print 'morphInit'
   import morph.util
   import morph.extractMorphemes
   import morph.iPlusN
   import morph.viewMorphemes

mw.registerPlugin( 'Morphology', 20110505213517 )
addHook( 'init', morphInit )
