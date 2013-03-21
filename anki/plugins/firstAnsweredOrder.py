from ankiqt import mw
import anki.deck
# make random review order instead order cards by when they were first answered

def revOrder( self ):
    return (    'priority desc, interval desc',
                'priority desc, interval',
                'priority desc, combinedDue',
                'priority desc, firstAnswered',
            )[ self.revCardOrder ]

anki.deck.Deck.revOrder = revOrder
mw.registerPlugin( 'First answered rev order', 2012062517 )
