# -*- coding: utf-8 -*-
import morphemes as M
import codecs

def mkRankDb( morphDb ): return dict([ ((e,r), 0) for (e,pos,subPos,r) in morphDb.keys() ])


def rankFact( st, f ):  
    ms = M.getMorphemes( st['mp'], f['Expression'] )
    ret = 0
    for x in ms:
        r = rankMorpheme( st['rdb'], x )
        ret += r

    return ret

def rankMorpheme( db, (expr,pos,subPos,read) ): return rankWord( db, (expr,read) )

def rankWord( db, (expr,read) ):
    
    wordEase = 0
    numCharsConsidered = 0

    hasKanji = False

    if (expr,read) in db.keys(): return 0
    
    for i,c in enumerate(expr):
        # skip non-kanji
        if c < u'\u4E00' or c > u'\u9FBF': continue

        hasKanji = True
        charEase = 20
        npow = 0
        numCharsConsidered += 1
        for (e,r) in db.keys():
            # has same kanji
            if c in e:
                if npow > -0.5: npow -= 0.1                
                # has same kanji at same pos
                if len(e) > i and c == e[i]:
                    if npow > -1.0: npow -= 0.1
                    # has same kanji at same pos with similar reading
                    if i == 0 and read[0] == r[0] or i == len(expr)-1 and read[-1] == r[-1]:
                        npow -= 0.8
        wordEase += charEase * pow(2, npow)
    if not hasKanji:
        return 10
    return wordEase
    
def test():
    expr1,read1 = someTimeAgo = (u'先程',u'サキホド')
    expr2,read2 = lastWeek = (u'先週',u'センシュー')
    expr3,read3 = miss = (u'姉さん',u'ネーサン')
    expr4,read4 = approach = (u'近寄る',u'チカヨル')
    expr5,read5 = timid = (u'弱気',u'ヨワキ')

    k = M.loadDb( 'dbs/known.db' )
    ker = mkRankDb( k )

    print 'some time ago\n', rankWord( ker, someTimeAgo )
    print 'last week\n', rankWord( ker, lastWeek )
    print 'miss/oldSis\n', rankWord( ker, miss )
    print 'approach\n', rankWord( ker, approach )
    print 'timid\n', rankWord( ker, timid )

if __name__ == '__main__': test()
