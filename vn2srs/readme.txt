== vn2srs ==
Version 0.1

vn2srs is a suite of tools for creating multimedia flash cards from a visual
novel. Primarily it is accomplished via ITH detecting and parsing game text,
which signals a recording program to record the current text, take a screenshot,
and save all the audio since the last line ITH detected.

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
2) Install imagemagick, check the option to add the binaries to your PATH.
3) Add python to your PATH or use full path when instructed below.
   ex: `python record.py` -> `C:\Python2.7\python.exe record.py`
4) Set your default audio input device so that it captures audio from your VN.
   Easiest way is to use Virtual Audio Cable, as each virtual sound output device
   has a corresponding input device that is linked to contain the same sound.
   Thus, have the VN use the virtual output device (probably by setting it as
   default) and set the corresponding virtual input device as system default.
   A poor alternative would be to have a microphone record from your speakers.

== Components ==
record.py - A daemon that records txt, audio, img, and indexing files.
    Driven by clipboard (via ITH)

convert.py - A daemon that converts bmp->png and wav->mp3

mash.py - Creates .tsv for show (and each part) based on timing .dat files.
    Uses translation.db object to generate Meaning entries as well as correct
    Expression lines in some cases.

mkMuvluvTranslationDb.py - Creates a translation.db which maps J->E lines for
    the game Muv-Luv Alternative (used with mash.py)

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
   * You can use the game's auto-read mode if it has one to completely automate
   the extraction process with the exception of making in-game choices and every
   so often stopping/resuming the recording with a different prefix in order to
   properly name files for different sections of the game.
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

== How it works ==
1) Interactive Text Hooker hooks underlying Windows GDI calls like TextOutA
in order to capture text printed by a process. Most popular VNs are already
supported but you can fix 'hcode' (hook code) to define a custom hook if needed
in order to add support for a new game (many can be found by searching online).
There is an option to automatically copy all text lines to the clipboard, which
we use to drive our recording system.

2) Virtual Audio Cable creates virtual audio devices in pairs of an output and
an input device, which are linked such that all sound delivered by applications
to the output device is also sent to the input device. This lets us record the
audio of applications by recording from the virtual input device while having
the app in question play sound with the virtual output device. Many applications
don't let you customize which sound input/output device they use, so most likely
you'll have to change your system default appropriately.

3) record.py starts a daemon that records all audio from your default audio
input device to a master audio file. It also detects changes to your system
clipboard and if text is copied to the clipboard (eg. if ITH parses a line of
game text) then it saves that text as the current line of the VN, saves the
audio between the current time and the time of the last line, and takes a
screenshot of the window of the VN. All of these resources are named according
to a provided "prefix" and a number (counting from 0).

4) Most VNs have an auto-read mode, which lets us run our game and recording
system in the background (though the game's window must still be on your
desktop and not have other windows on top of it in order for the screenshots to
work) without any effort on our part. Human intervention should only be required
to make in game choices, restart auto-read mode (many games cancel it after
cut-scenes or important events), or restart the record.py daemon in order to
change the prefix (useful for handling multiple routes and otherwise
categorizing).

5) The mash.py script looks in the provided media directory's misc/ dir for
index files (defaults to the .dat file index but can also use the .txt if
configured to at the top) and uses these to create .TSV files based on the line
in the index file, the corresponding media, context lines, and identifiers for
the line, show, time, etc. It also attempts to parse out the Speaker of the
line but this is generally different from game to game and so will probably
have to be customized in order to give useful results. Finally, it looks in a
translation.db file to look up Meanings based on Expressions as well as correct
said Expressions in some cases (ie. if a Meaning doesn't exist for a given
Expression, it tries various fixes to see if a Meaning can then be matched).

6) The translation.db object is a python dictionary of Expression string to
Meaning string, serialized to a file via pickle. If you don't want a monodeck,
you'll have to create one of these for the particular game you're processing.
Most likely you can contact the fan translations patch writers to obtain their
original script files or inspect the game resource files in both languages to
obtain some sort of mapping and then manipulate the data into the appropriate
object. An example of this is provided with mkMuvLuvTranslationDb.py, which
does exactly this with the Muv-Luv Alternative fan translation script files.
The scripts themselves were obtained from the English fan patch translators and
are included in the mla_scripts directory for reference.

7) Many VNs include lines that aren't voiced, so after we import our .TSV files
into Anki, we suspend lines as appropriate to our VN. For example, all Muv-Luv
lines without a speaker are unvoiced naration and the vast majority of those
spoken by the main character are unvoiced, so we suspend "Speaker:" as well as
"Speaker:武".

== How you can help ==
* Create a translation.db for various games or obtain the Japanese and English
scripts (try just asking the translation patch writers) so that others can
create one from them.

== Known Issues ==
* record.py will crash on some systems once the master session audio file in
  misc/ gets to 2GB, so break up sessions into smaller ones if this happens.

* the .png files are overly large and could probably be reduced with lossy
  compression and palette conversion
