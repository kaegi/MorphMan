from unittest.mock import MagicMock
import sys
aqt = MagicMock()
aqt.mw.pm.profileFolder = MagicMock(return_value='somewhere')
aqt.mw.col.conf = {}
sys.modules['aqt'] = aqt

from morph.preferences import initPreferences, get_preference
import unittest


class TestPreferences(unittest.TestCase):
    def setUp(self):
        initPreferences()

    def test_get_preference_in_config_py(self):
        self.assertEqual(get_preference('threshold_mature'), 21)

    def test_get_preference_in_json_config(self):
        self.assertEqual(get_preference('Field_FocusMorph'), 'MorphMan_FocusMorph')

    def test_get_preference_unexisting(self):
        self.assertEqual(get_preference('test non existing preference'), None)

    def test_dbsPath(self):
        self.assertEqual(get_preference('path_dbs'), 'somewhere/dbs')
        from morph.preferences import dbsPath
        self.assertEqual(dbsPath, 'somewhere/dbs')


if __name__ == '__main__':
    unittest.main()
