# Morphman for Anki 2.1

This document will look nicer in the future, please see the various config sections to know what everything does, and "How to Override" to learn how to override the settings.

## goodSentenceLength
Controls how long *good* sentences should be.

+1000 MMI per morpheme outside the "good" length range

*minimum* and *maximum* represent the fewest and most morphs respectively, that a sentence can have and still be in the good sentence range.

## analyzer
Controls settings related to the Readability Analyzer.

*defaultStudyTarget*: **TODO**

*defaultMorphemizer*: Which morphemizer to use by default. 

* Options: **MecabMorphemizer**, **SpaceMorphemizer**, **CjkCharMorphemizer**, **JiebaMorphemizer**

## dbs
Controls DB related settings.

**NOTE: database saving/loading. You can disable these for performance reasons but their semantics are unintuitive, for example: features like morphHighlight always try to load all.db, and expect it to be up to date. Not saving all.db and having it load an out of date copy may produce strange behavior.**

*loadAllDb*: Whether to load existing all.db when recalculating or create one from scratch.

*saveDbs*: Whether to save all.db, known.db, mature.db, and seen.db.


## shortcuts
Controls shortcut related settings.

descriptions of what these shortcuts do are shamelessly stolen and abbreviated from https://massimmersionapproach.com/table-of-contents/anki/morphman/#browser

*browseSameFocus*: Browse morphs with the same focus morph.

*markKnownAndSkip*: Mark selected cards as known and bury.

*batchPlay*: Batch play all media in selected cards.

*extractMorphemes*: Extract morphs from selected cards.

*learnNow*: Put selected cards at the top of the learning queue.

*massTagger*: Add tags to all cards that contain a morph in a specified field from a specified .db file.

*viewMorphemes*: Show all morphs in selected cards.


## weights
Controls weighting related settings.

*reinforceNewVolcab*: remove (*reinforceNewVolcab* / maturity) MMI per known that is not yet mature.

*verbBonus*: remove *verbBonus* MMI if at least one unknown is a verb.

*priorityDb*: remove *priorityDb* MMI per unknown that exists in priority.db

*frequencyTxtScale*: Scale by which card "due" values decrease per unknown in frequency.txt

**Note: It is recommended to lower the scale based on the size of frequency.txt**

**Example: 10k frequencyTxtScale: 2; 5k frequencyTxtScale: 4**

## paths
Controls path settings.

*analysisInput*: Default path to Input directory in Readability Analyzer.

*masterFrequencyList*: Default path to Master Frequency List in Readability Analyzer.

**NOTE: The following paths have complex logic:**

* Leaving them as null will fill them with the embedded default values (same as prior)
* Putting a relative path (one that doesn't start with a drive letter on Windows, or a forward slash on basically everything else) will allow you do use a path relative to the active profile.
* Using an absolute path will work as expected, and will use the same path you put in.

 *dbs*: the path to the dbs directory
 
 *priority*: priority.db
 
 *external*: external.db
 
 *frequency*: frequency.txt
 
 *all*: all.db
 
 *mature*: mature.db
 
 *known*: known.db
 
 *seen*: seen.db
 
 *log*: morphman.log
 
 *stats*: morphman.stats

## parser
Controls settings related to morpheme parsing.

*ignoreGrammarPosition*: if true, ignores morpheme grammar positions.  It's recommended to delete your all.db if changed.

## media
Controls settings related to media.

*batchPlayerFields*: try playing fields in the given order when using batch media player.

## alternatives
Controls settings related to cards with the same focus morph as the one just reviewed.

*autoSkip*: Controls whether cards with the same focus morph as the one just reviewed should be automatically buried.

*printNumberSkipped*: Controls whether or not to print the number of cards skipped by *autoSkip*

## thresholds
Controls time related settings.

**NOTE: In an older version of Morphman, these settings were measured in days, however, here they are measured in seconds, this is because json can't do math. (although, it does support floating point numbers, "0.0001157407407407407" seems to be the worse of the two evils**

*mature*: How long until a morph is considered mature. 21 days is what Anki uses.

*known*: How long until a morph is considered known. Recommend a few seconds if you want to count things in learning queue or ~3 days otherwise.

*seen*: **TODO**. 

*textFileImportMaturity*: When you import a file via Extract Morphemes From File, they are all given this maturity.

## updates
Controls morphman recalc related settings.

*only2TAndBelowCards*: Only recalc cards if they are 2T or harder.

*setDueBasedOnMMI*: Use the MorphManIndex of a card to set its due value.

*ignoreMaturity*: Pretends card maturity is always zero if true.

## How to Override
Everything can be overridden per profile by adding an entry to *profileOverrides* for the profile and adding the key there. 

For instance, if you have a config file like this:

```json
{
  "default": {
    "goodSentenceLength": { "min": 2, "max": 8 }
  },
  "profileOverrides": []
}
```

To override the minimum sentence length in the 'Japanesey' profile, you'd do this:

```json
{
  "default": "<snip>",
  "profileOverrides": [
    {
      "name": "Japanesey",
      "goodSentenceLength": { "min": 5 }
    }
  ]
}
```

Deck overrides and model overrides can be done in the same way. However, they can only be done on certain groups:

Deck overrides can only be done on the *newCards* group, trying to override something else will cause the override to be ignored.

Model overrides can only be done on the *media*, **TODO** groups and *autoSkip* from *alternatives*.

The priority for overrides is `deckOverrides > modelOverrides > profileOverrides > default`, anything missing will go down the list until it hits the default.

