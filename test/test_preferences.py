import os
import unittest

from test import fake_aqt

from morph.preferences import init_preferences, get_preference, update_preferences

class TestPreferences(unittest.TestCase):
    def setUp(self):
        pass

    def init_default_collection(self):
        fake_aqt.init_collection()
        init_preferences()

    def init_existing_collection(self):
        fake_aqt.init_collection(config={'addons': {'morphman': {'already_in_profile': 'yep'}}} )
        init_preferences()

    def assertPreference(self, name, value):
        return self.assertEqual(get_preference(name), value)

    def test_dbsPath(self):
        self.init_default_collection()
        self.assertPreference('path_dbs', os.path.normpath('somewhere/dbs'))
    
    def test_get_preference_in_config_py(self):
        self.init_default_collection()
        self.assertPreference('threshold_mature', 21)

    def test_get_preference_in_default_json_config(self):
        self.init_default_collection()
        self.assertPreference('Field_FocusMorph', 'MorphMan_FocusMorph')

    def test_get_preference_in_stored_json_config(self):
        self.init_existing_collection()
        self.assertPreference('already_in_profile', 'yep')

    def test_get_preference_unexisting(self):
        self.init_existing_collection()
        self.assertPreference('test non existing preference', None)

    def test_update_preferences(self):
        self.init_existing_collection()
        self.assertPreference('newly_inserted', None)  # This preference does not exist yet, good
        update_preferences({'newly_inserted': 1111})
        self.assertPreference('newly_inserted', 1111)

        self.assertPreference('Field_FocusMorph', 'MorphMan_FocusMorph')  # Didn't broke default
        self.assertPreference('already_in_profile', 'yep')  # Didn't broke existing


if __name__ == '__main__':
    unittest.main()
