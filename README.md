# MorphMan
MorphMan is an Anki addon that tracks what words you know, and utilizes that information to optimally reorder language cards. This
__greatly__ optimizes your learning queue, as you will only see sentences with exactly one unknown word (see
[i+1 principle](https://massimmersionapproach.com/table-of-contents/anki/morphman/#glossary) for a more detailed explanation).

# Installation (Anki 2.1)

Install MorphMan via [AnkiWeb](https://ankiweb.net/shared/info/900801631)  (**NOTE: The Anki Experimental V2 Scheduler is currently not supported, 
as it causes issues with MorphMan's scheduling**)  

# Installation (Anki 2.0)

To install MorphMan, download the latest .zip archive from [here](https://github.com/kaegi/MorphMan/releases)
and extract the files to your Anki2/addons_ (To find your Anki folder on Windows, enter "%appdata%" in the file explorer).
Your folder structure should look like this:

-   _Anki2/addons/morphman.py_
-   _Anki2/addons/morph/\*allFilesAndDirectories\*_

After restarting Anki, you should see an entry called _morphman_ under _Tools -> Add-ons_.
You can find information and troubleshooting tips [here](https://github.com/kaegi/MorphMan/wiki/Installation).

# Usage

MorphMan supports the following languages:
-   languages with spaces: __English__, __Russian__, __Spanish__, __Korean__, __Hindi__, __etc.__
-   __Japanese__: You must additionally install the _[Japanese Support](https://ankiweb.net/shared/info/3918629684)_ Anki addon
-   __Chinese__: For Anki 2.0, please use [Jieba-Morph](https://github.com/NinKenDo64/Jieba-Morph). Chinese is included in Morphman for Anki 2.1
-   __CJK Characters__: Morphemizer that splits sentence into characters and filters for Chinese-Japanese-Korean logographic/idiographic characters.
-   more languages can be added on request if morpheme-splitting-tools are available for it

See Matt VS Japan's [video tutorial](https://www.youtube.com/watch?v=dVReg8_XnyA) 
and accompanying [blog post](https://massimmersionapproach.com/table-of-contents/anki/morphman).  

See the [MorphMan wiki](https://github.com/kaegi/MorphMan/wiki) for more information.
