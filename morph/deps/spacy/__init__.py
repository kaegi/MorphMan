import re
import subprocess

from .morphemizer import SpacyMorphemizer
from ...preferences import get_preference
from ...subprocess_util import platform_subprocess_args
from ...util import printf


def init_spacy(morphemizerRegistry):
    printf("Initializing Spacy!")

    python_path = get_preference('path_python')

    if python_path:
        models = _spacy_models(python_path)
        if models:
            for model in models:
                printf(f"Creating morphemizer for spacy model {model}.")
                register_morphemizer(morphemizerRegistry, model)
        else:
            printf("No models were installed for spaCy.")
    else:
        printf('Python path not specified in config.py.')


def _parse_morphemizers(info_command_result):
    m = re.search('^Models\\s+(.*)$', info_command_result, re.MULTILINE)
    return [x.strip() for x in m.group(1).split(',')]


def _spacy_models(python_path):
    cmd = [python_path, '-m', 'spacy', 'info']
    printf(f"Collecting spacy model info: {cmd}")

    result = subprocess.run(
        [python_path, '-m', 'spacy', 'info'],
        capture_output=True,
        **platform_subprocess_args())

    if result.returncode != 0:
        printf('Command to find spaCy models failed. Please ensure python is installed at the path '
               'given in config.py under the "path_python" key and spaCy is installed in that '
               'python installation')
        return None
    else:
        printf(result)
        output = result.stdout.decode('utf-8')
        printf(f"spaCy info returned the following: {output}")
        return _parse_morphemizers(output)


def register_morphemizer(morphemizerRegistry, model):
    morphemizerRegistry.addMorphemizer(SpacyMorphemizer(model))
