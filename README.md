# Japanese Translation Assistant

This is an embarrassingly ugly attempt to parse Japanese sentences using SudachiPy and print out the definitions of all of the words using JmDict, falling back to using Google Translate if no dictionary entry exists.
The entire sentence is also translated using Google Translate to give the reader a guide on what sorts of word senses to be looking for. Although Google Translate is notoriously bad at Japanese to English translation, it can sometimes be helpful.

# Example

```
❯ python ja_helper.py 小さい頃ずっと聞いてて最近ふとこの曲が授業中に頭の中で流れてやっと見つけました
小さい 頃 ずっと 聞い て て 最近 ふと この 曲 が 授業 中 に 頭 の 中 で 流れ て やっと 見つけ まし た
I've been listening since I was little and recently found this song flowing in my head during class
小さい [ちいさい] adjective
    small/little/tiny ((adjective (keiyoushi)))

頃 [ころ] noun
    (approximate) time/around/about/toward ((noun (common) (futsuumeishi)|adverbial noun (fukushitekimeishi)|noun, used as a suffix))
    suitable time (or condition)
    time of year/season

ずっと adverb
    continuously in some state (for a long time, distance)/throughout/all along/the whole time/all the way ((adverb (fukushi)))
    much (better, etc.)/by far/far and away
    far away/long ago
    direct/straight

聞いて [きいて] verb (聞く) conjunctive_plain_pos
    to hear ((Godan verb with 'ku' ending|transitive verb))
    to listen (e.g. to music)
    to ask/to enquire/to query
    to learn of/to hear about
    to follow (advice)/to comply with
    to smell (esp. incense)/to sample fragrance

て particle
    casual quoting particle ((particle))
    indicates supposition/if ... then
    indicates a rhetorical question
    indicates certainty, insistence, etc.

最近 [さいきん] noun
    most recent/these days/right now/recently/nowadays ((nouns which may take the genitive case particle 'no'|adverbial noun (fukushitekimeishi)|noun (temporal) (jisoumeishi)))

ふと adverb
    suddenly/casually/accidentally/incidentally/unexpectedly/unintentionally ((adverb (fukushi)))

この pre-noun adjectival
    this (something or someone close to the speaker (including the speaker), or ideas expressed by the speaker) ((pre-noun adjectival (rentaishi)))

曲 [きょく] noun
    song/tune/composition/piece of music ((noun (common) (futsuumeishi)|noun, used as a suffix))

が particle
    indicates sentence subject (occasionally object) ((particle))
    but/however/still/and ((particle|conjunction))
    indicates possessive (esp. in literary expressions)

授業 [じゅぎょう] noun
    lesson/class work/teaching/instruction ((noun (common) (futsuumeishi)|noun or participle which takes the aux. verb suru))

中 [ちゅう] suffix
    medium/average/middle ((noun (common) (futsuumeishi)|prefix|suffix))
    middle school
    China
    volume two (of three)
    in/out of (e.g. three out of ten people)

に particle
    at (place, time)/in/on/during ((particle))
    to (direction, state)/toward/into
    for (purpose)
    because of (reason)/for/with
    by/from
    as (i.e. in the role of)
    per/in/for/a (e.g. "once a month")
    and/in addition to
    if/although

頭 [あたま] noun
    head ((noun (common) (futsuumeishi)))
    hair (on one's head)
    mind/brains/intellect
    leader/chief/boss/captain
    top/tip
    beginning/start
    head/person
    top structural component of a kanji
    pair

の particle
    indicates possessive ((particle))
    nominalizes verbs and adjectives
    substitutes for "ga" in subordinate phrases
    (at sentence-end, falling tone) indicates a confident conclusion
    (at sentence-end) indicates emotional emphasis
    (at sentence-end, rising tone) indicates question

    possessive particle ((particle))

中 [なか] noun
    inside/in ((noun (common) (futsuumeishi)))
    among/within
    center (centre)/middle
    during/while

で particle
    indicates location of action/at/in ((particle))
    indicates certainty, emphasis, etc. ((particle))
    indicates time of action
    indicates means of action/cause of effect/by

流れて [ながれて] verb (流れる) conjunctive_plain_pos
    to stream/to flow (liquid, time, etc.)/to run (ink) ((Ichidan verb|intransitive verb))
    to be washed away/to be carried
    to drift/to float (e.g. clouds)/to wander/to stray
    to sweep (e.g. rumour, fire)/to spread/to circulate
    to be heard (e.g. music)/to be played
    to lapse (e.g. into indolence, despair)
    to pass/to elapse/to be transmitted
    to be called off/to be forfeited
    to disappear/to be removed

やっと adverb
    at last/at length ((adverb (fukushi)))
    barely/narrowly/just/by the skin of one's teeth

見つけました [みつけました] verb (見つける) past_polite_pos
    to discover/to find (e.g. an error in a book)/to come across/to detect/to spot ((Ichidan verb|transitive verb))
    to locate/to find (e.g. something missing)/to find fault
    to be used to seeing/to be familiar with
```
