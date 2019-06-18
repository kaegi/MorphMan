import codecs
from .morphemes import getMorphemes, MorphDb
from .util import cfg1

# utils
def getNotInDb( ms, db ):
    s = set()
    for m in ms:
        if m not in db:
            s.add( m )
    mstr = '  '.join( m.base for m in s )
    return mstr, len(s)

def getText( line ):
    line = line[10:]
    ps = line.split(',', 10)
    return ps[9].rstrip()

def getPreText( line ):
    line_ = line[10:]
    ps = line_.split(',', 10)
    return line[:10] + ','.join( ps[:9] ) + ','

def run( inputSubsPath, outputSubsPath, morphemizer, matureFmt, knownFmt, unknownFmt ):
    # Load files
    kdb = MorphDb( cfg1('path_known') )
    mdb = MorphDb( cfg1('path_mature') )
    with codecs.open( inputSubsPath, 'r', 'utf-8' ) as subFile:
	    subFileLines = subFile.readlines()
	    # Get dueling subs
	    dialogueLines = [ l for l in subFileLines if l.startswith( 'Dialogue' ) ]
	    header = subFileLines[ : subFileLines.index( dialogueLines[0] ) ]
	    assert len( dialogueLines ) % 2 == 0, 'Should be an even number of dialogue lines. Are you using duel subtitles?'

    lines = []
    for i in range( 0, len( dialogueLines ), 2 ):
        target, native = dialogueLines[i:i+2]
        target, native, pre = getText( target ), getText( native ), getPreText( target )

        # get unknowns
        ms = getMorphemes(morphemizer, target)
        unknowns, N_k = getNotInDb( ms, kdb.db )
        unmatures, N_m = getNotInDb( ms, mdb.db )
        d = { 'target':target, 'native':native, 'N_k':N_k, 'N_m':N_m, 'unknowns':unknowns, 'unmatures':unmatures }

        if N_m == 0:
            lines.append( pre + matureFmt % d )
        elif N_k == 0:
            lines.append( pre + knownFmt % d )
        else:
            lines.append( pre + unknownFmt % d )

    with codecs.open( outputSubsPath, 'w', 'utf-8' ) as outFile:
	    outFile.write( ''.join( header ) )
	    outFile.write( '\n'.join( lines ) )
