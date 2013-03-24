== Requirements ==
python2.7.3 (http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi)

pywin32 r218 (http://sourceforge.net/projects/pywin32/files/pywin32/Build%20218/pywin32-218.win32-py2.7.exe/download)

pyaudio v19 (http://people.csail.mit.edu/hubert/pyaudio/packages/pyaudio-0.2.7.py27.exe)

imagemagick (http://www.imagemagick.org/download/binaries/ImageMagick-6.8.3-10-Q16-x86-dll.exe)

ITH v3 [included] (https://code.google.com/p/interactive-text-hooker/downloads/detail?name=ITH_UpdaterV3.rar&can=2&q=)

LAME [included]

== Components ==
record.py - a daemon that records txt, audio, img, and indexing files. driven by clipboard (ITH proc)

convert.py - a daemon that converts bmp->png and wav->mp3

mash.py - creates .tsv for show (and each part) based on timing .dat files. uses translation db object to generate english lines as well

mkMuvluvTranslationDb.py - creates muvluv.db, an object that provides a mapping between jap and eng lines (used with mash)

== Instructions ==
1) start VN and setup ITH so that it's capturing game text to the clipboard

2) capture txt/img/audio with `python record.py prefix` where "prefix" is a name
   used for all media files captured. recommended to use it to denote the section
   of the game and/or choices being made.
   do not use the same name with multiple runs

3) convert all media with `python convery.py [mediaPath]`. runs as daemon
   constantly looking for files in mediaPath (defaults to 'media') as they
   become available and converting as neccessary.
   specify a 2nd argument to enable converting the "misc" directory, but this
   should only be done after record.py is no longer running

4) [optional] create a database of translations for lines of the script.
   see mkMuvLuvTranslationDb.py for an example, but effectively it's just a
   pickled dictionary of Japanese->English.
   Not only does this provide a Meaning field, but it helps detect+correct
   various errors in the Expression field due to ITH capturing improperly.

5) use `python mash.py showName mediaPath` to create a .tsv file ready for Anki
   import based on all the lines in the timing .dat files and corresponding
   resource files.
   * also links context sentences -2,-1,+1, and +2 by default, but can modify
     "contexts" list at top of script to change.
   * can also change "transDbPath" at top of script to change where Meaning
     field translations are looked for if you did step #4.
   * it may be neccessary to modify parseLine or getMeaning depending on the vn
     for better results (ie. Speaker & Meaning field, fix ITH issues)

6) copy the mediaPath dir to your collections.media directory and import the
   tsv file into an Anki deck.
   most likely you'll want the 'decks/showName - total.tsv' file.
