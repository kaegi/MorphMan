import importlib.util
import json
import re
import sys

# TODO: Figure out if we can just enumerate all SpaCY modules directly.
known_spacy_models = [
  ('en_core_web_sm', 'SpaCy English Core Web (small)'),
  ('en_core_web_md', 'SpaCy English Core Web (medium)'),
  ('en_core_web_lg', 'SpaCy English Core Web (large)'),
  ('es_core_web_sm', 'SpaCy Spanish Core News (small)'),
  ('es_core_web_md', 'SpaCy Spanish Core News (medium)'),
  ('es_core_web_lg', 'SpaCy Spanish Core News (large)'),
  ('fr_core_news_sm', 'SpaCy French Core News (small)'),
  ('fr_core_news_md', 'SpaCy French Core News (medium)'),
  ('fr_core_news_lg', 'SpaCy French Core News (large)'),
  ('it_core_news_sm', 'SpaCy Italian Core News (small)'),
  ('it_core_news_md', 'SpaCy Italian Core News (medium)'),
  ('it_core_news_lg', 'SpaCy Italian Core News (large)'),
  ('ja_core_news_sm', 'SpaCy Japanese Core News (small)'),
  ('ja_core_news_md', 'SpaCy Japanese Core News (medium)'),
  ('ja_core_news_lg', 'SpaCy Japanese Core News (large)'),
  ('ro_core_news_sm', 'SpaCy Romanian Core News (small)'),
  ('ro_core_news_md', 'SpaCy Romanian Core News (medium)'),
  ('ro_core_news_lg', 'SpaCy Romanian Core News (large)'),
  ('zh_core_news_sm', 'SpaCy Chinese Core Web (small)'),
  ('zh_core_news_md', 'SpaCy Chinese Core Web (medium)'),
  ('zh_core_news_lg', 'SpaCy Chinese Core Web (large)'),
]

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

def dump_parsers():
  parsers = []
  
  # Check for SudachiPy
  if importlib.util.find_spec('sudachipy') is not None:
    parsers.append(('sudachipy:a', 'Sudachi Japanese (narrow)'))
    parsers.append(('sudachipy:b', 'Sudachi Japanese (normal)'))
    parsers.append(('sudachipy:c', 'Sudachi Japanese (wide)'))

  # Check for spacy
  if importlib.util.find_spec('spacy') is not None:
    for m in known_spacy_models:
      if importlib.util.find_spec(m[0]) is not None:
        parsers.append(('spacy:' + m[0], m[1]))

  print(json.dumps(parsers))
  sys.stdout.flush()

def interactive_mode():
  module = sys.argv[2].split(':')
  if module[0] == 'spacy':
    import spacy
    nlp = spacy.load(module[1])

    for line in sys.stdin:
      doc = nlp(line)
      if ("reading_forms" in doc.user_data):
        def proc_morph(w):
          reading = doc.user_data["reading_forms"][w.i]
          reading = "" if reading is None else reading
          return (w.lemma_, w.norm_, w.text, reading, w.pos_, '*')
        result = [proc_morph(w) for w in doc]
      else:
        result = [(w.lemma_, w.norm_, w.text, w.lemma_, w.pos_, '*') for w in doc]
      print(json.dumps(result))
      sys.stdout.flush()
  elif module[0] == 'sudachipy':
    from sudachipy import tokenizer
    from sudachipy import dictionary

    if module[1] == 'a':
      mode = tokenizer.Tokenizer.SplitMode.A
    elif module[1] == 'b':
      mode = tokenizer.Tokenizer.SplitMode.B
    elif module[1] == 'c':
      mode = tokenizer.Tokenizer.SplitMode.C

    tokenizer_obj = dictionary.Dictionary().create()

    # Exclude morphemes with alpha-numeric characters
    alpha_num = re.compile('[a-zA-Z0-9０-９]')

    for line in sys.stdin:
      try:
        line = line.strip()
        def proc_morph(m):
          dform = m.dictionary_form()
          surf = m.surface()
          reading = m.reading_form()

          # Get the unconjugated reading
          if dform != surf:
            morphs2 = tokenizer_obj.tokenize(dform, mode)
            if len(morphs2) == 1 and morphs2[0].dictionary_form() == dform:
              reading = morphs2[0].reading_form()

          return (
            m.normalized_form(),
            dform,
            surf,
            reading,
            m.part_of_speech()[0],
            m.part_of_speech()[1],
          )

        result = [proc_morph(m) for m in tokenizer_obj.tokenize(line, mode) if alpha_num.search(m.surface()) is None]
      except:
        result = []
      #print(result)
      print(json.dumps(result))
      sys.stdout.flush()

if __name__ == '__main__':
  if sys.argv[1] == 'parsers':
    dump_parsers()
  elif sys.argv[1] == 'interact':
    interactive_mode()
