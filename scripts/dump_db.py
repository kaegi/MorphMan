# -*- coding: utf-8 -*-
import os
import sys

# find the directory where the classes files are
morphDir = os.path.join(os.path.dirname(sys.path[0]), "morph")
# this path should not have the directory terminator at the end

# add it to the path so we can find the morphemes class
sys.path.insert(1, morphDir)


from morphemes import Morpheme, MorphDb

def show_location(loc):
    return "\t%s\t%s\t%s\t%s\t%s"%(loc.noteId, loc.fieldName, loc.maturity, loc.guid, loc.weight)


class Dumpster():
    def __init__(self, path=None, parent=None):
        self.db = MorphDb(path)

    def dump(self, withLocations=False):  # Str
        print('\t'.join(['norm', 'base', 'inflected', 'reading', 'pos', 'subpos']))
        # to sort the items we need to turn them into a list
        lItems  = list(self.db.db.items())
        lItems.sort(key=lambda x: x[0].show())
        for item in lItems:
            # item[0] is the morph, item[1] is the list of locations
            print (item[0].show())
            if withLocations:
                locs = list(map(show_location, item[1]))
                locs.sort()
                for l in locs:
                    print(l)

if __name__ == "__main__":
    if len(sys.argv) > 1 and len(sys.argv) <= 3:
        fileName = sys.argv[1]
        withLocations  = False
        if (len(sys.argv) == 3):
            withLocations = sys.argv[2] == 'locations'

        try:
            mm = Dumpster(fileName)
            mm.dump(withLocations)
        except:
            print ("Unable to load file [%s]" % fileName)
            raise
    else:
        print ("Dump database as a tab delimited file\n\nUsage:\n\t%s <filename> [locations]\n\nif parameter locations specified, them dump locations too\n" % sys.argv[0])
