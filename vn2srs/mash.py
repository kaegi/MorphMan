#!/usr/bin/env python
#-*- coding: utf-8 -*-

# 1) flag lines that are missing img or sound
# 2) add english lines

import codecs
import cPickle as pickle
import glob
import os
import re

base_fields = ( 'Id', 'Show', 'Prefix', 'Index', 'Time', )
context_fields = ( 'Sound', 'Image', 'Speaker', 'Expression', )
contexts = [-2,-1,+1,+2]
baseMediaDir = 'muvluv.10-22to11-30'

def getResourcePath( rtype, rext, idx, prefix ):
    return u'{mediaDir}/{rtype}/{prefix}.{idx}.{rext}'.format( mediaDir=baseMediaDir, rtype=rtype, prefix=prefix, idx=idx, rext=rext )
def getImgPath( idx, prefix ): return getResourcePath( 'img', 'png', idx, prefix )
def getSoundPath( idx, prefix ): return getResourcePath( 'audio', 'mp3', idx, prefix )

def parseFromDat( show, prefix ):
    p = u'{mediaDir}/misc/timing.{prefix}.dat'.format( mediaDir=baseMediaDir, prefix=prefix )
    db = pickle.load( open( p, 'rb' ) )
    d = {}
    for idx,( time, txt ) in db.iteritems():
        d[ idx ] = parseLine( show, prefix, idx, time, txt )
    return d

def parseFromTxt( show, prefix ): # this is a bit unreliable due to bleed from multi-lines/invalid chars
    lines = codecs.open( u'{mediaDir}/misc/timing.{prefix}.txt'.format( mediaDir=baseMediaDir, prefix=prefix ), 'rb', 'utf-16').read().split('\r\n')
    d = {}
    for line in lines:
        if not line: continue
        try: idx, time, txt = line.split( u' ', 2 )
        except ValueError: # assume is bleed from previous line due to invalid characters
            d[ int(idx)-1 ][ 'Expression' ] += line.strip( u'\r\n\0' )
        d[ int(idx) ] = parseLine( show, prefix, idx, time, txt )
    return d

parse = parseFromDat

def parseLine( show, prefix, idx, time, txt ):
    if u'\0' in txt:
        txt = txt.split( u'\0' )[0]  # strip everything after null as ITH stores garbage from previous lines
    speaker = ''

    # parse out speaker if name in brackets preceedes text. ex: 【武】。。。
    r = re.match( u'\u3010(.*?)\u3011(.*)', txt )
    if r:
        speaker = r.group(1)
        txt = r.group(2)

    return { 'Id':u'%s-%s-%d' % ( show, prefix, int(idx) ), 'Show':show, 'Prefix':prefix, 'Index':idx, 'Time':time, 'Expression':txt, 'Image':getImgPath( idx, prefix ), 'Sound':getSoundPath( idx, prefix ), 'Speaker':speaker }

def mkContextFieldName( f, i ):
    return u'%s %s' % ( f, '+%d' % i if i >= 0 else '%d' % i )

def addContext( d ):
    D = {}
    for idx,v in d.iteritems():
        D[ idx ] = v
        for i in contexts:
            for f in context_fields:
                fname = mkContextFieldName( f, i )
                fval = d[ idx+i ][ f ] if (idx+i) in d else ''
                D[ idx ][ fname ] = fval
    return D

def toTSV( d ):
    fs = base_fields + context_fields + tuple( mkContextFieldName( f, i ) for i in contexts for f in context_fields )
    row_templ = u'\t'.join( u'{%s}' % f for f in fs )
    tsv = u'\n'.join( row_templ.format( **d[ idx ] ) for idx in d )
    return tsv

def processPart( show, prefix ):
    print u'Processing %s - %s' % ( show, prefix )
    d = parse( show, prefix )
    d = addContext( d )
    tsv = toTSV( d )

    p = u'decks/%s - %s.tsv' % ( show, prefix )
    if not os.path.exists( 'decks' ): os.mkdir( 'decks' )
    codecs.open( p, 'wb', encoding='utf-8' ).write( tsv )

    return d, tsv

def getAllPrefixes(): return [ os.path.basename( p )[7:-4] for p in glob.glob( u'%s/misc/timing.*.txt' % baseMediaDir ) ]

def processShow( show ):
    tsvs = [ processPart( show, pre )[1] for pre in getAllPrefixes() ]
    showTSV = u'\n'.join( tsvs )
    codecs.open( u'decks/%s - total.tsv' % show, 'wb', encoding='utf-8' ).write( showTSV )
    print 'Saved total show tsv'

def test():
    x = processPart( 'Muv-Luv Alternative', 'day10-25_part1' )
    print x[1].split('\n')[100]

processShow( 'Muv-Luv Alternative' )
