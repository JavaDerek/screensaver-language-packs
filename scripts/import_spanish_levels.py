#!/usr/bin/env python3
"""Rebuild Spanish packs from pinned ELELex and Spanish/English WordNet data.

Only the build uses downloads. Playback and the test suite work offline with the
installed packs. Spanish data licenses are documented in the language-packs repository.
"""
from __future__ import annotations

import argparse
import collections
import csv
from decimal import Decimal
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import unicodedata
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.spanish_advanced_headwords import C1, C2
from scripts.spanish_legacy_headwords import LEGACY

OUTPUT = Path(__file__).resolve().parent.parent / "dist/spanish"
LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
OMW_REV = "406bf83b3c507a3d1f26e88252d5d66893fd36bf"
NLTK_REV = "550b6625bcef1f2abff2ff770a5a0d272c9c6b2a"
SOURCES = {
    "ELELex.tsv": {
        "url": "https://cental.uclouvain.be/cefrlex/static/resources/es/ELELex.tsv",
        "sha256": "87a28dc6d3c5c2344883698f7bc77e259bd42212446ac2b52761a3fc8f5f26cf",
        "license": "CC-BY-NC-SA-4.0", "snapshot_date": "2026-11-06",
    },
    "mcr-spa.tab": {
        "url": f"https://raw.githubusercontent.com/omwn/omw-data/{OMW_REV}/wns/mcr/wn-data-spa.tab",
        "sha256": "0ec37ce94ee2acc63ad6b120e1051f9841d172778cc24adc0023fb8dccf0a7cd",
        "license": "CC-BY-3.0", "revision": OMW_REV,
    },
    "wordnet.zip": {
        "url": f"https://raw.githubusercontent.com/nltk/nltk_data/{NLTK_REV}/packages/corpora/wordnet.zip",
        "sha256": "cbda5ea6eef7f36a97a43d4a75f85e07fccbb4f23657d27b4ccbc93e2646ab59",
        "license": "WordNet-3.0", "revision": NLTK_REV,
    },
    "muse-es-en.txt": {
        "url": "https://dl.fbaipublicfiles.com/arrival/dictionaries/es-en.txt",
        "sha256": "252dde7e162a90019cac70355a78563a94ea3dea93426aa75f7a87958d9b809f",
        "license": "CC-BY-NC-4.0", "snapshot_date": "2026-11-06",
    },
    "muse-en-es.txt": {
        "url": "https://dl.fbaipublicfiles.com/arrival/dictionaries/en-es.txt",
        "sha256": "aeea7d10f03e32e5cf2959eb0602055143176cffeed1949eb7c6e59dc0f34b1d",
        "license": "CC-BY-NC-4.0", "snapshot_date": "2026-11-06",
    },
}
POS = {"NCM": "n", "NCF": "n", "NCC": "n", "AQ0": "a", "VM": "v",
       "VA": "v", "VS": "v", "RG": "r", "RN": "r"}
POS_NAMES = {"n": "noun", "v": "verb", "a": "adjective", "r": "adverb"}
FUNCTION_POS = {"SP": "preposition", "CS": "conjunction", "CC": "conjunction",
                "PP0": "pronoun", "PI0": "pronoun", "PD0": "pronoun", "PR0": "pronoun",
                "PT0": "pronoun", "DA": "determiner", "DI": "determiner", "DD": "determiner",
                "DP": "determiner", "I": "interjection"}
POS_NAMES.update({name: name for name in FUNCTION_POS.values()})
# Explicitly checked common-function mappings. The translations below must also
# occur in the pinned bilingual source; these are selection filters, not glosses.
CORE_PAIRS = {("poder", "v"): ("puede", "can"), ("ir", "v"): ("ir", "go"),
              ("deber", "v"): ("debe", "must"), ("muy", "r"): ("muy", "very"),
              ("pretender", "v"): ("pretender", "intend"),
              ("sensible", "a"): ("sensible", "sensitive"),
              ("simpático", "a"): ("simpático", "nice"), ("largo", "a"): ("largo", "long")}
REVIEW_REFERENCES = {
    "pretender": "https://dictionary.cambridge.org/dictionary/spanish-english/pretender",
    "sensible": "https://dictionary.cambridge.org/es/diccionario/espanol-ingles/sensible",
    "simpático": "https://dictionary.cambridge.org/dictionary/spanish-english/simpatico",
}
FUNCTION_ENGLISH = {
    "determiner": set("the a an one each every this that these those all some any no another other several both much many few enough more most less least my your his her its our their whose which what".split()),
    "pronoun": set("i you he she it we they me him her us them myself yourself himself herself itself ourselves yourselves themselves who whom whose which what whoever whatever someone anyone everyone nobody anybody somebody everybody something anything everything nothing one none all both each another others".split()),
    "preposition": set("to for by with without between among of from in on at about over under above below across through before after during since until toward towards against beside beyond despite except via within outside inside like near around behind versus per into onto along beneath including".split()),
    "conjunction": set("and or but if because although though when while as than unless since until whether yet nor so once".split()),
    "interjection": set("hello hi thanks thank goodbye bye yes no please sorry okay ok welcome cheers wow ah oh alas bravo".split()),
}
MIN_DOCUMENTS = 3
MIN_FREQUENCY = Decimal("5")
MIN_SHARE = Decimal("0.10")


def normalized(text):
    return unicodedata.normalize("NFC", text.replace("_", " ").strip()).casefold()


def verify(raw, source):
    if hashlib.sha256(raw).hexdigest() != source["sha256"]:
        raise ValueError(f"Source checksum mismatch: {source['url']}")
    return raw


def read_sources(directory=None, download_to=None, snapshots=None):
    result = {}
    for name, source in SOURCES.items():
        if directory:
            raw = (directory / name).read_bytes()
        elif name in ("ELELex.tsv", "muse-es-en.txt", "muse-en-es.txt"):
            # These upstream URLs are not versioned: use the pack's pinned snapshots.
            if snapshots is None:
                candidate = Path(__file__).resolve().parent.parent / "packs/spanish/data/spanish"
                if candidate.exists():
                    snapshots = candidate
                else:
                    from screensaver.savers.word_drift.levels import directory_for
                    snapshots = directory_for("Spanish")
            snapshot = {"ELELex.tsv": "elelex-source.tsv.gz", "muse-es-en.txt": "muse-source.txt.gz",
                        "muse-en-es.txt": "muse-reverse-source.txt.gz"}[name]
            raw = gzip.decompress((snapshots / snapshot).read_bytes())
        else:
            with urllib.request.urlopen(source["url"], timeout=60) as response:
                raw = response.read()
        result[name] = verify(raw, source)
        if download_to:
            download_to.mkdir(parents=True, exist_ok=True)
            (download_to / name).write_bytes(raw)
    return result


def read_wordnet(raw):
    """Read Princeton 3.0 synsets and tagged English sense frequencies."""
    synsets = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for suffix in ("noun", "verb", "adj", "adv"):
            for line in archive.read(f"wordnet/data.{suffix}").decode().splitlines():
                if not line or line[0].isspace():
                    continue
                data, definition = line.split("|", 1)
                fields = data.split()
                pos = "a" if fields[2] == "s" else fields[2]
                key = f"{fields[0]}-{pos}"
                words = [re.sub(r"\((?:a|p|ip)\)$", "", fields[4 + i * 2]).replace("_", " ")
                         for i in range(int(fields[3], 16))]
                synsets[key] = {"words": words, "definition": definition.strip(), "tag_count": 0}
        for line in archive.read("wordnet/index.sense").decode().splitlines():
            sense, offset, _number, count = line.split()
            pos = {"1": "n", "2": "v", "3": "a", "4": "r", "5": "a"}[sense.split("%", 1)[1][0]]
            key = f"{offset}-{pos}"
            if key in synsets:
                synsets[key]["tag_count"] += int(count)
    return synsets


def read_spanish(raw):
    entries = collections.defaultdict(set)
    examples = collections.defaultdict(list)
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if fields[1] == "spa:lemma":
            entries[(normalized(fields[2]), fields[0][-1])].add(fields[0])
        elif fields[1] == "spa:exe":
            examples[fields[0]].append(fields[-1].strip())
    return entries, examples


def read_english_exceptions(raw):
    exceptions = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for suffix, pos in (("noun", "n"), ("verb", "v"), ("adj", "a"), ("adv", "r")):
            for line in archive.read(f"wordnet/{suffix}.exc").decode().splitlines():
                word, *lemmas = line.split()
                exceptions[(word, pos)] = lemmas
    return exceptions


def english_forms(word, pos, exceptions):
    """Propose base forms; a same-POS Spanish/English synset must confirm them."""
    word = word.casefold()
    forms = {word, *exceptions.get((word, pos), ())}
    rules = {"n": (("s", ""), ("ses", "s"), ("xes", "x"), ("zes", "z"),
                   ("ches", "ch"), ("shes", "sh"), ("ies", "y")),
             "v": (("s", ""), ("es", ""), ("ies", "y"), ("ed", ""),
                   ("ed", "e"), ("ing", ""), ("ing", "e")),
             "a": (("er", ""), ("est", ""), ("er", "e"), ("est", "e"))}
    for ending, replacement in rules.get(pos, ()):
        if word.endswith(ending) and len(word) > len(ending) + 1:
            base = word[:-len(ending)] + replacement
            forms.add(base)
            if pos == "v" and not replacement and len(base) > 2 and base[-1] == base[-2]:
                forms.add(base[:-1])
    return forms


def band(row):
    """Earliest band with repeated, substantial corpus evidence, never a lone hit.

    ELELex has normalized per-level frequencies, not certified lemma-level CEFR
    labels. Keep this derived threshold and all source observations auditable.
    """
    frequencies = [Decimal(row[f"level_freq@{level.lower()}"]) for level in LEVELS[:5]]
    total = sum(frequencies)
    if not total:
        return None
    for level, frequency in zip(LEVELS, frequencies):
        documents = Decimal(row[f"nb_doc@{level.lower()}"])
        if documents >= MIN_DOCUMENTS and frequency >= MIN_FREQUENCY and frequency / total >= MIN_SHARE:
            return level
    return None


def read_bilingual(raw, reverse=b""):
    pairs = collections.defaultdict(list)
    for line in raw.decode("utf-8").splitlines():
        cells = line.split()
        if len(cells) == 2:
            lemma, translation = cells
            if translation not in pairs[normalized(lemma)]:
                pairs[normalized(lemma)].append(translation)
    for line in reverse.decode("utf-8").splitlines():
        cells = line.split()
        if len(cells) == 2:
            translation, lemma = cells
            if translation not in pairs[normalized(lemma)]:
                pairs[normalized(lemma)].append(translation)
    return pairs


def dictionary_meaning(lemma, pos, spanish, english, examples, bilingual, exceptions=None):
    """Require bilingual corroboration or one unambiguous dictionary synset."""
    if (lemma, pos) in CORE_PAIRS:
        surface, translation = CORE_PAIRS[(lemma, pos)]
        evidence = [key for key in spanish.get((lemma, pos), ()) if key in english
                    and translation in english[key]["words"]]
        bilingual_match = translation in bilingual.get(surface, ())
        if not bilingual_match and not evidence:
            return None
        gloss = translation if translation in ("can", "must") else f"to {translation}" if pos == "v" else translation
        return {"english": gloss, "synsets": sorted(evidence), "example": "",
                "bilingual": {"surface": surface, "translations": [translation] if bilingual_match else []},
                "review_reference": REVIEW_REFERENCES.get(lemma, ""),
                "meaning_method": "Reviewed core mapping · attested dictionary/bilingual pair"}
    if pos in FUNCTION_POS.values():
        words = [word for word in bilingual.get(lemma, ())
                 if word.casefold() in FUNCTION_ENGLISH[pos]][:3]
        if not words:
            return None
        return {"english": "; ".join(words), "synsets": [], "example": "",
                "bilingual": {"surface": lemma, "translations": words},
                "meaning_method": "Published bilingual pair · function-word POS filter"}
    candidates = sorted((key for key in spanish.get((lemma, pos), ()) if key in english),
                        key=lambda key: (-english[key]["tag_count"], key))
    translations = bilingual.get(lemma, ())
    aligned = [(word, key) for surface in translations for key in candidates for word in english[key]["words"]
               if word.casefold() in english_forms(surface, pos, exceptions or {})]
    if aligned:
        candidates = list(dict.fromkeys(key for _word, key in aligned))
    elif translations or len(candidates) != 1:
        return None
    chosen, glosses = [], []
    for key in candidates:
        words = english[key]["words"]
        # Preserve the dictionary's preferred English lemma, including accents.
        aligned_word = next((word for word, candidate in aligned if candidate == key), "")
        word = next((word for word in words if word.casefold() == aligned_word.casefold()), words[0] if words else "")
        if not word or not re.fullmatch(r"[A-Za-zÀ-ž][A-Za-zÀ-ž '’.-]*", word):
            continue
        gloss = f"to {word}" if pos == "v" else word
        if gloss.casefold() in {item.casefold() for item in glosses}:
            continue
        chosen.append(key)
        glosses.append(gloss)
        if len(chosen) == 3:
            break
    if not chosen:
        return None
    # A shared synset's example may use a synonym: retain only literal matches.
    pattern = re.compile(r"(?<!\w)" + re.escape(lemma) + r"(?!\w)", re.IGNORECASE)
    example = next((text for key in chosen for text in examples.get(key, ())
                    if pattern.search(text) and len(text) <= 180), "")
    return {"english": "; ".join(glosses), "synsets": chosen, "example": example,
            "bilingual": {"surface": lemma, "translations": list(translations)},
            "meaning_method": "MCR + bilingual agreement" if aligned else "Unambiguous MCR synset · no bilingual entry"}


def build(elelex, mcr, wordnet, muse, muse_reverse=b"", advanced=None, legacy=LEGACY):
    spanish, examples = read_spanish(mcr)
    english = read_wordnet(wordnet)
    exceptions = read_english_exceptions(wordnet)
    bilingual = read_bilingual(muse, muse_reverse)
    advanced = {"C1": C1, "C2": C2} if advanced is None else advanced
    # These spellings preserve already-saved keys; they never provide meanings or levels.
    spellings = {}
    for _old_level, display, old_pos in legacy:
        lemma = re.sub(r"^(?:el|la|los|las) ", "", display) if old_pos == "noun" else display
        spellings[(normalized(lemma), old_pos)] = display
    candidates = collections.defaultdict(list)
    rejected = collections.Counter()
    for row in csv.DictReader(io.StringIO(elelex.decode("utf-8-sig")), delimiter="\t"):
        lemma = normalized(row["word"])
        pos = POS.get(row["tag"]) or FUNCTION_POS.get(row["tag"])
        if not pos:
            rejected["unsupported_or_ambiguous_pos"] += 1
            continue
        if not re.fullmatch(r"[a-záéíóúüñ]{2,}(?:[ -][a-záéíóúüñ]+)*", lemma) and lemma not in ("a", "y", "o", "e", "u"):
            rejected["non_headword"] += 1
            continue
        level = band(row)
        if not level:
            rejected["insufficient_level_evidence"] += 1
            continue
        if level == "C1" and lemma not in advanced.get("C1", ()):
            # Corpus sparsity alone can put everyday words in C1. As with Russian,
            # advanced selections also require explicit editorial inclusion.
            rejected["c1_not_in_advanced_selection"] += 1
            continue
        meaning = dictionary_meaning(lemma, pos, spanish, english, examples, bilingual, exceptions)
        if not meaning:
            rejected["no_same_pos_dictionary_meaning"] += 1
            continue
        candidates[lemma].append({"lemma": lemma, "pos": pos, "level": level, **meaning,
                                  "corpus": dict(row), "level_source": "ELELex · derived corpus band"})
    selected = []
    claimed = set()
    for lemma, choices in candidates.items():
        # One first-column key per lemma. The dominant attested POS takes precedence
        # over mistagged/rare alternative analyses; don't invent separate schedules.
        entry = min(choices, key=lambda item: (-Decimal(item["corpus"]["total_freq@total"]),
                                             LEVELS.index(item["level"]), item["pos"]))
        selected.append(entry)
        claimed.add(lemma)
        rejected["duplicate_or_alternative_pos"] += len(choices) - 1
    for level, headwords in advanced.items():
        for raw in dict.fromkeys(headwords):
            lemma = normalized(raw)
            if lemma in claimed:
                rejected["advanced_already_in_lower_pack"] += 1
                continue
            choices = [(pos, dictionary_meaning(lemma, pos, spanish, english, examples, bilingual, exceptions)) for pos in ("n", "v", "a", "r")]
            choices = [(pos, meaning) for pos, meaning in choices if meaning]
            if len(choices) != 1:
                rejected["advanced_missing_or_ambiguous_pos"] += 1
                continue
            pos, meaning = choices[0]
            selected.append({"lemma": lemma, "pos": pos, "level": level, **meaning,
                             "level_source": "Curated advanced selection · approximate"})
            claimed.add(lemma)
    packs = {level: [] for level in LEVELS}
    for entry in sorted(selected, key=lambda item: (
            LEVELS.index(item["level"]),
            -Decimal(item.get("corpus", {}).get("total_freq@total", "0")), item["lemma"])):
        entry["spanish"] = spellings.get((entry["lemma"], POS_NAMES[entry["pos"]]), entry["lemma"])
        entry["key"] = f"spanish:{normalized(entry['spanish'])}"
        packs[entry["level"]].append(entry)
    starter = []
    for old_level, display, old_pos in legacy:
        if old_level != "A1":
            continue
        lemma = normalized(re.sub(r"^(?:el|la|los|las) ", "", display) if old_pos == "noun" else display)
        pos = next(code for code, name in POS_NAMES.items() if name == old_pos)
        meaning = dictionary_meaning(lemma, pos, spanish, english, examples, bilingual, exceptions)
        if not meaning:
            raise ValueError(f"Original starter has no verified meaning: {display}")
        starter.append({"spanish": display, "lemma": lemma, "pos": pos, "level": "starter",
                        "key": f"spanish:{normalized(display)}", **meaning,
                        "level_source": "Original starter selection · dictionary-verified; no CEFR claim"})
    return packs, starter, dict(rejected), english


def encoded_pack(entries):
    file = io.StringIO(newline="")
    writer = csv.writer(file, delimiter="\t", lineterminator="\n")
    writer.writerow(("Spanish", "English", "POS", "Example"))
    for entry in entries:
        writer.writerow((entry["spanish"], entry["english"], POS_NAMES[entry["pos"]], entry["example"]))
    return file.getvalue().encode("utf-8")


def compressed_json(data):
    return gzip.compress(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(), mtime=0)


def write_output(packs, starter, rejected, english, output):
    output.mkdir(parents=True, exist_ok=True)
    provenance = {}
    manifest = {"version": 1, "language": "Spanish", "license": "CC-BY-NC-SA-4.0",
                "sources": SOURCES, "rejected": rejected, "packs": {},
                "method": {"minimum_documents": MIN_DOCUMENTS, "minimum_frequency_per_million": str(MIN_FREQUENCY),
                           "minimum_normalized_frequency_share": str(MIN_SHARE),
                           "bands": "Earliest qualifying ELELex band; dominant POS; all derived levels approximate",
                           "advanced": "Dictionary-backed curated C1/C2 selections; approximate, not certified CEFR"},
                "selection_sha256": hashlib.sha256(Path(__file__).with_name("spanish_advanced_headwords.py").read_bytes()).hexdigest(),
                "importer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "legacy_spellings_sha256": hashlib.sha256(Path(__file__).with_name("spanish_legacy_headwords.py").read_bytes()).hexdigest()}
    for level, entries in packs.items():
        raw = encoded_pack(entries)
        (output / f"{level.lower()}.tsv").write_bytes(raw)
        manifest["packs"][level] = {"count": len(entries), "sha256": hashlib.sha256(raw).hexdigest(),
                                   "approximate": True, "pos": dict(collections.Counter(POS_NAMES[e["pos"]] for e in entries)),
                                   "sources": dict(collections.Counter(e["level_source"] for e in entries)),
                                   "examples": sum(bool(e["example"]) for e in entries)}
        for entry in entries:
            provenance[entry["key"]] = {**entry, "dictionary": {
                key: english[key] for key in entry["synsets"]}}
        print(level, len(entries), "words", manifest["packs"][level]["pos"])
    starter_raw = encoded_pack(starter)
    (output / "starter.tsv").write_bytes(starter_raw)
    manifest["starter"] = {"count": len(starter), "sha256": hashlib.sha256(starter_raw).hexdigest()}
    starter_provenance = {entry["key"]: {**entry, "dictionary": {key: english[key] for key in entry["synsets"]}}
                          for entry in starter}
    raw = compressed_json({"version": 1, "entries": provenance, "starter": starter_provenance})
    (output / "provenance.json.gz").write_bytes(raw)
    manifest["provenance_sha256"] = hashlib.sha256(raw).hexdigest()
    retained = set(provenance) | set(starter_provenance)
    manifest["legacy_keys_retained"] = [f"spanish:{normalized(word)}" for _, word, _ in LEGACY
                                        if f"spanish:{normalized(word)}" in retained]
    manifest["legacy_keys_not_in_any_selection"] = [f"spanish:{normalized(word)}" for _, word, _ in LEGACY
                                                   if f"spanish:{normalized(word)}" not in retained]
    manifest["legacy_keys_outside_current_packs"] = [f"spanish:{normalized(word)}" for _, word, _ in LEGACY
                                                   if f"spanish:{normalized(word)}" not in provenance]
    (output / "manifest.json.gz").write_bytes(compressed_json(manifest))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="directory of all five verified offline input files")
    parser.add_argument("--snapshots-dir", type=Path, help="pack data directory containing the pinned ELELex/MUSE .gz snapshots")
    parser.add_argument("--download-sources", type=Path, help="also save verified input files for offline rebuilds")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    sources = read_sources(args.source_dir, args.download_sources, args.snapshots_dir)
    packs, starter, rejected, english = build(sources["ELELex.tsv"], sources["mcr-spa.tab"], sources["wordnet.zip"],
                                              sources["muse-es-en.txt"], sources["muse-en-es.txt"])
    write_output(packs, starter, rejected, english, args.output)


if __name__ == "__main__":
    main()
