import functools
import sys

def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size

###############################################################################
## Functional tools
###############################################################################
class memoize(object):
   '''Decorator that memoizes a function'''
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      # Don't memoize large args
      if get_size(args) > 512:
         return self.func(*args)
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
