== Requirements ==
Note: other versions may be acceptable, but only those below have been tested

python v2.7.3 (http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi)

pywin32 r218 (http://sourceforge.net/projects/pywin32/files/pywin32/Build%20218/pywin32-218.win32-py2.7.exe/download)

pyaudio v0.2.7 (http://people.csail.mit.edu/hubert/pyaudio/packages/pyaudio-0.2.7.py27.exe)

imagemagick v6.8.3 (http://www.imagemagick.org/download/binaries/ImageMagick-6.8.3-10-Q16-x86-dll.exe)

ITH v3 [included] (https://code.google.com/p/interactive-text-hooker/downloads/detail?name=ITH_UpdaterV3.rar&can=2&q=)

LAME v3.99.5 [included]

== Setup ==
1) Install python followed by pywin32 and pyaudio.
2) Install imagemagick, check the option to add the binaries to your PATH if not already selected
3) Add python to your PATH or call the full path instead of just `python` when instructed below
   ex: `python record.py` -> `C:\Python2.7\python.exe record.py`
4) Set your default audio input device so that it captures audio from your VN.
   Easiest way is to use Virtual Audio Cable, as each virtual sound output device
   has a corresponding input device that is linked to contain the same sound.
   Thus, have the VN use the virtual output device (probably by setting it as
   default) and set the corresponding virtual input device as system default.

== Components ==
record.py - a daemon that records txt, audio, img, and indexing files. driven by clipboard (via ITH)

convert.py - a daemon that converts bmp->png and wav->mp3

mash.py - creates .tsv for show (and each part) based on timing .dat files. uses translation db object to generate Meaning entries as well as correct Expression line in some cases

mkMuvluvTranslationDb.py - creates a translation.db which maps J->E lines in Muv-Luv Alternative (used with mash.py)

== Instructions ==
1) Start VN and setup ITH so that it's capturing game text to the clipboard.

2) Capture txt/img/audio with `python record.py prefix` where "prefix" is a name
   used for all media files captured this session. Recommended to use it to denote
   the section of the game and/or choices being made.
   * Do not use the same name with multiple runs as it will overwrite the old files.
   * You must switch focus to the VN's window after starting so it knows which
   window to take screenshots from, but the first 3 seconds focus doesn't matter
   and you can freely use your computer so long as no window overlaps the VN
   window (and any sound from other applications must use a different audio device).
   * Stop recording with Ctrl-C.

3) Convert all media with `python convert.py [mediaPath]`. Runs as daemon
   constantly looking for files in mediaPath (defaults to 'media') as they
   become available and converting as neccessary.
   * Specify a 2nd argument to enable converting the "misc" directory, but this
   should only be done after record.py is no longer running.
   * Stop converting with Ctrl-C.

4) [optional] Create a database of translations for lines of the script.
   See mkMuvLuvTranslationDb.py for an example, but effectively it's just a
   pickled dictionary of Expression->Meaning (usually Japanese->English).
   * Not only does this provide a Meaning field, but it helps detect+correct
   various errors in the Expression field due to ITH capturing improperly.

5) Use `python mash.py showName mediaPath` to create a .tsv file ready for Anki
   import based on all the lines in the timing .dat files and corresponding
   resource files.
   * Also links context sentences -2,-1,+1, and +2 by default, but can modify
   "contexts" list at top of script to change.
   * It may be neccessary to modify parseLine or getMeaning depending on the vn
   for better results (ie. Speaker & Meaning field, fix ITH issues)

6) Copy the mediaPath dir to your collections.media directory and import the
   tsv file into an Anki deck.
   * You can use the `decks/showName - total.tsv` to get all the sections of
   the last media directory mashed.

== Known Issues ==
* record.py will crash on some systems once the master session audio file in
  misc/ gets to 2GB, so break up sessions into smaller ones if this happens.

* the .png files are overly large and could probably be reduced with lossy
  compression or palette conversion
