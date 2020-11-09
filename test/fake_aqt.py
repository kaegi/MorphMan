from unittest.mock import MagicMock

class FakeCollection:
    def __init__(self, config):
        self.config = config if config is not None else {}

    def get_config(self, key):
        return self.config.get(key, None)

    def set_config(self, key, value):
        self.config[key] = value

browser = MagicMock()
mw = MagicMock()
mw.pm.profileFolder = None
mw.col = None
mw.toolbar.draw = lambda: None


def init_collection(profile_folder='somewhere', config=None):
    mw.pm.profileFolder = MagicMock(return_value=profile_folder)
    mw.col = FakeCollection(config)
