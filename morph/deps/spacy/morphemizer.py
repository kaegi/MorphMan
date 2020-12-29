import spacy

####################################################################################################
# spacy Morphemizer
####################################################################################################
from ...morphemes import Morpheme
from ...morphemizer import Morphemizer

class SpacyMorphemizer(Morphemizer):
    """
    Morphemizer based on the spaCy NLP processor
    """
    def __init__(self, model_name, model_path):
        super(SpacyMorphemizer, self).__init__()
        self.model_name = model_name
        self.model_path = model_path
        self.nlp = None

    def _getMorphemesFromExpr(self, e):
        if not self.nlp:
            self.nlp = spacy.load(self.model_path)

        doc = self.nlp(e)
        return list(map(lambda t: self._createMorpheme(t, doc), filter(self.filter_tokens, doc)))

    def _createMorpheme(self, token, doc):
        reading = token.lemma_

        if "reading_forms" in doc.user_data:
            reading_forms = doc.user_data["reading_forms"]
            if token.i < len(reading_forms):
                reading = "" if reading_forms[token.i] is None else reading_forms[token.i]

        return Morpheme(
            norm=token.lemma_,
            base=token.norm_,
            inflected=token.text,
            read=reading,
            pos=token.pos_,
            subPos="*")

    def getDescription(self):
        return f'spaCy - {self.model_name}'

    def getName(self):
        return self.model_name

    @staticmethod
    def filter_tokens(token):
        return not (token.pos_ == 'PUNCT' or token.pos_ == 'NUM')
