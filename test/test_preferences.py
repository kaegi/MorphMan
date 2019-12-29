import unittest
import sys
from unittest.mock import MagicMock

# Mock Anki functions used by Preferences
aqt = MagicMock()
aqt.mw.pm.profileFolder = MagicMock(return_value='somewhere')
aqt.mw.col.conf = {}
sys.modules['aqt'] = aqt


from morph.preferences import init_preferences, get_preference


class TestPreferences(unittest.TestCase):
    def setUp(self):
        init_preferences()

    def test_get_preference_in_config_py(self):
        self.assertEqual(get_preference('threshold_mature'), 21)

    def test_get_preference_in_json_config(self):
        self.assertEqual(get_preference('Field_FocusMorph'), 'MorphMan_FocusMorph')

    def test_get_preference_unexisting(self):
        self.assertEqual(get_preference('test non existing preference'), None)

    def test_dbsPath(self):
        self.assertEqual(get_preference('path_dbs'), 'somewhere/dbs')


if __name__ == '__main__':
    unittest.main()
