from PyQt4.QtCore import *
from PyQt4.QtGui import *
import util
import rankVocab as R
import morphemes as M

def pre( ed ):
    if not util.requireKnownDb(): return 'BAIL'
    kdb = M.loadDb( util.knownDbPath )
    rdb = R.mkRankDb( kdb )
    return { 'rdb':rdb, 'mp':M.mecab(None) }

def per( st, f ):
    f['vocabRank'] = u'%d' % R.rankFact( st, f )
    return st

def post( st ):
    st['mp'].kill()

util.addDoOnSelectionBtn( 'Set vocabRank', 'vocabRank set', 'Ranking...', pre, per, post )
