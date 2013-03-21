#!/usr/bin/python2
import anki, re

deckPath = '/home/roark/.anki/decks/RtK.anki' # loads anki deck from here
revtkCSVPath = 'my_stories.csv' # gets revtk stories from here
storyField = 'Story' # replaces this field
heisigNumberField = 'Heisig number' # matches facts by this field

def updateAnkiDeck( revtks ): # :: Map HeisigNumber RevTKFact -> IO ()
    d = anki.deck.DeckStorage.Deck( deckPath )
    cs = d.s.query( anki.cards.Card )

    factIds, cardIds = [], []
    for c in cs:
       try:
          hid = int( c.fact[ heisigNumberField ] )
          if hid in revtks:
             if c.fact[ storyField ] != revtks[ hid ][ 'story' ]:
                c.fact[ storyField ] = revtks[ hid ][ 'story' ]
                factIds.append( c.fact.id )
                cardIds.append( c.id )
       except ValueError: pass # no heisig num on this card
    print 'Modified %d cards, %d facts' % ( len( cardIds ), len( factIds ) )
    d.updateCardsFromFactIds( factIds )
    d.updateCardQACacheFromIds( factIds, type='fact' )
    d.updateCardQACacheFromIds( cardIds, type='card' )
    d.unsuspendCards( cardIds )
    d.save()
    d.close()

def parseRevTKStories(): # :: IO Map HeisigNumber RevTKFact
    def f(s):
        s = s[1:] if s[0] == '"' else s
        s = s[:-1] if s[-1] == '"' else s
        return s.decode('utf-8')
    rs = open( revtkCSVPath ).read().split('\r\n')[:-1]
    d = {}
    for r in rs:
        p = r.split(',') # heisig id, kanji, keyword, public?, time, story
        try: d[ int(p[0]) ] = { 'id':int(p[0]), 'kanji':f(p[1]), 'keyword':f(p[2]), 'public':f(p[3]), 'time':p[4], 'story':f(','.join(p[5:])) }
        except Exception, e:
           print r
           raise e
    return d

def formatRevTK2anki( fact ): # :: RevTKFact -> RevTKFact
    s = fact['story']
    # surrounded by asteriks => italics, hashes => bold, keyword => bold
    s = re.sub( '\*(.*?)\*', r'<span style="font-style:italic;">\1</span>', s )
    s = re.sub( '\#(.*?)\#', r'<span style="font-weight:600;">\1</span>', s )
    s = re.sub( '(%s)' % fact['keyword'], r'<span style="font-weight:600;">\1</span>', s, re.IGNORECASE )
    # strip extraneous quotes
    s = s[1:] if s[0] == '"' else s
    s = s[:-1] if s[-1] == '"' else s

    fact['story'] = s
    return fact

print 'Reformatting stories'
t = parseRevTKStories()
for k,v in t.items(): t[k] = formatRevTK2anki( v )

print 'Updating anki deck'
updateAnkiDeck( t )
