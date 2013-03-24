#!/usr/bin/env python
#-*- coding: utf-8 -*-
import codecs
import cPickle as pickle
import glob
import os
import re

def norm( txt ):
    for c in [ '\\c', '\\d', '\\l', '\\e', '\\f', '\\n', '\\p' ]:
        txt = txt.replace( c, '' )
    return txt

ps = glob.glob( 'mla_scripts/MLA_*' )
jap2eng = {}
dupes = []
for p in ps:
    name = os.path.basename( p ).split('MLA_')[1].split('.txt')[0]
    print 'Processing', name
    lines = codecs.open( p, 'rb', encoding='shift-jis', errors='ignore' ).read().split(u'\r\n')
    d = dict( (i,line) for i,line in enumerate(lines) )

    japLine, engLine = None, None
    for lineno,line in d.items():
        r = re.match( '//<(.*?)> (.*)', line )
        if r:
            japLine = norm( r.group(2) )

        r = re.match( '<(.*?)> (.*)', line )
        if r:
            engLine = norm( r.group(2) )

        if japLine and engLine:
            if japLine in jap2eng:
                dupes.append( ( japLine, engLine ) )
            jap2eng[ japLine ] = engLine
            japLine, engLine = None, None

pickle.dump( jap2eng, open( 'muvluv_mla.db', 'wb' ), -1 )
