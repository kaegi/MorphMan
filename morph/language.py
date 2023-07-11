from aqt.utils import tooltip
import os
import io
import csv
import itertools
from .preferences import get_preference as cfg
from .morphemes import Morpheme

# Each language has its own MorphDb
_allDb = {}

class FrequencyList:
	def __init__(self):
		self.map = dict()
		self.len = 0
		self.has_morphemes = False
		self.has_frequency_count = False
		self.master_total_instances = 0

def getLanguageList():
	languages = set()
	rowData = cfg('Filter')
	for row in rowData:
		languages.add(row['Language'])
	if len(languages) == 0:
		languages.add('Default')
	return list(languages)


def getPathByLanguage(path, language):
	if (language == 'Default'):
		return path % ('')
	else:
		return path % ('_' + language )


def getAllDb(language):
	global _allDb

	# Force reload if all.db got deleted
	all_db_path = getPathByLanguage(cfg('path_all'),language)
	reload = not os.path.isfile(all_db_path)

	if reload or (language not in _allDb):
		from .morphemes import MorphDb
		_allDb[language] = MorphDb(all_db_path, ignoreErrors=True)
	return _allDb[language]


def getTotalKnownSet():
	from .morphemes import MorphDb

	# Load known.db and get total morphemes known
	totalVariations = 0
	totalKnown = 0
	languages = getLanguageList()
	for language in languages:
		known_db = MorphDb(getPathByLanguage(cfg('path_known'),language), ignoreErrors=True)
		totalVariations += len(known_db.db)
		totalKnown += len(known_db.groups)

	d = {'totalVariations': totalVariations, 'totalKnown': totalKnown}
	return d


"""
See docs/FrequencyListFormats.md for specific info about the file format  
"""
def loadFrequencyList(frequencyListPath, force_morphemes=False):

	print("Loading Frequency List for file %s.." % frequencyListPath)
	fl = FrequencyList()

	try:
		with io.open(frequencyListPath, encoding='utf-8-sig') as csvfile:
			csvreader = csv.reader(csvfile, delimiter="\t")
			rows = [row for row in csvreader]
			print("First line: [%s]" % rows[0][0])

			if rows[0][0] == "#study_plan_frequency":
				print("Detected Study plan frequency format")
				fl.has_morphemes = True
				fl.map = dict(
					zip([Morpheme(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows[1:]],
						itertools.count(0)))

			elif rows[0][0] == "#frequency_report":
				print("Detected Frequency report format")
				fl.has_morphemes = True
				fl.has_frequency_count = True
				for row in rows[1:]:
					fl.map[ Morpheme(row[1], row[2], row[2], row[3], row[4], row[5]) ] = int(row[0])

			elif rows[0][0] == "#HEADERTYPE_count_word":
				print("Detected frequency + word format")
				fl.has_frequency_count = True
				if force_morphemes:
					fl.has_morphemes = True
					for row in rows[1:]:
						fl.map[ Morpheme(row[1], row[1], row[1], row[1], "UNKNOWN","UNKNOWN") ] = int(row[0])
				else:
					for row in rows[1:]:
						fl.map[ row[1] ] = int(row[0])
			else:
				print("Assuming one-word-per-line format")
				if force_morphemes:
					fl.has_morphemes = True
					fl.map = dict(zip([Morpheme(row[1], row[1], row[1], row[1], "UNKNOWN","UNKNOWN") for row in rows], itertools.count(0)))
				else:
					fl.map = dict(zip([row[0] for row in rows], itertools.count(0)))

			fl.len = len(fl.map)
			if fl.has_frequency_count:
				fl.master_total_instances = sum(fl.map.values())

	except (FileNotFoundError, IndexError) as e:
		err = "Warning! Couldn't not read frequency list %s" % (frequencyListPath)
		print(err)
		tooltip(err)
		pass

	return fl

def loadFrequencyListByLanguage(language):
	frequencyListPath = getPathByLanguage(cfg('path_frequency'), language)
	return loadFrequencyList(frequencyListPath)

