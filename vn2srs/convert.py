import glob, os, subprocess, time, sys

def mkPath( path, ext ):
    fdir, fname = os.path.split( path )
    fname_ = fname[:-3] + ext
    path_ = os.path.join( fdir, fname_ )
    return path_

def bmp2png( path ):
    print 'Converting bmp2png for %s' % path
    path_ = mkPath( path, 'png' )
    ret = subprocess.call( [ 'convert', path, path_ ], shell=True )
    if not ret:
        os.remove( path )

def wav2mp3( path ):
    print 'Converting wav2mp3 for %s' % path
    path_ = mkPath( path, 'mp3' )
    ret = subprocess.call( [ 'lame', '--preset', 'standard', path, path_ ] )
    if not ret:
        os.remove( path )

def loop():
    paths = glob.glob( 'media/audio/*.wav' )
    if len( sys.argv ) > 1 and sys.argv[1] == 'misc':
        paths += glob.glob( 'media/misc/*.wav' )
    [ wav2mp3( p ) for p in paths ]

    [ bmp2png( p ) for p in glob.glob( 'media/img/*.bmp' ) ]

def main():
    print 'Starting daemon'
    try:
        while True:
            loop()
            time.sleep( 60 )
    except KeyboardInterrupt:
        print 'Shutting down'

main()