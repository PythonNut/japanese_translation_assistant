# Japanese Translation Assistant

This is an embarrassingly ugly attempt to parse Japanese sentences using SudachiPy and print out the definitions of all of the words using JmDict, falling back to using Google Translate if no dictionary entry exists.
The entire sentence is also translated using Google Translate to give the reader a guide on what sorts of word senses to be looking for. Although Google Translate is notoriously bad at Japanese to English translation, it can sometimes be helpful.

# Example

```
❯ python ja_helper.py 小さい頃ずっと聞いてて最近ふとこの曲が授業中に頭の中で流れてやっと見つけました。
小さい 頃 ずっと 聞いて て 最近 ふと この 曲 が 授業中 に 頭 の 中 で 流れて やっと 見つけました 。
I listened to it all the time when I was little, and recently I suddenly found this song in my head during class.
小さい [ちいさい] adjective non-past_plain_pos
    small/little/tiny (adj-i)

頃 [ころ] noun
    (approximate) time/around/about/toward (n|n-adv|n-suf)
    suitable time (or condition)
    time of year/season

ずっと adverb
    continuously in some state (for a long time, distance)/throughout/all along/the whole time/all the way (adv)
    much (better, etc.)/by far/far and away
    far away/long ago
    direct/straight

聞いて [きいて] verb (聞く) conjunctive_plain_pos
    to hear (v5k|vt)
    to listen (e.g. to music)
    to ask/to enquire/to query
    to learn of/to hear about
    to follow (advice)/to comply with
    to smell (esp. incense)/to sample fragrance

て particle
    casual quoting particle (prt)
    indicates supposition/if ... then
    indicates a rhetorical question
    indicates certainty, insistence, etc.

最近 [さいきん] noun
    most recent/these days/right now/recently/nowadays (adj-no|n-adv|n-t)

ふと adverb
    suddenly/casually/accidentally/incidentally/unexpectedly/unintentionally (adv)

この pre-noun adjectival
    this (something or someone close to the speaker (including the speaker), or ideas expressed by the speaker) (adj-pn)

曲 [きょく] noun
    song/tune/composition/piece of music (n|n-suf)

が particle

授業中 [じゅぎょうちゅう] noun
    while in class (n)

に particle

頭 [あたま] noun
    head (n)
    hair (on one's head)
    mind/brains/intellect
    leader/chief/boss/captain
    top/tip
    beginning/start
    head/person
    top structural component of a kanji
    pair

の particle

中 [なか] noun
    inside/in (n)
    among/within
    center (centre)/middle
    during/while

で particle

流れて [ながれて] verb (流れる) conjunctive_plain_pos
    to stream/to flow (liquid, time, etc.)/to run (ink) (v1|vi)
    to be washed away/to be carried
    to drift/to float (e.g. clouds)/to wander/to stray
    to sweep (e.g. rumour, fire)/to spread/to circulate
    to be heard (e.g. music)/to be played
    to lapse (e.g. into indolence, despair)
    to pass/to elapse/to be transmitted
    to be called off/to be forfeited
    to disappear/to be removed

やっと adverb
    at last/at length (adv)
    barely/narrowly/just/by the skin of one's teeth

見つけました [みつけました] verb (見つける) past_polite_pos
    to discover/to find (e.g. an error in a book)/to come across/to detect/to spot (v1|vt)
    to locate/to find (e.g. something missing)/to find fault
    to be used to seeing/to be familiar with
```
