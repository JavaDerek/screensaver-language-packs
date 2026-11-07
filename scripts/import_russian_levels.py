#!/usr/bin/env python3
"""Build offline Russian study packs from attributed, pinned source data."""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import hashlib
import io
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from screensaver.savers.word_drift.russian import clean_forms, lookup_key, stress
from screensaver.savers.word_drift.vocab import has_cyrillic
from scripts.russian_advanced_headwords import ADVANCED

LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
OUTPUT = Path(__file__).resolve().parent.parent / "dist/russian"
SMART_REV = "c20223c008c278c9399d8442f52948fae9c82c1c"
OPEN_REV = "50e210c4803237779cb562bc1abcea529066031c"
SMART_HASHES = (
    "84fc670664b34b4ee682da2270b49a08174aebb18acfc78645147e790c84bcd4",
    "cf3068c98505f9dcbefaf18fd8419ee294e491325dc6fd22a5fb48b9a7c37183",
    "b0e5ecd4fe7e1f3cb31d95e1704b601fcb6fa3c679a0c9a9fc23b7876618fbcd",
    "5532cdbf5e92bdc5fae099d22318677aed7e940334988233dee1f15ec51db94c",
)
OPEN_HASHES = {
    "nouns": "c388f9e6dde51932832be8d7e9afdbe9f0acee72fcf70677f0fe25ea61293c84",
    "verbs": "8659de6799b949fb35f080b08088fb7d347ed300490954ebb380a31642646e1d",
    "adjectives": "89ab5d10dcd2f21f6b485de704aef372f32251468e3aa96f18b21e259f26b80a",
    "others": "9f22a16b17fc9a564298112168b667fced11aafb254ccebf5b7544fc37cdaa92",
}
SNAPSHOT_HASH = "180e993bddb79d1c7697a455c9d13a013a1047512c8effde8cde5d21927a9d80"
STOP_WORDS = {"a", "an", "the", "to", "of", "in", "be", "and", "or", "for", "with", "one", "s", "someone"}


def tokens(text):
    return set(re.findall(r"[a-z]+", text.casefold())) - STOP_WORDS


def read_source(url, digest, local=None):
    raw = local.read_bytes() if local else urllib.request.urlopen(url, timeout=60).read()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"Source checksum mismatch: {url}")
    return raw


def rows(raw):
    return csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter="\t")


def canonical(raw, gloss, pos, accents):
    """Resolve stress from the dictionary, declining to guess ambiguous matches."""
    candidates = accents.get(lookup_key(raw), [])
    same_pos = [item for item in candidates if item[2] == pos]
    if same_pos:
        candidates = same_pos
    marked = clean_forms(raw)
    if len(marked) == 1 and stress(marked[0]):
        given = marked[0]
        # An explicit stress mark/ё is authoritative. Unmarked monosyllables
        # also have a uniquely recoverable stress position.
        if "\u0301" in raw or "ё" in raw or not candidates:
            return given
    unique = sorted({word for word, _, _ in candidates if stress(word)})
    if len(unique) == 1:
        return unique[0]
    scores = {word: max((len(tokens(gloss) & tokens(meaning)) for candidate, meaning, _ in candidates
                         if candidate == word), default=0) for word in unique}
    best = max(scores.values(), default=0)
    winners = [word for word, score in scores.items() if score == best]
    return winners[0] if best and len(winners) == 1 else None


def build(smart_sources, accent_sources, snapshot):
    accents = collections.defaultdict(list)
    for kind, raw in accent_sources.items():
        pos = {"nouns": "noun", "verbs": "verb", "adjectives": "adjective", "others": "other"}[kind]
        for row in rows(raw):
            words = clean_forms(row["accented"] or row["bare"])
            if len(words) == 1:
                accents[lookup_key(words[0])].append((words[0], row["translations_en"], pos))
    packs = {level: [] for level in LEVELS}
    claimed = set()
    rejected = collections.Counter()

    def add(level, raw, english, pos, source, example=""):
        raw = unicodedata.normalize("NFC", raw.strip())
        english = re.sub(r"\s+", " ", english).strip()
        key = lookup_key(raw)
        if key in claimed:
            return
        if not english or has_cyrillic(english):
            rejected["missing_or_mixed_language_gloss"] += 1
            return
        # These are headword packs, not mixed lists of inflected examples.
        if not re.fullmatch(r"[А-Яа-яЁё\u0301-]+", raw):
            rejected["non_headword"] += 1
            return
        word = canonical(raw, english, pos, accents)
        if word is None:
            rejected["unresolved_stress"] += 1
            return
        claimed.add(key)
        packs[level].append({"russian": word, "english": english, "example": example.strip(),
                             "pos": pos, "source": source})

    # Teacher-selected levels take precedence over the broader dictionary bands.
    for level in LEVELS[:4]:
        seen = set()
        reader = csv.DictReader(io.StringIO(smart_sources[level].decode("utf-8-sig")))
        for row in reader:
            raw = row["Target language lemma"].strip()
            if not raw or raw in seen:
                continue
            seen.add(raw)
            pos = "noun" if row["POS"].startswith("N") else {"V": "verb", "A": "adjective"}.get(row["POS"], "other")
            add(level, raw, row["User language gloss"], pos, "SMARTool",
                row.get("Target language example sentence", ""))
    # Supplement missing parts of speech in the lower packs. The source's C
    # bands include everyday vocabulary, so they are not adopted wholesale.
    for level in LEVELS[:4]:
        for row in snapshot["levels"][level]:
            raw = row["accented"] or row["bare"]
            translations = row.get("majorTranslations") or row.get("translations", [])
            add(level, raw.replace("'", "\u0301"), "; ".join(translations[:2]), row["pos"] or "other", "OpenRussian")
    for level, headwords in ADVANCED.items():
        for headword in headwords:
            candidates = accents.get(lookup_key(headword), [])
            if not candidates:
                rejected["advanced_not_in_dictionary"] += 1
                continue
            word, gloss, pos = candidates[0]
            # The dictionary, not the hand-written selection, supplies stress.
            add(level, word, gloss, pos, "OpenRussian · curated selection")
    return packs, dict(rejected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="reuse downloaded pinned CSVs")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--snapshot", type=Path, help="pinned openrussian-source.json.gz from the Russian pack")
    args = parser.parse_args()
    smart, accented, provenance = {}, {}, []
    for level, digest in zip(LEVELS[:4], SMART_HASHES):
        name = f"SMARTool_data_{level}.csv"
        url = f"https://raw.githubusercontent.com/smartool/data-rus-eng/{SMART_REV}/{name}"
        smart[level] = read_source(url, digest, args.source_dir / name if args.source_dir else None)
        provenance.append({"url": url, "sha256": digest})
    for kind, digest in OPEN_HASHES.items():
        url = f"https://raw.githubusercontent.com/Badestrand/russian-dictionary/{OPEN_REV}/{kind}.csv"
        accented[kind] = read_source(url, digest, args.source_dir / f"openrussian-{kind}.csv" if args.source_dir else None)
        provenance.append({"url": url, "sha256": digest})
    snapshot_path = args.snapshot or args.output / "openrussian-source.json.gz"
    if not snapshot_path.exists() and not args.snapshot:
        from screensaver.savers.word_drift.levels import directory_for
        snapshot_path = directory_for("Russian") / "openrussian-source.json.gz"
    raw = read_source(str(snapshot_path), SNAPSHOT_HASH, snapshot_path)
    snapshot = json.loads(gzip.decompress(raw))
    packs, rejected = build(smart, accented, snapshot)
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {"version": 1, "sources": provenance, "snapshot_sha256": SNAPSHOT_HASH,
                "snapshot_date": snapshot["date"], "rejected": rejected, "packs": {}}
    for level, entries in packs.items():
        target = args.output / f"{level.lower()}.tsv"
        file = io.StringIO(newline="")
        writer = csv.writer(file, delimiter="\t", lineterminator="\n")
        writer.writerow(("Russian", "English", "POS", "Example"))
        for entry in entries:
            row = [entry["russian"], entry["english"], entry["pos"]]
            if entry["example"]:
                row.append(entry["example"])
            writer.writerow(row)
        encoded = file.getvalue().encode("utf-8")
        target.write_bytes(encoded)
        manifest["packs"][level] = {"count": len(entries), "sha256": hashlib.sha256(encoded).hexdigest(),
                                    "pos": dict(collections.Counter(e["pos"] for e in entries)),
                                    "sources": dict(collections.Counter(e["source"] for e in entries)),
                                    "approximate": level.startswith("C")}
        print(level, manifest["packs"][level])
    (args.output / "manifest.json.gz").write_bytes(gzip.compress(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode(), mtime=0))
    print("Skipped:", rejected)


if __name__ == "__main__":
    main()
