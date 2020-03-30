# -*- coding: utf-8 -*-
import os
import sys

print (sys.path[0])

# find the directory where the classes files are
morphDir = os.path.join(os.path.dirname(sys.path[0]), "morph")
# this path should not have the directory terminator at the end

# add it to the path so we can find the morphemes class
sys.path.insert(1, morphDir)


from morphemes import Morpheme, MorphDb

class Dumpster():
    def __init__(self, parent=None):
        self.db = None

    def load(self, path):
        self.db = MorphDb(path=self.aPath)

    def dump(self):  # Str
        print('\t'.join(['norm', 'base', 'inflected', 'reading', 'pos', 'subpos']))
        for m, ls in self.db.db.items():
            print (m.show())


if __name__ == "__main__":
    if len(sys.argv) == 2:
        fileName = sys.argv[1]
        try:
            mm = Dumpster()
            mm.load(fileName)
            mm.dump()
        except:
            print ("Unable to load file [%s]" % fileName)
            raise
    else:
        print ("Dump database as a tab delimited file\n\nUsage:\n\t%s <filename>" % sys.argv[0])
