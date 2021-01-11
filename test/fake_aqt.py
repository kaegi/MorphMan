import sys
from unittest.mock import MagicMock

aqt = MagicMock()
aqt.mw = MagicMock()
aqt.mw.pm.profileFolder = None
aqt.mw.col = None
aqt.mw.toolbar.draw = lambda: None

aqt.browser = MagicMock()

sys.modules['aqt'] = aqt
sys.modules['aqt.browser'] = aqt.browser
sys.modules['aqt.qt'] = MagicMock()
sys.modules['aqt.utils'] = MagicMock()


class FakeCollection:
    def __init__(self, config):
        self.config = config if config is not None else {}

    def get_config(self, key):
        return self.config.get(key, None)

    def set_config(self, key, value):
        self.config[key] = value


def init_collection(profile_folder='somewhere', config=None):
    aqt.mw.pm.profileFolder = MagicMock(return_value=profile_folder)
    aqt.mw.col = FakeCollection(config)
