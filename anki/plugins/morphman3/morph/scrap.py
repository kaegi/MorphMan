@memoize
def fldIdxMap( mid ): # ModelId -> Map FieldName Idx
    m = mw.col.models.get( mid )
    return dict( ( f['name'], f['ord'] ) for f in m[ 'flds' ] )

def flds2dict( flds, mid ):
    fs = splitFields( flds )
    d = fldIdxMap( mid )
    return dict( ( name, fs[ idx ] ) for name, idx in d.iteritems() )

def dict2flds( d, mid ):
    idxMap = fldIdxMap( mid )
    fnames = sorted( idxMap.iteritems(), key=lambda (k,v): v )
    fs = [ d[ name ] for name,idx in fnames ]
    return joinFields( fs )

def getField( fieldName, flds, mid ):
    idx = getFieldIndex( fieldName, mid )
    return splitFields( flds )[ idx ]

def normalizeFieldValue( s ):
    return stripHTML( s )


#n = mw.col.getNote( nid )
#n['iPlusN'] = u'%d' % N_k
#n.flush()
