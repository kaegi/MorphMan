import codecs
from morphemes import getMorphemes2, MorphDb
from util import cfg1

# utils
def getNotInDb( ms, db ):
    s = set()
    for m in ms:
        if m not in db:
            s.add( m )
    mstr = u'  '.join( m.base for m in s )
    return mstr, len(s)

def getText( line ):
    line = line[10:]
    ps = line.split(',', 10)
    return ps[9].rstrip()

def getPreText( line ):
    line_ = line[10:]
    ps = line_.split(',', 10)
    return line[:10] + u','.join( ps[:9] ) + u','

def run( duelingSubsPath, outputSubsPath, morphemizer, whitelist, blacklist, matureFmt, knownFmt, unknownFmt ):
    # Load files
    kdb = MorphDb( cfg1('path_known') )
    mdb = MorphDb( cfg1('path_mature') )
    subFileLines = codecs.open( duelingSubsPath, 'r', 'utf-8' ).readlines()

    # Get dueling subs
    dialogueLines = [ l for l in subFileLines if l.startswith( u'Dialogue' ) ]
    header = subFileLines[ : subFileLines.index( dialogueLines[0] ) ]
    assert len( dialogueLines ) % 2 == 0, 'Should be an even number of dialogue lines'

    lines = []
    for i in xrange( 0, len( dialogueLines ), 2 ):
        target, native = dialogueLines[i:i+2]
        target, native, pre = getText( target ), getText( native ), getPreText( target )

        # get unknowns
        ms = getMorphemes2(morphemizer, target, whitelist, blacklist )
        unknowns, N_k = getNotInDb( ms, kdb.db )
        unmatures, N_m = getNotInDb( ms, mdb.db )
        d = { 'target':target, 'native':native, 'N_k':N_k, 'N_m':N_m, 'unknowns':unknowns, 'unmatures':unmatures }

        if N_m == 0:
            lines.append( pre + matureFmt % d )
        elif N_k == 0:
            lines.append( pre + knownFmt % d )
        else:
            lines.append( pre + unknownFmt % d )

    outFile = codecs.open( outputSubsPath, 'w', 'utf-8' )
    outFile.write( u''.join( header ) )
    outFile.write( u'\n'.join( lines ) )
    outFile.close()
