# -*- coding: utf-8 -*-
import morphemes as M

def mkRankDb( morphDb ): return dict( ((m.base, m.read), 0) for m in morphDb.db.keys() )

def rankMorphemes( rDb, ms ): return sum( rankMorpheme( rDb, m.base, m.read ) for m in ms )

def rankMorpheme( rDb, expr, read ):
    wordEase = 0
    numCharsConsidered = 0
    hasKanji = False
    if (expr, read) in rDb: return 0
    for i,c in enumerate( expr ):
        # skip non-kanji
        if c < u'\u4E00' or c > u'\u9FBF': continue

        hasKanji = True
        charEase = 20
        npow = 0
        numCharsConsidered += 1
        for (e,r) in rDb:
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
