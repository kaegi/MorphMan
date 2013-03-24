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
?
