import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock Anki functions used by Preferences
aqt = MagicMock()
aqt.mw.pm.profileFolder = MagicMock(return_value='somewhere')
aqt.mw.col.conf = {'addons': {'morphman': {'already_in_profile': 'yep'}}}
sys.modules['aqt'] = aqt


from morph.preferences import init_preferences, get_preference, update_preferences


class TestPreferences(unittest.TestCase):
    def setUp(self):
        init_preferences()

    def assertPreference(self, name, value):
        return self.assertEqual(get_preference(name), value)

    def test_get_preference_in_config_py(self):
        self.assertPreference('threshold_mature', 21)

    def test_get_preference_in_default_json_config(self):
        self.assertPreference('Field_FocusMorph', 'MorphMan_FocusMorph')

    def test_get_preference_in_stored_json_config(self):
        self.assertPreference('already_in_profile', 'yep')

    def test_get_preference_unexisting(self):
        self.assertPreference('test non existing preference', None)

    def test_dbsPath(self):
        self.assertPreference('path_dbs', os.path.normpath('somewhere/dbs'))

    def test_update_preferences(self):
        self.assertPreference('newly_inserted', None)  # This preference does not exist yet, good
        update_preferences({'newly_inserted': 1111})
        self.assertPreference('newly_inserted', 1111)

        self.assertPreference('Field_FocusMorph', 'MorphMan_FocusMorph')  # Didn't broke default
        self.assertPreference('already_in_profile', 'yep')  # Didn't broke existing


if __name__ == '__main__':
    unittest.main()
