class Edge():
    def __init__( self, s, t, w=0 ):
        self.s, self.t, self.w = s, t, w
    def __repr__( self ): return '%s -> %s = %d' % ( self.s, self.t, self.w )

class Graph():
    # Creation
    def __init__( self ):
        self.adj, self.flow = {}, {}
        self.S, self.T = '#', '&' #XXX: must not be in V
    def mkMatch( self, ps ):
        A = list(set( [ a for (a,b) in ps ] ))
        B = list(set( [ b for (a,b) in ps ] ))
        map( self.addVertex, [self.S,self.T] )
        map( self.addVertex, A )
        map( self.addVertex, B )
        for a in A:
            self.addEdge( self.S, a, 1 )
        for b in B:
            self.addEdge( b, self.T, 1 )
        for (a,b) in ps:
            self.addEdge( a, b, 1 )

    def addVertex( self, v ): self.adj[ v ] = []
    def addEdge( self, s, t, w=0 ):
        e = Edge( s, t, w )
        re = Edge( t, s, 0 )
        e.rev = re
        re.rev = e
        self.adj[ s ].append( e )
        self.adj[ t ].append( re )
        self.flow[ e ] = 0
        self.flow[ re ] = 0
    # Analysis
    def complexity( self ):
        return 'Complexity: |V|=%d, |E|=%d' % ( len(self.adj), len(self.flow)/2 )
    # Comp
    def getNeighborEdges( self, v ): return self.adj[ v ]
    def getMatchPairing( self ): return [ (e.s,e.t) for (e,f) in self.flow.iteritems() if f == 1 and e.s != self.S and e.t != self.T ]

    # Calculate shortest path
    def bfsSP( self, s, t ):
        self.bfsOuter, self.bfsInner = 0, 0
        queue = [ s ]       # :: [ Node ]
        paths = { s:[] }    # :: Map Node -> [ Edge ]
        while queue:
            self.bfsOuter += 1
            u = queue.pop(0)
            for e in self.getNeighborEdges( u ):
                self.bfsInner += 1
                if e.w - self.flow[ e ] > 0 and e.t not in paths:
                    paths[ e.t ] = paths[ u ] + [ e ]
                    if e.t == t: return paths[ e.t ]
                    queue.append( e.t )
        return None

    # Find max flow. molests self.flow
    def edmondsKarp( self, s, t ):
        while True:
            path = self.bfsSP( s, t )
            if not path: break
            maxCap = min( e.w - self.flow[ e ] for e in path )
            for e in path:
                self.flow[ e ] += maxCap
                self.flow[ e.rev ] -= maxCap
        return sum( self.flow[ e ] for e in self.getNeighborEdges( s ) )

    def doMatch( self, debugF=None ):
        self.edmondsKarp( self.S, self.T )
        return self.getMatchPairing()

def chunksOf( n, xs ):
    def f( xs ):
        a,b = xs[:n], xs[n:]
        if not a: return []
        else: return [a] + f( b )
    return f( xs )

def test():
    print '-- Trivial abcd x 123 problem --'
    A = 'abcd'
    B = '123'
    pairsStr = 'a2a3b1b2b3c1c2'
    pairs = [ (x[0], x[1]) for x in chunksOf( 2, pairsStr ) ]

    g = Graph()
    g.mkMatch( pairs )
    print g.complexity()
    ms = g.doMatch()
    print 'Flow:', len(ms)
    print 'Matching:', ms

def randTest():
    print '-- Random test'
    import string, random
    A = range(26*2)
    B = string.ascii_letters
    N = lambda n=len(B): random.randint(0,n)
    pairs = []
    for a in A:
        for i in range( N() ):
            b = random.choice( B )
            if (a,b) not in pairs: pairs.append( (a,b) )

    g = Graph()
    g.mkMatch( pairs )
    print '|A|=%d, |B|=%d, |E|=%d' % ( len(A), len(B), len(pairs) )
    print g.complexity()
    ms = g.doMatch()
    print 'Flow:', len(ms)
    print 'Matching:', ms

if __name__ == '__main__':
    test()
    randTest()
