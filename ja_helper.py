import sys
import requests
import googletrans
import re
import jaconv
import romkan
import functools

from pathlib import Path
from typing import List, Tuple
from sudachipy import tokenizer, dictionary, morpheme
from dataclasses import dataclass
from jamdict import Jamdict, jmdict
from japaneseverbconjugator.src.constants.EnumeratedTypes import VerbClass
import jconj.conj as jconj

CT = jconj.read_conj_tables("./jconj/data")
JMDICT_ABBREV_MAP = {v: k for k, vs in CT["kwpos"].items() for v in vs}
JMDICT_ABBREV_MAP["expressions (phrases, clauses, etc.)"] = "exp"

tokenizer_obj = dictionary.Dictionary().create()
jmd = Jamdict()
google_translate = googletrans.Translator()

SUDACHI_POS_MAP = {
    "感動詞": "interjection",
    "記号": "symbol",
    "補助記号": "supplementary symbol",
    "名詞": "noun",
    "接尾辞": "suffix",
    "助詞": "particle",
    "形容詞": "adjective",  # "i-adjective",
    "助動詞": "auxiliary verb",
    "代名詞": "pronoun",
    "空白": "blank space",
    "動詞": "verb",
    "接頭辞": "prefix",
    "形状詞": "classifier",
    "副詞": "adverb",
    "連体詞": "pre-noun adjectival",
    "接続詞": "conjunction"
}

SUDACHI_POS_REGEX_MAP = {
    "interjection": "i",
    "symbol": "y",
    "supplementary symbol": "Y",
    "noun": "n",
    "suffix": "s",
    "particle": "p",
    "adjective": "j",
    "auxiliary verb": "x",
    "pronoun": "r",
    "blank space": "b",
    "verb": "v",
    "prefix": "P",
    "classifier": "c",
    "adverb": "a",
    "pre-noun adjectival": "J",
    "conjunction": "o",
}

# 4E00    9FEF    http://www.unicode.org/charts/PDF/U4E00.pdf CJK Unified Ideographs
# 3400    4DBF    http://www.unicode.org/charts/PDF/U3400.pdf CJK Unified Ideographs Extension A
# 20000   2A6DF   http://www.unicode.org/charts/PDF/U20000.pdf    CJK Unified Ideographs Extension B
# 2A700   2B73F   http://www.unicode.org/charts/PDF/U2A700.pdf    CJK Unified Ideographs Extension C
# 2B740   2B81F   http://www.unicode.org/charts/PDF/U2B740.pdf    CJK Unified Ideographs Extension D
# 2B820   2CEAF   http://www.unicode.org/charts/PDF/U2B820.pdf    CJK Unified Ideographs Extension E
# 2CEB0   2EBEF   https://www.unicode.org/charts/PDF/U2CEB0.pdf   CJK Unified Ideographs Extension F
# 3007    3007    https://zh.wiktionary.org/wiki/%E3%80%87    in block CJK Symbols and Punctuation
kanji_re = "[\u4E00-\u9FEF\u3400-\u4DBF\U00020000-\U0002A6DF\U0002A700-\U0002B73F\U0002B740-\U0002B81F\U0002B820-\U0002CEAF\U0002CEB0-\U0002EBEF]"
hira_re = "[\u3040-\u309F]"
kata_re = "[\u30A0-\u30FF]"
alphanum_re = "[\uFF01-\uFF5E]"


def google(text):
    return google_translate.translate(text, src="ja", dest="en").text


@functools.lru_cache(maxsize=None)
def jmdict_lookup(s):
    return jmd.lookup(s)


def guess_verb_class(pos):
    if "五段" in pos[4]:
        return VerbClass.GODAN
    elif "一段" in pos[4]:
        return VerbClass.ICHIDAN
    elif "変格" in pos[4]:
        return VerbClass.IRREGULAR
    elif pos[4].startswith("助動詞-"):
        # Todo: this is just a heuristic
        rest = pos[4][4:]
        r = romkan.to_roma(rest)
        if r.endswith("u") and re.match(f"{kata_re}+", rest):
            if r.endswith("ru"):
                if r[-3] in "ie":
                    return VerbClass.ICHIDAN

            return VerbClass.GODAN

    print(f"Unrecognized verb: {pos}")
    return


def morpheme_to_str(m: morpheme.Morpheme):
    surface = m.surface()
    dform = m.dictionary_form()
    pos = m.part_of_speech()
    return f"Morpheme({repr(surface)}, dform={repr(dform)}, pos={repr(pos)})"


morpheme.Morpheme.__str__ = morpheme_to_str
morpheme.Morpheme.__repr__ = morpheme_to_str


@dataclass
class MultiMorpheme(object):
    morphemes: List[morpheme.Morpheme]

    def surface(self):
        return "".join(m.surface() for m in self.morphemes)

    def reading_form(self):
        return "".join(m.reading_form() for m in self.morphemes)

    def parts_of_speech(self):
        return [m.part_of_speech() for m in self.morphemes]

    def pos_str(self):
        return ''.join(SUDACHI_POS_REGEX_MAP[SUDACHI_POS_MAP[pos[0]]] for pos in self.parts_of_speech())

    def composition_check(self):
        if len(self.morphemes) == 1:
            return True

        pos = self.pos_str()
        if re.fullmatch("[rn](s|[pjx]*)", pos):
            return True
        elif re.fullmatch("v[vpx]*", pos):
            return True
        elif re.fullmatch("x(p|[vx]*)", pos):
            return True
        elif re.fullmatch("j[jx]+", pos):
            return True

        return False

    def maybe_potential_form(self):
        pos = self.pos_str()
        surface = self.surface()

        if (
            pos[0] == "v"
            and len(self.morphemes) == 1
            and self.morphemes[0].dictionary_form() == surface
            and romkan.to_roma(surface).endswith("eru")
            and not jmdict_lookup(surface).entries
        ):
            suf = romkan.to_hiragana(romkan.to_roma(surface[-2:]).replace("eru", "u"))
            result = surface[:-2] + suf
            if jmdict_lookup(result).entries:
                return result

    def dictionary_form(self):
        assert self.composition_check()
        pos = self.pos_str()

        potential_form = self.maybe_potential_form()
        if potential_form:
            return potential_form

        if pos[0] == "v":
            i = pos.rindex('v')
            return ''.join(self.morphemes[j].surface() for j in range(i)) + self.morphemes[i].dictionary_form()

        elif pos[0] == "j":
            return self.morphemes[0].dictionary_form()

        result = []
        for m in self.morphemes:
            result.append(m.dictionary_form())
            if m.dictionary_form() != m.surface():
                break

        return "".join(result)

    def part_of_speech(self):
        assert self.composition_check()
        pos = self.pos_str()

        potential_form = self.maybe_potential_form()
        if potential_form:
            return parse(potential_form)[0].part_of_speech()

        if pos[0] == "v":
            i = pos.rindex('v')
            return self.morphemes[i].part_of_speech()

        if pos[0] in "jx":
            return self.morphemes[0].part_of_speech()

        i = 1
        while pos[-i] in "xs" and i < len(pos):
            i += 1

        return self.morphemes[-i].part_of_speech()

    def all_conjugations(self):
        dform = self.dictionary_form()
        pos = self.part_of_speech()
        return merge_multi_dicts(
            *[flip_multi_dict(m) for m in all_conjugations(dform, pos).values()]
        )

    def lookup(self):
        dform = self.dictionary_form()
        pos = self.part_of_speech()

        if dform == self.surface():
            return jmdict_lookup(self.surface()).entries

        if self.surface() in self.all_conjugations():
            return jmdict_lookup(dform).entries

    def detect_conjugation(self):
        return self.all_conjugations().get(self.surface(), [])

    def score(self):
        return bool(self.lookup()) * len(self.morphemes) ** 2


def sudachi_jmdict_pos_match(s_pos: Tuple[str, ...], j_pos: str):
    s_base_pos = SUDACHI_POS_MAP.get(s_pos[0], "")
    if s_base_pos == "verb":
        vclass = guess_verb_class(s_pos)
        if vclass == VerbClass.GODAN:
            return j_pos.startswith("Godan verb")

        elif vclass == VerbClass.ICHIDAN:
            return j_pos.startswith("Ichidan verb")

        elif vclass == VerbClass.IRREGULAR:
            if s_pos[4] == "サ行変格":
                return j_pos.startswith("suru verb")

            elif s_pos[4] == "カ行変格":
                return j_pos.startswith("Kuru verb")

            return j_pos.endswith("irregular")

        return "verb" in j_pos
    elif s_base_pos == "auxiliary verb":
        return not j_pos.startswith("noun")

    elif s_base_pos == "classifier":
        return j_pos.startswith("adjectival nouns")

    else:
        return j_pos.startswith(s_base_pos)


def search_morpheme(
    m: morpheme.Morpheme, match_reading=True
) -> Tuple[List[jmdict.JMDEntry], List[int]]:
    pos = m.part_of_speech()
    has_kanji = re.search(kanji_re, m.surface())
    ids = set()
    entries: List[jmdict.JMDEntry] = []
    reading = m.reading_form()
    dict_reading = "".join(m.reading_form() for m in parse(m.dictionary_form()))
    for entry in jmdict_lookup(m.dictionary_form()).entries:
        if entry.idseq not in ids:
            ids.add(entry.idseq)
            entries.append(entry)

    matches: Tuple[List[jmdict.JMDEntry], List[int]] = []
    reading_matches: Tuple[List[jmdict.JMDEntry], List[int]] = []
    for entry in entries:
        if match_reading and not any(
            jaconv.hira2kata(r.text) in (reading, dict_reading)
            for r in entry.kana_forms
        ):
            continue

        match_senses = list()
        senses = list()
        reading_matches.append((entry, set(range(len(entry.senses)))))
        for i, sense in enumerate(entry.senses):
            if not sense.pos:
                senses.append(i)
            elif any(sudachi_jmdict_pos_match(pos, p) for p in sense.pos):
                senses.append(i)
                match_senses.append(i)

        def sense_key(i):
            sense = entry.senses[i]
            uk_match = (
                has_kanji != "word usually written using kana alone" in sense.misc
            )
            common = any(("common" in p or "futsuumeishi" in p) for p in sense.pos)
            has_pos = bool(sense.pos)
            return (uk_match, common, has_pos)

        senses.sort(key=sense_key, reverse=True)

        if match_senses:
            matches.append((entry, senses))

    if not matches:
        return reading_matches

    return matches


def sudachi_jmdict_abbrev_match(s_pos: Tuple[str, ...], j_pos: str):
    s_base_pos = SUDACHI_POS_MAP.get(s_pos[0], "")
    if s_base_pos in ("verb", "auxiliary verb"):
        vclass = guess_verb_class(s_pos)
        if vclass == VerbClass.GODAN:
            return j_pos.startswith("v5")

        elif vclass == VerbClass.ICHIDAN:
            return j_pos.startswith("v1")

        elif vclass == VerbClass.IRREGULAR:
            if s_pos[4] == "サ行変格":
                return j_pos in ("vs-i", "vs-s")

            elif s_pos[4] == "カ行変格":
                return j_pos == "vk"

        return "verb" in j_pos

    elif s_base_pos == "noun":
        return j_pos == "n" or j_pos.startswith("n-")

    elif s_base_pos == "adjective":
        return j_pos.startswith("adj")


def guess_exact_pos(dict_form, pos):
    if dict_form in ("だ", "です") and pos[4] in ("助動詞-ダ", "助動詞-デス"):
        return "だ", ["cop-da"]

    entries = jmdict_lookup(dict_form).entries
    pos_strs = {p for e in entries for s in e.senses for p in s.pos}
    pos_abbrevs = [a for p in pos_strs if (a := JMDICT_ABBREV_MAP.get(p))]
    pos_matches = [
        p
        for p in pos_abbrevs
        if CT["kwpos"][p][0] in [x[0] for x in CT["conjo"]]
        and sudachi_jmdict_abbrev_match(pos, p)
    ]

    return dict_form, pos_matches


def all_conjugations(dict_form, pos, refs=False):
    dict_form, pos_matches = guess_exact_pos(dict_form, pos)
    result = {}

    for pos_match in pos_matches:
        conjugations, ref_map = all_conjugations_helper(dict_form, pos_match)
        if refs:
            result[pos_match] = conjugations, ref_map
        else:
            result[pos_match] = conjugations

    return result


def all_conjugations_helper(dict_form: str, pos_match: str, cases=None):
    pos = CT["kwpos"][pos_match][0]
    has_kanji = re.search(kanji_re, dict_form)

    if has_kanji:
        kanji, kana = dict_form, None
    else:
        kanji, kana = None, dict_form

    conjs = jconj.conjugate(kanji, kana, pos, CT)

    entry, ref_map = {}, {}
    for (_, case, neg, pol, _), v in conjs.items():
        if cases and case not in cases:
            continue
        neg_str = "neg" if neg else "pos"
        pol_str = "polite" if pol else "plain"
        type_str = CT["conj"][case][1].lower().split(" ")[0]
        key = f"{type_str}_{pol_str}_{neg_str}"
        entry.setdefault(key, []).append(v)
        ref_map[case, neg, pol] = key

    if pos_match.startswith("v") and (not cases or 4 in cases):
        prov_neg_plains = entry[ref_map[4, True, False]]
        for prov_neg_plain in list(prov_neg_plains):
            if prov_neg_plain.endswith("なければ"):
                prov_neg_plains.extend(
                    (prov_neg_plain[:-4] + "なきゃ", prov_neg_plain[:-4] + "なくちゃ")
                )

    if pos_match.startswith("v") and (not cases or 6 in cases):
        passive = entry[ref_map[6, False, False]][0]
        assert passive.endswith("る")
        key = "passive_conjunctive_plain_pos"
        entry[key] = [passive[:-1] + "て"]
        ref_map[(6, 3, False, False)] = key

    if pos_match.startswith("v") and (not cases or 14 in cases):
        plain_pos_pol = entry[ref_map[1, False, True]]
        assert len(plain_pos_pol) == 1
        renyoukei = plain_pos_pol[0][:-2]
        tai = renyoukei + "たい"

        tai_entry, tai_ref = all_conjugations_helper(tai, "adj-i")
        tai_reverse = {v: k for k, v in tai_ref.items()}
        tai_entry[tai_ref[1, False, False]].extend((renyoukei + "てぇ", renyoukei + "てー"))

        for k, v in tai_entry.items():
            key = f"tai_{k}"
            entry[key] = v
            ref_map[(14, *tai_reverse[k])] = key

        tai3 = renyoukei + "たがっている"
        # The same set of conjugations as an adjective
        # TODO: Actually determine which conjugations are allowed here
        tai3_entry, tai3_ref = all_conjugations_helper(
            tai3, "v1", {1, 2, 3, 4, 7, 9, 12, 13}
        )
        tai3_reverse = {v: k for k, v in tai3_ref.items()}

        for k, v in tai3_entry.items():
            key = f"tai3_{k}"
            entry[key] = v
            ref_map[(14, *tai3_reverse[k])] = key

    if pos_match.startswith("v") and (not cases or 15 in cases):
        tes = entry[ref_map[3, False, False]]
        assert len(tes) == 1
        progressive = tes[0] + "いる"
        prog_entry, prog_ref = all_conjugations_helper(progressive, "v1", {1, 2})
        prog_reverse = {v: k for k, v in prog_ref.items()}

        for k, v in prog_entry.items():
            key = f"progressive_{k}"
            entry[key] = v
            ref_map[(15, *prog_reverse[k])] = key

        entry[ref_map[15, 1, False, False]].append(tes[0] + "る")
        entry[ref_map[15, 2, False, False]].append(tes[0] + "た")

    if pos_match == "cop-da":
        for k, vs in entry.items():
            for v in vs:
                if v.startswith("では"):
                    entry[k].append("じゃ" + v[2:])

    return entry, ref_map


def flip_multi_dict(d):
    result = {}
    for k, vs in d.items():
        for v in vs:
            result.setdefault(v, []).append(k)
    return result


def merge_multi_dicts(*ds):
    result = {}
    for d in ds:
        for k, v in d.items():
            result.setdefault(k, []).extend(v)
    return result


def post_parse(morphemes: List[morpheme.Morpheme]):
    n = len(morphemes)
    dp = [(float("-inf"), None) for _ in range(n)]

    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n + 1):
            unit = MultiMorpheme(morphemes[i:j])
            if not unit.composition_check():
                continue

            unit_score = unit.score()

            if j == n:
                if unit_score >= dp[i][0]:
                    dp[i] = unit_score, [unit]
                break

            rest_score, rest = dp[j]
            score = unit_score + rest_score
            if rest and score >= dp[i][0]:
                dp[i] = score, [unit] + rest

    return dp[0][1]


def parse(text):
    mode = tokenizer.Tokenizer.SplitMode.A
    return list(tokenizer_obj.tokenize(text, mode))


def display_part_of_speech(m: MultiMorpheme):
    pos = m.part_of_speech()
    sudachi_pos = SUDACHI_POS_MAP.get(pos[0], "") or pos[0]

    if sudachi_pos == "noun" and pos[1] == "数詞":
        return "numeral"
    elif sudachi_pos == "noun" and pos[1] == "固有名詞":
        return "proper noun"

    return sudachi_pos


def translation_assist(text):
    morphs = post_parse(parse(text))
    print(" ".join(m.surface() for m in morphs))
    print(google(text))

    morphemes_seen = set()

    for m in morphs:
        pos = m.part_of_speech()
        dform = m.dictionary_form()
        conj = m.detect_conjugation()
        surface = m.surface()
        reading = jaconv.kata2hira(m.reading_form())

        sudachi_pos = display_part_of_speech(m)
        if sudachi_pos == "blank space":
            continue

        match_reading = True
        if sudachi_pos == "supplementary symbol":
            entries = jmdict_lookup(dform).entries
            if re.match(f"{alphanum_re}+", surface) or not entries:
                continue

            if reading == "きごう":
                match_reading = False
                reading = None

        elif sudachi_pos == "particle" and surface in "がでとにのはへを":
            print(f"{surface} particle\n")
            continue

        elif sudachi_pos == "numeral":
            print(f"{surface} [{reading}] numeral\n")
            continue

        dform_str = ""
        if dform != m.surface():
            dform_str = f" ({dform})"

        conj_str = ""
        if conj:
            conj_str = " " + " ".join(conj)

        reading_str = ""
        if reading and reading != surface:
            reading_str = f" [{reading}]"
        print(f"{surface}{reading_str} {sudachi_pos}{dform_str}{conj_str}")

        seen = (tuple(pos), dform, surface, reading)
        if seen in morphemes_seen:
            print("    [see above]\n")
            continue
        morphemes_seen.add(seen)

        entries = search_morpheme(m, match_reading=match_reading)

        if not entries:
            if sudachi_pos != "proper noun":
                print(
                    "    No matches", ", ".join(pos),
                )

            print(f"    [google] {google(dform)}")
            print()

        for entry, senses in entries:
            if not senses:
                print("    No senses???")
                continue
            for i in senses:
                sense = entry.senses[i]
                pos_str = ""
                if sense.pos:
                    pos_str = " ({})".format(
                        "|".join(JMDICT_ABBREV_MAP.get(p, p) for p in sense.pos)
                    )

                gloss = sense.text().replace("`", "'")

                print(f"    {gloss}{pos_str}")
            print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        translation_assist(" ".join(sys.argv[1:]))
