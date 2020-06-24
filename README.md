# MorphMan

<a title="Rate on AnkiWeb" href="https://ankiweb.net/shared/info/900801631"><img src="https://glutanimate.com/logos/ankiweb-rate.svg"></a>
<br>
MorphMan is an Anki addon that tracks what words you know, and utilizes that information to optimally reorder language cards. This
**greatly** optimizes your learning queue, as you will only see sentences with exactly one unknown word (see
[i+1 principle](https://massimmersionapproach.com/table-of-contents/anki/morphman/#glossary) for a more detailed explanation).

This fork has added Korean integration. All credit goes to them. See the github repository [here](https://github.com/kaegi/MorphMan).


# Installation (Anki 2.1)

To install MorphMan with Korean, download this repository extract the files to your Anki2/addons\_ (To find your Anki folder on Windows, enter "%appdata%" in the file explorer).
Your folder structure should look like this:

- _Anki2/addons/MorphMan-Folder
- _Anki2/addons/MorphMan-Folder/morph/\*allFilesAndDirectories\*_

After restarting Anki, you should see an entry called _morphman_ under _Tools -> Add-ons_.
You can find information and troubleshooting tips [here](https://github.com/kaegi/MorphMan/wiki/Installation).

# Usage

MorphMan supports the following languages:
- languages with spaces: **English**, **Russian**, **Spanish**, **Hindi**, **etc.**
- **Japanese**: You must additionally install the _[Japanese Support](https://ankiweb.net/shared/info/3918629684)_ Anki addon
- **Chinese**: For Anki 2.0, please use [Jieba-Morph](https://github.com/NinKenDo64/Jieba-Morph). Chinese is included in Morphman for Anki 2.1
- **CJK Characters**: Morphemizer that splits sentence into characters and filters for Chinese-Japanese-Korean logographic/idiographic characters.
- **Korean**: You must additionally download the Korean dictionary [here](https://github.com/Pusnow/mecab-ko-dic-msvc), rename it "mecab-ko-dic" and put it in Anki2/addons/Morphman/morph/deps/mecab. 
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
