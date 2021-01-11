# MorphMan

<a title="Rate on AnkiWeb" href="https://ankiweb.net/shared/info/900801631"><img src="https://glutanimate.com/logos/ankiweb-rate.svg"></a>
<br>
MorphMan is an Anki addon that tracks what words you know, and utilizes that information to optimally reorder language cards. This
**greatly** optimizes your learning queue, as you will only see sentences with exactly one unknown word (see
[i+1 principle](https://massimmersionapproach.com/table-of-contents/anki/morphman/#glossary) for a more detailed explanation).

# Installation (Anki 2.1)

Install MorphMan via [AnkiWeb](https://ankiweb.net/shared/info/900801631)

# Installation (Anki 2.0)

To install MorphMan, download the latest .zip archive from [here](https://github.com/kaegi/MorphMan/releases)
and extract the files to your Anki2/addons\_ (To find your Anki folder on Windows, enter "%appdata%" in the file explorer).
Your folder structure should look like this:

- _Anki2/addons/morphman.py_
- _Anki2/addons/morph/\*allFilesAndDirectories\*_

After restarting Anki, you should see an entry called _morphman_ under _Tools -> Add-ons_.
You can find information and troubleshooting tips [here](https://github.com/kaegi/MorphMan/wiki/Installation).

# Usage

MorphMan supports the following languages:

- languages with spaces: **English**, **Russian**, **Spanish**, **Korean**, **Hindi**, **etc.**
- **Japanese**: You must additionally install the _[Japanese Support](https://ankiweb.net/shared/info/3918629684)_ Anki addon
- **Chinese**: For Anki 2.0, please use [Jieba-Morph](https://github.com/NinKenDo64/Jieba-Morph). Chinese is included in Morphman for Anki 2.1
- **CJK Characters**: Morphemizer that splits sentence into characters and filters for Chinese-Japanese-Korean logographic/idiographic characters.
- **spaCy**: [SpaCy](https://spacy.io/) is a free open-source library for Natural Language Processing in Python. See section below for more information. 
- more languages can be added on request if morpheme-splitting-tools are available for it

See Matt VS Japan's [video tutorial](https://www.youtube.com/watch?v=dVReg8_XnyA)
and accompanying [blog post](https://massimmersionapproach.com/table-of-contents/anki/morphman).
See the [MorphMan wiki](https://github.com/kaegi/MorphMan/wiki) for more information.

## spaCy
[SpaCy](https://spacy.io/) is a free open-source library for Natural Language Processing in Python.
Machine learning models for a variety of languages are available, including Chinese, Danish, Dutch,
English, French, German, Greek, Italian, Japanese, Lithuanian, Norwegian Bokmål, Polish,
Portuguese, Romanian, and Spanish. Additionally, spaCy provides the tools to train additional
language models if you desire.

### Requirements
* Current installation of python 3. (Currently tested on python 3.8.5)
* spaCy installed
* One or more desired language models installed and linked.

### Installation

1. Install python if it is not already. See the 
[python download page](https://www.python.org/downloads/) for more information.

2. Determine the path to you python executable and add it to `config.py`.
    On Unix/MacOs this can be done with the `which` command using a terminal
    ```
    > which python
    > /Users/someperson/workspace/spacy_test/venv/bin/python
    ```

    For Windows you can usually find with the `where` command using the command prompt. 
    ```
    C:\>where python
    C:\Users\someperson\AppData\Local\Microsoft\WindowsApps\python.exe
    ```
   
   Once you have that open config.py in your MorphMan installation and set 
   `path_python` to the path value.
   
   Change
   ```
   'path_python': None     
   ```
   to your path
   ```
   'path_python': '/Users/someperson/somepython/bin/python',
   ```

3. Install spaCy.

    Unix/MacOs
    ```
    python -m pip install spacy
    ```

    Windows
    ```
    py -m pip install spacy
    ```
   
   For more information installing spaCy see the 
   [installation instructions](https://spacy.io/usage).
   
4. Install and link the desired spaCy models.
   You must install the spaCy model and then make sure it is linked. For example, if you wanted 
   to use the German model `de_core_news_sm`. You would do the following.
   ```
   python -m spacy download de_core_news_sm
   python -m spacy link de_core_news_sm <link_name>
   ```
   
   "spaCy - `link_name`" is the name that will show up in MorphMan when selecting a morphemizer. 
   For example, if we did 
   ```
   python -m spacy link de_core_news_sm de
   ```
   
   then we should see "spaCy - de" as a morphemizer option.
   
    You can verify what models are installed for spaCy
    ```
    python -m spacy info
    
    ============================== Info about spaCy ==============================
    
    spaCy version    2.3.5
    Location         /Users/someperson/python3.8/site-packages/spacy
    Platform         macOS-10.15.7-x86_64-i386-64bit
    Python version   3.8.5
    Models           ja, de
    ```
   
   Here you can see two models have been installed and linked, `ja` and `de`.
   
   For more information installing spaCy models see the 
   [installation instructions](https://spacy.io/usage/models).

### Debugging
If you find you are having issues getting MoprhMan to recognize your installed models there may
be valuable log output in morphman log file. By default this log file should be in the root of your
Anki profile directory and called `morphman.log`. Please use the output of this log file when 
opening any issues.
 
# Development
- Set up local environment:
  - The best is to use a Python virtual environment and install prebuilt Anki wheels:
    ```
    python -m virtualenv pyenv
    source pyenv/bin/activate
    python -m pip install aqt==2.1.35 anki==2.1.35 pyqtwebengine pylint
    export PYTHONPATH=./
    ```
- Run tests: `python test.py`
- Build Qt Developer UI with `python scripts/build_ui.py`
- Install git commit hook to run tests and pylint
  ` scripts/setup_dev.sh`
