# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from aqt import mw
from aqt.utils import showWarning as info
from anki.hooks import addHook, wrap
import datetime, os, codecs

cfg = None
def loadCfg():
    global cfg
    cfg = {
        'path_ext': os.path.join( mw.pm.profileFolder(), 'dbs', 'external.db' ),
        'path_all': os.path.join( mw.pm.profileFolder(), 'dbs', 'all.db' ),
        'path_known': os.path.join( mw.pm.profileFolder(), 'dbs', 'known.db' ),
        'path_mature': os.path.join( mw.pm.profileFolder(), 'dbs', 'mature.db' ),
        'path_log': os.path.join( mw.pm.profileFolder(), 'morphman.log' ),
        'threshold_mature': 21,
        'threshold_known': 3,
        'threshold_seen': 1,
        'morph_fields': ['Expression'],
        'morph_whitelist': u''.split(','),
        'morph_blacklist': [ u'記号', u'UNKNOWN'],
    }
    #cfg.update( mw.pm.profile.get( 'morphMan', {} ) )
    mw.pm.profile[ 'morphMan' ] = cfg
addHook( 'profileLoaded', loadCfg )

def printf( msg ):
    txt = '%s: %s' % ( datetime.datetime.now(), msg )
    f = codecs.open( cfg['path_log'], 'a', 'utf-8' )
    f.write( txt+'\r\n' )
    f.close()
    print txt

def clearLog():
    f = codecs.open( cfg['path_log'], 'w', 'utf-8' )
    f.close()

class memoize(object):
   '''Decorator that memoizes a function'''
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      try:
         return self.cache[args]
      except KeyError:
         value = self.func(*args)
         self.cache[args] = value
         return value
      except TypeError: # uncachable -- for instance, passing a list as an argument. Better to not cache than to blow up entirely.
         return self.func(*args)
   def __repr__(self):
      """Return the function's docstring"""
      return self.func.__doc__
   def __get__(self, obj, objtype):
      """Support instance methods"""
      return functools.partial(self.__call__, obj)
