import json, cgi
from wsgiref.simple_server import make_server
from morph.morphemes import getMorphemes, MorphDb

allDbPath = r'C:\Users\overt_000\Documents\Anki\User 1\dbs\all.db'
allDb = MorphDb( allDbPath )

def decorate( text ):
    global allDb

    #ms = getMorphemes( text )
    ms = []
    for m in ms:
        locs = allDb.db.get( m, set() )
        mat = max( loc.maturity for loc in locs ) if locs else 0
        if   mat >= 21: mtype = 'mature'
        elif mat >=  3: mtype = 'known'
        elif mat >= .1: mtype = 'seen'
        else:           mtype = 'unknown'

    return [ ('foo','known'), ('bar','mature'), ('ball','seen') ]
 
def app( env, start_response ):
    post = cgi.FieldStorage(
        fp=env['wsgi.input'],
        environ=env,
        keep_blank_values=True
    )

    text = post[ 'text' ].value
    elems = decorate( text )
    result = { 'text': text, 'elems': elems }

    response_body = json.dumps( result )
    status = '200 OK'
    response_headers =  [   ( 'Content-Type', 'application/json' ),
                            ( 'Content-Length', str(len(response_body)) )
                        ]
    start_response( status, response_headers )
    return response_body
 
httpd = make_server( '', 8080, app )
print 'Serving...'
httpd.serve_forever()

