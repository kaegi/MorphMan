# MorphMan
MorphMan is an Anki plugin that reorders Japanese cards based on the words you known. This
greatly optimizes your learning queue as you only get sentences with one unknown word (see
[I+1 principle](http://rtkwiki.koohii.com/wiki/I%2B1) for a more detailed explanation).

# Installation
MorphMan uses a tool called *mecab* to split a sentence into its individual words (morphemes).
To install that program there are two possibilities:

1. install the *[Japanese Support](https://ankiweb.net/shared/info/3918629684)* plugin in Anki
2. compile *[mecab](https://taku910.github.io/mecab/)* and install executable in your system path

The first way is easier and therefore recommended. The second way can be used as fallback for
systems that are not supported by the *Japanese Support* plugin.

To install MorphMan download the .zip archive from the [MorphMan GitHub Repository](https://github.com/ChangSpivey/MorphMan)
and extract all files (except *README.md* and *LICENSE*) to your *Documents/Anki/addons* folder.

After restarting Anki you should see an entry called *morphman* under *Tools -> Add-ons*.
