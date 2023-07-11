# Multi-language support

If you want to study multiple languages but keep using the same Anki profile, it's now possible with the new multi-language support. This means that each target language has its own frequency list and databases, neatly separated into distinct files.


## Setup

*Morphman Preferences -> Note Filter* window has now a new column for selecting the target language for each filter.  By selecting for example '*Japanese*'  the Morphman will use the following files for that specific filter: 

 - frequency_Japanese.txt
 - all_Japanese.db
 - seen_Japanese.db
 - known_Japanese.db
 - mature_Japanese.db
 - external_Japanese.db
 - priority_Japanese.db
 
**Default** setting means that Morphman will keep using the existing frequencylist.txt, all.db, known.db .. files for backwards compatibility when processing that filter. 

The language list is currently hard-coded, but if you need to add a new one you can do that easily by editing *preferences.py*, or select **Other** . In the latter case Morphman would use files such as *known_Other.txt*

If you have existing **frequency.txt** and **external.db** files, you can rename them to reflect the target language (e.g. *frequency_Japanese.txt* and *external_Japanese.db*). You can then delete the rest of the database files and do a Recalc.

## Changes in Readability Analyzer

When using *Readability Analyzer* you must now explicitly select both Known and Mature database files (because it will not try to infer the mature morph database file name from known data base file).  If generating frequency lists the  output file name is currently fixed *frequency.txt* so you will need to manually rename it for the specific language.