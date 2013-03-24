#!/usr/bin/env python
#-*- coding: utf-8 -*-
import codecs
import glob
import os
import re

ps = glob.glob( 'mla_scripts/MLA_*' )
engDb, japDb, jap2eng = {}, {}, {}
for p in ps:
    name = os.path.basename( p ).split('MLA_')[1].split('.txt')[0]
    print 'Processing', name
    lines = codecs.open( p, 'rb', encoding='shift-jis', errors='ignore' ).read().split(u'\r\n')
    d = dict( (i,line) for i,line in enumerate(lines) )
    for lineno,line in d.items():
        r = re.match( '//<(.*?)> (.*)', line )
        if r: japDb[ name + r.group(1) ] = r.group(2)

        r = re.match( '<(.*?)> (.*)', line )
        if r: engDb[ name + r.group(1) ] = r.group(2)

print 'engDb:', len( engDb )
print 'japDb:', len( japDb )
for k in japDb:
    try: jap2eng[ japDb[k] ] = engDb[k]
    except KeyError:
        print 'Failed to match'
        print k
        print japDb.get( k )
        print engDb.get( k )
        raise
print 'jap2eng:', len( jap2eng )
