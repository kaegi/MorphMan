import argparse
import json
import sys

import spacy


POS_BLACKLIST = [
    'SPACE',
    'PUNCT',
    'NUM',
]


def process_input(model):
    nlp = spacy.load(model)
    for line in sys.stdin:
        doc = nlp(line)
        result = list(map(lambda t: _createMorpheme(t, doc), filter(_filter_tokens, doc)))
        print(json.dumps(result))
        sys.stdout.flush()


def _createMorpheme(token, doc):
    reading = token.lemma_
    if "reading_forms" in doc.user_data:
        reading_forms = doc.user_data["reading_forms"]
        if token.i < len(reading_forms):
            reading = "" if reading_forms[token.i] is None else reading_forms[token.i]

    return {
        'norm': token.lemma_,
        'base': token.norm_,
        'inflected': token.text,
        'read': reading,
        'pos': token.pos_,
        'subPos': "*"
    }


def _filter_tokens(token):
    return not token.pos_ in POS_BLACKLIST


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""Listens on stdin and process given text with spaCy. After starting pass in
    line delimited text to process with spaCy using the given model. The output is a json
    object containing norm, base, inflected, read, pos, and subpos."""
    )
    parser.add_argument('--model', required=True, help="Model to use for processing text. ")
    args = parser.parse_args()
    process_input(args.model)
