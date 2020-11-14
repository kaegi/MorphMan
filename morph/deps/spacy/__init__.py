from anki.hooks import addHook

def init_spacy(morphemizerManager):
  addHook('AnkiSpacy.modelAvailable',
    lambda model: register_morphemizer(morphemizerManager, model))
  addHook('AnkiSpacy.modelUnavailable',
    lambda model: unregister_morphemizer(morphemizerManager, model))

def register_morphemizer(morphemizerManager, model):
  from .morphemizer import SpacyMorphemizer
  morphemizerManager.addMorphemizer(
    SpacyMorphemizer(model['name'], model['path'])
  )

def unregister_morphemizer(morphemizerManager, model):
  morphemizerManager.removeMorphemizer(model['name'])
