import glob
import sys
import unittest

from unittest.mock import MagicMock

# Mock Anki functions used by Preferences
col_conf = {'addons': {'morphman': {'already_in_profile': 'yep'}}}

aqt = MagicMock()
aqt.browser = MagicMock()
aqt.mw.pm.profileFolder = MagicMock(return_value='somewhere')
aqt.mw.col.conf = col_conf
aqt.mw.col.get_config = lambda key: col_conf[key]
aqt.mw.toolbar.draw = lambda: None
sys.modules['aqt'] = aqt

def create_test_suite():
    test_file_strings = glob.glob('test/test_*.py')
    module_strings = ['test.'+str[5:len(str)-3] for str in test_file_strings]
    suites = [unittest.defaultTestLoader.loadTestsFromName(name)
              for name in module_strings]
    testSuite = unittest.TestSuite(suites)
    return testSuite
