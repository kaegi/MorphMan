# import spacy
import json
####################################################################################################
# spacy Morphemizer
####################################################################################################
import os
import subprocess

from ...morphemes import Morpheme
from ...morphemizer import Morphemizer
from ...preferences import get_preference
from ...subprocess_util import platform_subprocess_args
from ...util import printf


class SpacyMorphemizer(Morphemizer):
    """
    Morphemizer based on the spaCy NLP
    """

    def __init__(self, model_name):
        super(SpacyMorphemizer, self).__init__()
        self.model_name = model_name
        self.proc = None

    def _getMorphemesFromExpr(self, e):
        if not self.proc:
            path = os.path.join(os.path.dirname(__file__), 'extract_morphemes.py')
            cmd = [get_preference('path_python'), path, '--model', self.model_name]
            printf(f"Spawning process for spacy: {cmd}")
            self.proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                **platform_subprocess_args()
            )

        self.proc.stdin.write(e.encode('utf-8') + b'\n')
        self.proc.stdin.flush()
        morphs = json.loads(self.proc.stdout.readline())
        results = [
            Morpheme(
                m['norm'],
                m['base'],
                m['inflected'],
                m['read'],
                m['pos'],
                m['subPos']) for m in morphs]

        return results

    def getDescription(self):
        return f'spaCy - {self.model_name}'

    def getName(self):
        return self.model_name
