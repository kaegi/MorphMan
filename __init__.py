from aqt.reviewer import Reviewer
from aqt.utils import tooltip
from aqt import gui_hooks

# TODO: importlib is seemingly used to patch over and disguise veeeeery bad bugs... remove its usages and fix the bugs
import importlib

import anki.stats
from anki import hooks
from anki.lang import _  # TODO: deprecated?

from .morph.util import *  # TODO: replace this star
from .morph import morph_stats
from .morph import reviewing_utils
from .morph import main as main_module  # TODO: change the file name 'main' to something more fitting like 'recalc'
from .morph import manager
from .morph import readability
from .morph import preferencesDialog
from .morph import graphs
from .morph import preferences

morphman_sub_menu = None
morphman_sub_menu_creation_action = None


def main():
    # Support anki version 2.1.50 and above
    # Hooks should be in the order they are executed!

    gui_hooks.profile_did_open.append(preferences.init_preferences)

    # Adds morphman to menu multiples times when profiles are changed
    gui_hooks.profile_did_open.append(init_actions_and_submenu)

    # TODO: Extract all hooks from the imports below and remove the pylint disable
    # pylint: disable=W0611
    from .morph.browser import viewMorphemes
    from .morph.browser import extractMorphemes
    from .morph.browser import batchPlay
    from .morph.browser import massTagger
    from .morph.browser import learnNow
    from .morph.browser import boldUnknowns
    from .morph.browser import browseMorph
    from .morph.browser import alreadyKnownTagger

    gui_hooks.profile_did_open.append(replace_reviewer_functions)

    # This stores the focus morphs seen today, necessary for the respective skipping option to work
    gui_hooks.reviewer_did_answer_card.append(mark_morph_seen)

    # Adds the 'K: V:' to the toolbar
    gui_hooks.top_toolbar_did_init_links.append(add_morph_stats_to_toolbar)

    # See more detailed morph stats by holding 'Shift'-key while pressing 'Stats' in toolbar
    # TODO: maybe move it somewhere less hidden if possible? E.g.a separate toolbar button
    gui_hooks.stats_dialog_will_show(add_morph_stats_to_ease_graph)

    gui_hooks.profile_will_close.append(tear_down_actions_and_submenu)


def init_actions_and_submenu():
    global morphman_sub_menu

    recalc_action = create_recalc_action()
    preferences_action = create_preferences_action()
    database_manager_action = create_database_manager_action()
    readability_analyzer_action = create_readability_analyzer_action()

    morphman_sub_menu = create_morphman_submenu()
    morphman_sub_menu.addAction(recalc_action)
    morphman_sub_menu.addAction(preferences_action)
    morphman_sub_menu.addAction(database_manager_action)
    morphman_sub_menu.addAction(readability_analyzer_action)

    # test_action = create_test_action()
    # morphman_sub_menu.addAction(test_action)


def mark_morph_seen(reviewer: Reviewer, card, ease):
    # Hook gives extra input parameters, hence this seemingly redundant function
    reviewing_utils.mark_morph_seen(card.note())


def replace_reviewer_functions() -> None:
    # This skips the cards the user specified in preferences GUI
    Reviewer.nextCard = hooks.wrap(Reviewer.nextCard, reviewing_utils.my_next_card, "around")

    # Automatically highlights morphs on cards if the respective note stylings are present
    hooks.field_filter.append(reviewing_utils.highlight)


def add_morph_stats_to_toolbar(links, toolbar):
    name, details = morph_stats.get_stats()
    links.append(
        toolbar.create_link(
            "morph", name, morph_stats.on_morph_stats_clicked, tip=details, id="morph"
        )
    )


def add_morph_stats_to_ease_graph():
    anki.stats.CollectionStats.easeGraph = hooks.wrap(anki.stats.CollectionStats.easeGraph, morph_graphs_wrapper,
                                                      "around")


def create_morphman_submenu() -> QMenu:
    global morphman_sub_menu_creation_action

    morphman_sub_menu = QMenu("MorphMan", mw)
    morphman_sub_menu_creation_action = mw.form.menuTools.addMenu(morphman_sub_menu)

    return morphman_sub_menu


def create_test_action() -> QAction:
    action = QAction('&Test', mw)
    action.setStatusTip(_("Recalculate all.db, note fields, and new card ordering"))
    action.setShortcut(_("Ctrl+T"))
    action.triggered.connect(test_function)
    return action


def create_recalc_action() -> QAction:
    action = QAction('&Recalc', mw)
    action.setStatusTip(_("Recalculate all.db, note fields, and new card ordering"))
    action.setShortcut(_("Ctrl+M"))
    action.triggered.connect(main_module.main)
    return action


def create_preferences_action() -> QAction:
    action = QAction('&Preferences', mw)
    action.setStatusTip(_("Change inspected cards, fields and tags"))
    action.setShortcut(_("Ctrl+O"))
    action.triggered.connect(preferencesDialog.main)
    return action


def create_database_manager_action() -> QAction:
    action = QAction('&Database Manager', mw)
    action.setStatusTip(
        _("Open gui manager to inspect, compare, and analyze MorphMan DBs"))
    action.setShortcut(_("Ctrl+D"))
    action.triggered.connect(manager.main)
    return action


def create_readability_analyzer_action() -> QAction:
    action = QAction('Readability &Analyzer', mw)
    action.setStatusTip(_("Check readability and build frequency lists"))
    action.setShortcut(_("Ctrl+A"))
    action.triggered.connect(readability.main)
    return action


def morph_graphs_wrapper(*args, **kwargs):
    importlib.reload(graphs)
    return graphs.morphGraphs(args, kwargs)


def tear_down_actions_and_submenu():
    if morphman_sub_menu is not None:
        morphman_sub_menu.clear()
        mw.form.menuTools.removeAction(morphman_sub_menu_creation_action)


def test_function():
    skipped_cards = reviewing_utils.SkippedCards()

    skipped_cards.skipped_cards['comprehension'] += 10
    skipped_cards.skipped_cards['fresh'] += 1
    skipped_cards.skipped_cards['today'] += 1

    skipped_cards.show_tooltip_of_skipped_cards()


main()
