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
context_fields = ( 'Sound', 'Image', 'Speaker', 'Expression', 'Meaning', )
contexts = [-2,-1,+1,+2]
baseMediaDir = 'muvluv.10-22to11-30'
transDbPath = 'muvluv_mla.db'
transDb = pickle.load( open( transDbPath, 'rb' ) )

N = 0
def getMeaning( txt ):
    try:
        return transDb[ txt ], txt
    except KeyError:
        # Check for various malformed lines and correct them if possible

        # progress = lines with progressively more info. presumably because
        # the line was long or had delays of some sort and so ITH was confused

        '''
        # 1) progress dialogue
        # ex: [Speaker] txt [Speaker] more txt [Speaker] even more txt
        # ex: 【夕呼】「…………こんなもの構えることになるなんて【夕呼】「…………こんなもの構えることになるなんて……思わなかったわ」
        ps = re.split( u'(\u3010.*?\u3011)', txt )
        if len( ps ) > 4:
            last = ps[-2]+ps[-1]
            if last in transDb:
                print 1
                return transDb[ last ], last
        '''
        # try largest valid dialogue (in case of garbage or progressive dialogue)
        # ex: 【夕呼】「…………こんなもの構えることになるなんて【夕呼】「…………こんなもの構えることになるなんて……思わなかったわ」
            # first, do findall on regex for full dialogue lines
        ds = []
        for d in re.findall( u'(\u3010.*?\u3011.*?」)', txt ):
            # second, split ea in case of invalid lines merged together (as per start of example)
            ps = re.split( u'(\u3010.*?\u3011)', txt )[1:]
            first, last = ps[0]+ps[1], ps[-2]+ps[-1]
            if first != last:
                ds.append( first )
                ds.append( last )
            else: ds.append( d )
        if ds:
            best = max( ds, key=lambda x: len(x) )
            if best in transDb:
                print 1
                return transDb[ best ], best
            else:
                # there might be junk after closing quote
                # ex: [Speaker] 「txt1 txt2 txt3」txt2
                r = re.match( u'(\u3010.*?\u3011.*?」).*', best )
                if r:
                    newtxt = r.group(1)
                    if newtxt in transDb:
                        print 2
                        return transDb[ newtxt ], newtxt

        # 3) check for repeat line (exact 2x repeat)
        # ex: [Speaker] txt [Speaker] txt
        # ex: モニターを凝視して考え込んでいた先生が銃を下ろした。モニターを凝視して考え込んでいた先生が銃を下ろした。
        if len( txt ) % 2 == 0:
            mid = len( txt ) / 2
            a, b = txt[:mid], txt[mid:]
            if a == b and a in transDb:
                print 3, txt
                return transDb[ a ], a

        print '!!!', txt
        global N
        N += 1
        return '',txt

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
    # ITH leaves in garbage from previous lines, so strip everything after null term
    if u'\0' in txt: txt = txt.split( u'\0' )[0]

    speaker = ''
    meaning, txt = getMeaning( txt ) # also fixes text if it was a repeat line

    # parse out speaker if name in brackets preceedes text. ex: 【武】。。。
    r = re.match( u'\u3010(.*?)\u3011(.*)', txt )
    if r:
        speaker = r.group(1)
        txt = r.group(2)

    return { 'Id':u'%s-%s-%d' % ( show, prefix, int(idx) ), 'Show':show, 'Prefix':prefix, 'Index':idx, 'Time':time, 'Expression':txt, 'Image':getImgPath( idx, prefix ), 'Sound':getSoundPath( idx, prefix ), 'Speaker':speaker, 'Meaning':meaning }

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
    print 'Unable to match', N, len(d)
    assert False
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
