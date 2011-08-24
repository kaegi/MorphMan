v2.0

A fully automated system that constantly keeps track of what you know (in terms of morphemes) across all your decks and updates card fields with their current

* i+N value
* the unknowns in a sentence
* vocab rank - the estimated difficulty of learning the words in the sentence based on the kanji/readings they use and their positions in the words compared to what you've seen before
* morph man index - an overall suggested order to learn sentences in, which it uses to modify card creation times to make new cards appear in order of difficulty

The new database format also keeps track of the location morphemes were found in, which will assist in the addition of future features.

There are also the standard features of the old plugin:

* mass tagger - set tags on all facts whose morphemes are in the user provided database

* morpheme matcher - find a maximal cardinality bipartite matching (ie, the best 1:1 pairing) between morphemes in the selected fact's Expression field and a user provided database, and note the matching in the "matchedMorpheme" field.

* manager for analyzing, comparing, merging dbs, and creating dbs from text files

more details at http://forum.koohii.com/viewtopic.php?id=8074


Notes:

* New decks aren't processed until you re-open anki since you're probably still setting it up and thus don't want Morph Man tying it up until it's ready

* Morph Man can be stopped/restarted via the MorphMan gui. This is useful in case it's in the middle of updating a deck you want to use and your computer is slow

* By default Morph Man does it's checks every few seconds and logs to a file. If you use battery powered laptop you may want to disable logging (change NO_LOG to True in util.py )
