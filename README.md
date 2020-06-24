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
- languages with spaces: **English**, **Russian**, **Spanish**, **Hindi**, **etc.**
- **Japanese**: You must additionally install the _[Japanese Support](https://ankiweb.net/shared/info/3918629684)_ Anki addon
- **Chinese**: For Anki 2.0, please use [Jieba-Morph](https://github.com/NinKenDo64/Jieba-Morph). Chinese is included in Morphman for Anki 2.1
- **CJK Characters**: Morphemizer that splits sentence into characters and filters for Chinese-Japanese-Korean logographic/idiographic characters.
- **Korean**: You must additionally download the Korean dictionary [here](https://mega.nz/folder/P8xG1SLC#zhn4-HwEt3ks9mcBW-_n5w) and put it in morph/deps/mecab. 
- more languages can be added on request if morpheme-splitting-tools are available for it

See Matt VS Japan's [video tutorial](https://www.youtube.com/watch?v=dVReg8_XnyA)
and accompanying [blog post](https://massimmersionapproach.com/table-of-contents/anki/morphman).
See the [MorphMan wiki](https://github.com/kaegi/MorphMan/wiki) for more information.

# Development
- Set up local environment:
  - the best is to use a python virtual environment
  - pip install pylint
  - pip install PyQt5
  - install Anki source code, for example:
      - wget https://github.com/dae/anki/archive/2.1.16.tar.gz
      - tar -xzvf 2.1.16.tar.gz
      - export PYTHONPATH=./anki-2.1.16
- Run tests: `python test.py`
- Build Qt Developer UI with `python scripts/build_ui.py`
- Install git commit hook to run tests and pylint
  ` scripts/setup_dev.sh`
