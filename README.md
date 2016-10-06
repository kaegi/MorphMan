# MorphMan
MorphMan is an Anki plugin that reorders Japanese cards based on the words you known. This
__greatly__ optimizes your learning queue as you only get sentences with exactly one unknown word (see
[I+1 principle](http://rtkwiki.koohii.com/wiki/I%2B1) for a more detailed explanation).

# Usage
Cards generated with [SubtitleMemorize](https://github.com/ChangSpivey/SubtitleMemorize) will work out-of-the-box. No extra configuration needed.

Anki shortcuts (these are important for effective studying):
- `Ctrl-M`: regenerate morpheme database from your Anki cards and set due date for new cards; **you will have to do that after you import your language cards**
- `K` when seeing a _new_ card: mark morphemes in currently shown card as _known_ and skip to the next card
- `L` when seeing a _new_ or _reviewing_ a card: show cards that have the same focus morph (morpheme that you don't know well)

MorphMan requires at least on card that has exactly one unknown morpheme. In case there are only ones with no unknown or more than one unknown morphemes it will skip all new cards, so you will get no new cards. You can then either select cards you want to learn manually or create new ones.

See [MorphMan wiki](http://rtkwiki.koohii.com/wiki/Morph_Man) much more information.

# Installation

To install MorphMan download the .zip archive from the [here](https://github.com/ChangSpivey/MorphMan/releases)
and extract all files except *README.md* and *LICENSE* to your *Documents/Anki/addons* folder.

This plugin works for following languages:
-   Every language that uses spaces to seperate its words (English, Russian, Spanish, etc.).
-   Japanese. In this case you need will additionally need to install the *[Japanese Support](https://ankiweb.net/shared/info/3918629684)* plugin in Anki.
-   More languages can be easily added if that is requested and morpheme-splitting-tools are available for it.

### Japanese cards on a 64-bit-only Linux distribution
The Japanese Support plugin does not work on 64-bit-only Linux distributions. You will have to install mecab (tool to split japanese sentences into its morphemes) and its dictionary.

Installation...

- ...on Arch Linux: [`mecab-ipadic`](https://aur.archlinux.org/packages/mecab-ipadic/) from AUR
- ...on Ubuntu (unnecessary for current versions): see [here](https://gist.github.com/YoshihitoAso/9048005) (untested)
- ...from source (if your japanese is good): [`mecab source`](https://taku910.github.io/mecab/).

After restarting Anki you should see an entry called *morphman* under *Tools -> Add-ons*.
