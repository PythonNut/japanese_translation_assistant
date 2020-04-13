import sys
import requests
import googletrans
import subprocess
import collections
import re
import jaconv
import itertools

from pathlib import Path
from typing import List, Tuple, Set
from sudachipy import tokenizer, dictionary, morpheme
from jamdict import Jamdict, jmdict
from japaneseverbconjugator.src import (
    JapaneseVerbFormGenerator as japaneseVerbFormGenerator,
)
from japaneseverbconjugator.src.constants.EnumeratedTypes import (
    VerbClass,
    Tense,
    Polarity,
    Formality,
)

jvfg = japaneseVerbFormGenerator.JapaneseVerbFormGenerator()
tokenizer_obj = dictionary.Dictionary().create()
jmd = Jamdict()
google_translate = googletrans.Translator()
google_translate.session.mount(googletrans.urls.BASE, requests.adapters.HTTPAdapter())

SUDACHI_POS_MAP = {
    "感動詞": "interjection",
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


def guess_verb_class(pos):
    if "五段" in pos[4]:
        return VerbClass.GODAN
    elif "一段" in pos[4]:
        return VerbClass.ICHIDAN
    elif "変格" in pos[4]:
        return VerbClass.IRREGULAR

    print(f"Unrecognized verb: {m.surface()} {pos}")
    return


def morpheme_to_str(m: morpheme.Morpheme):
    surface = m.surface()
    dform = m.dictionary_form()
    pos = m.part_of_speech()
    return f"Morpheme({repr(surface)}, dform={repr(dform)}, pos={repr(pos)})"


morpheme.Morpheme.__str__ = morpheme_to_str
morpheme.Morpheme.__repr__ = morpheme_to_str


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
    dict_reading = parse(m.dictionary_form())[0].reading_form()
    for search in set((m.dictionary_form(), m.normalized_form())):
        for entry in jmd.lookup(search).entries:
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


def i_adj_short_form(dict_form, tense, polarity):
    if tense == Tense.PAST:
        if polarity == Polarity.NEGATIVE:
            return dict_form[:-1] + "くなかった"
        else:
            return dict_form[:-1] + "かった"
    else:
        if polarity == Polarity.NEGATIVE:
            return dict_form[:-1] + "くない"
        else:
            return dict_form


def all_verb_conjugations(verb, verb_class, sort_keys=False):
    # This is a terrible hack because JVC doesn't support 来る
    if verb == "来る" and verb_class == VerbClass.IRREGULAR:
        kana_conj = all_verb_conjugations("くる", VerbClass.IRREGULAR, sort_keys)
        return {k: "来" + v[1:] if v else None for k, v in kana_conj.items()}

    result = {}
    polarities = [(Polarity.POSITIVE, "positive"), (Polarity.NEGATIVE, "negative")]
    formalities = [(Formality.POLITE, "polite"), (Formality.PLAIN, "plain")]
    tenses = [(Tense.PAST, "past"), (Tense.NONPAST, "nonpast")]

    te = jvfg.generate_te_form(verb, verb_class)

    # Handle the 行く irregularity
    if verb == "行く" and verb_class == VerbClass.GODAN:
        te = "行って"

    result["te"] = te

    polite = jvfg.generate_polite_form(
        verb, verb_class, Tense.NONPAST, Polarity.POSITIVE
    )
    assert polite.endswith("ます")
    stem = polite[:-2]
    tai = stem + "たい"
    tai3 = stem + "たがっている"
    progressive = te + "いる"
    result["progressive_plain"] = progressive

    for (t_o, t_s), (p_o, p_s) in itertools.product(tenses, polarities):
        result[f"plain_{t_s}_{p_s}"] = jvfg.generate_plain_form(
            verb, verb_class, t_o, p_o
        )
        result[f"polite_{t_s}_{p_s}"] = jvfg.generate_polite_form(
            verb, verb_class, t_o, p_o
        )

        result[f"tai_{t_s}_{p_s}"] = i_adj_short_form(tai, t_o, p_o)
        result[f"tai_3rd_plain_{t_s}_{p_s}"] = jvfg.generate_plain_form(
            tai3, VerbClass.ICHIDAN, t_o, p_o
        )
        result[f"tai_3rd_polite_{t_s}_{p_s}"] = jvfg.generate_polite_form(
            tai3, VerbClass.ICHIDAN, t_o, p_o
        )

        result[f"progressive_polite_{t_s}_{p_s}"] = jvfg.generate_polite_form(
            progressive, VerbClass.ICHIDAN, t_o, p_o
        )

    for (f_o, f_s), (p_o, p_s) in itertools.product(formalities, polarities):
        result[f"conditional_{p_s}_{f_s}"] = jvfg.generate_conditional_form(
            verb, verb_class, f_o, p_o
        )
        result[f"volitional_{p_s}_{f_s}"] = jvfg.generate_volitional_form(
            verb, verb_class, f_o, p_o
        )
        result[f"potential_{p_s}_{f_s}"] = jvfg.generate_potential_form(
            verb, verb_class, f_o, p_o
        )
        result[f"imperative_{p_s}_{f_s}"] = jvfg.generate_imperative_form(
            verb, verb_class, f_o, p_o
        )
        result[f"provisional_{p_s}_{f_s}"] = jvfg.generate_provisional_form(
            verb, verb_class, f_o, p_o
        )
        result[f"causative_{p_s}_{f_s}"] = jvfg.generate_causative_form(
            verb, verb_class, f_o, p_o
        )
        result[f"passive_{p_s}_{f_s}"] = jvfg.generate_passive_form(
            verb, verb_class, f_o, p_o
        )

    # Compute alternate plain forms for the negative provisional
    provisional_neg_plain = result["provisional_negative_plain"]
    if provisional_neg_plain and provisional_neg_plain.endswith("なければ"):
        result["provisional_plain2_negative"] = provisional_neg_plain[:-4] + "なきゃ"
        result["provisional_plain3_negative"] = provisional_neg_plain[:-4] + "なくちゃ"

    if sort_keys:
        result = {k: v for k, v in sorted(result.items())}

    return result


def flip_dict(d):
    result = {}
    for k, v in d.items():
        result.setdefault(v, []).append(k)
    return result


def post_parse(morphs: List[morpheme.Morpheme]):
    morphs.reverse()
    result = []
    while morphs:
        m = morphs.pop()
        pos = m.part_of_speech()
        sudachi_pos = SUDACHI_POS_MAP.get(pos[0], "")

        if sudachi_pos == "verb":
            vclass = guess_verb_class(m.part_of_speech())
            if vclass:
                conj_map = flip_dict(all_verb_conjugations(m.dictionary_form(), vclass))

                limit = 0
                while len(morphs) > limit and SUDACHI_POS_MAP.get(
                    morphs[-limit - 1].part_of_speech()[0]
                ) in ("auxiliary verb", "particle", "verb"):
                    limit += 1

                conj = None
                num = 0
                for l in range(limit, 0, -1):
                    suffix = morphs[-1 : -l - 1 : -1]
                    cand = m.surface() + "".join(aux.surface() for aux in suffix)
                    if cand in conj_map:
                        conj = conj_map[cand]
                        num = l
                        break

                if conj:
                    result.append((m, morphs[-1 : -num - 1 : -1], conj))
                    for _ in range(num):
                        morphs.pop()
                    continue

        result.append((m, [], None))

    return result


def parse(text):
    mode = tokenizer.Tokenizer.SplitMode.B
    return list(tokenizer_obj.tokenize(text, mode))


def translation_assist(text):
    morphs = parse(text)
    print(" ".join(m.surface() for m in morphs))
    print(google(text))

    chunks = post_parse(morphs)

    morphemes_seen = set()

    for (m, rest, conj) in chunks:
        pos = m.part_of_speech()
        dform = m.dictionary_form()
        surface = m.surface() + "".join(aux.surface() for aux in rest)
        reading = jaconv.kata2hira(m.reading_form()) + "".join(
            jaconv.kata2hira(aux.reading_form()) for aux in rest
        )

        sudachi_pos = SUDACHI_POS_MAP.get(pos[0], "") or pos[0]
        if sudachi_pos == "blank space":
            continue

        match_reading = True
        if sudachi_pos == "supplementary symbol":
            entries = jmd.lookup(dform).entries
            if re.match(f"{alphanum_re}+", surface) or not entries:
                continue

            if reading == "きごう":
                match_reading = False
                reading = None

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
            print(
                "    No matches",
                m.surface(),
                m.dictionary_form(),
                m.reading_form(),
                ", ".join(pos),
            )
            print(f"    {google(dform)}")
            print()

        for entry, senses in entries:
            if not senses:
                print("    No senses???")
                continue
            for i in senses:
                sense = str(entry.senses[i]).replace("`", "'")
                print(f"    {sense}")
            print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        translation_assist(" ".join(sys.argv[1:]))
