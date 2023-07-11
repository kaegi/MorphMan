import re

from anki.utils import strip_html
from .morphemes import getMorphemes
from .morphemizer import getMorphemizerByName
from .preferences import get_preference as cfg
from .util import getFilterByMidAndTags
from .language import getAllDb

def nonSpanSub(sub, repl, string):
    return ''.join(re.sub(sub, repl, s, flags=re.IGNORECASE) if not s.startswith('<span') else s for s in
                    re.split('(<span.*?</span>)', string))

def bold_unknowns(mid, text, tags=None):
    if tags is None:
        tags = []
    
    # Strip any existing bold style
    text = nonSpanSub('(<b>|</b>)', '', text)

    mid_cfg = getFilterByMidAndTags(mid, tags)
    if mid_cfg is None:
        return text

    language = notecfg['Language']
    allDb = getAllDb(language)

    mName = mid_cfg['Morphemizer']
    morphemizer = getMorphemizerByName(mName)
    ms = getMorphemes(morphemizer, strip_html(text))

    # Merge helper verbs with their verb's inflections
    morphs = []
    for m in ms:
        if (m.pos == '助動詞' or (m.pos == '助詞' and m.subPos == '接続助詞')) and len(morphs) > 0 and morphs[-1][0].pos == '動詞':
            morphs[-1][1] += m.inflected
            continue
        morphs.append([m, m.inflected])

    proper_nouns_known = cfg('Option_ProperNounsAlreadyKnown')

    for m, inflected in sorted(morphs, key=lambda x: len(x[1]), reverse=True):  # largest subs first
        locs = allDb.getMatchingLocs(m)
        mat = max(loc.maturity for loc in locs) if locs else 0

        if (proper_nouns_known and m.isProperNoun()) or (mat >= cfg('threshold_known')):
            continue

        text = nonSpanSub('(%s)' % inflected, '<b>\\1</b>', text)

    return text
