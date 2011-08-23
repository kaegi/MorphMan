# -*- coding: utf-8 -*-
from morph.morphemes import *

def printf( s ):
    if sys.platform == 'win32':
        import win32console as W
        W.SetConsoleOutputCP( 65001 )
        W.SetConsoleCP( 65001 )
    try: print s
    except: pass

def test():
    ppath = 'morph'+ os.sep +'tests'+ os.sep
    a = MorphDb.mkFromFile( ppath +'test.txt' )
    a.save( ppath +'test.db.testTmp' )
    d = MorphDb( path=ppath+ os.sep +'test.db.testTmp' )
    print 'Found %d. Should be %d' % ( d.count, 71 )
    printf( d.analyze2str() )

def printKnown():
    k = MorphDb( path='morph'+ os.sep +'dbs'+ os.sep +'known.db' )
    printf( k.show() )

def printKnownLDb():
    k = MorphDb( path='morph'+ os.sep +'dbs'+ os.sep +'known.db' )
    printf( k.showLDb() )

def main(): # :: IO ()
    if '--test' in sys.argv:
        return test()
    elif '--known' in sys.argv:
        return printKnown()
    elif '--knownLDb' in sys.argv:
        return printKnownLDb()
    elif len( sys.argv ) != 3:
        print 'Usage: %s srcTxtFile destDbFile' % sys.argv[0]
        return
    d = MorphDb.mkFromFile( sys.argv[1] )
    d.save( sys.argv[2] )

if __name__ == '__main__': main()
