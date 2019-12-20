# -*- coding: utf-8 -*-
import importlib

from .util import initJcfg, jcfg, jcfg2
from aqt import mw


def initPreferences():
    initCfg()
    initJcfg()


cfgMod = None
dbsPath = None


def initCfg():
    global cfgMod, dbsPath
    from . import config
    importlib.reload(config)
    cfgMod = config
    dbsPath = config.default['path_dbs']

    # Redraw toolbar to update stats
    mw.toolbar.draw()


def cfg1(key, modelId=None, deckId=None):
    assert cfgMod, 'Tried to use cfgMods before profile loaded'
    profile = mw.pm.name
    model = mw.col.models.get(modelId)['name'] if modelId else None
    deck = mw.col.decks.get(deckId)['name'] if deckId else None
    if key in cfgMod.deck_overrides.get(deck, []):
        return cfgMod.deck_overrides[deck][key]
    elif key in cfgMod.model_overrides.get(model, []):
        return cfgMod.model_overrides[model][key]
    elif key in cfgMod.profile_overrides.get(profile, []):
        return cfgMod.profile_overrides[profile][key]
    else:
        return cfgMod.default[key]

