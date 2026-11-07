#!/usr/bin/env python3
"""Rebuild a Russian pack's offline dictionary from the pinned OpenRussian export."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from screensaver.savers.word_drift.russian import CASES, DICTIONARY, clean_forms

REVISION = "50e210c4803237779cb562bc1abcea529066031c"
SOURCE = f"https://raw.githubusercontent.com/Badestrand/russian-dictionary/{REVISION}/nouns.csv"
SOURCE_SHA256 = "c388f9e6dde51932832be8d7e9afdbe9f0acee72fcf70677f0fe25ea61293c84"

# Corrections checked against the current source, retained here so rebuilding
# does not silently restore errors in the historical backup. See data/README.md.
CORRECTIONS = {
    "год": {"sg_prep": "го'де", "pl_nom": "го'ды", "pl_gen": "лет, годо'в",
            "pl_dat": "года'м", "pl_acc": "го'ды", "pl_inst": "года'ми", "pl_prep": "года'х"},
    "ветер": {"sg_only": "0", "pl_nom": "ве'тры", "pl_gen": "ве'тров", "pl_dat": "ве'трам",
              "pl_acc": "ве'тры", "pl_inst": "ве'трами", "pl_prep": "ве'трах"},
}


def build(source: bytes) -> dict:
    nouns = []
    rejected = 0
    for row in csv.DictReader(io.StringIO(source.decode("utf-8-sig")), delimiter="\t"):
        row.update(CORRECTIONS.get(row["bare"], {}))
        lemmas = clean_forms(row["accented"] or row["bare"])
        if len(lemmas) != 1:
            rejected += 1
            continue
        forms = {}
        for number in ("sg", "pl"):
            if row["pl_only" if number == "sg" else "sg_only"] == "1":
                continue
            for case in CASES:
                key = f"{number}_{case}"
                # Indeclinability is explicitly supplied, not inferred from gaps.
                values = clean_forms(row[key])
                if row["indeclinable"] == "1" and not values:
                    values = lemmas
                if values:
                    forms[key] = values
        nouns.append({"lemma": lemmas[0], "meaning": row["translations_en"], "gender": row["gender"],
                      "animate": {"1": True, "0": False}.get(row["animate"]),
                      "indeclinable": row["indeclinable"] == "1", "singular_only": row["sg_only"] == "1",
                      "plural_only": row["pl_only"] == "1", "forms": forms})
    return {"version": 1, "source": SOURCE, "source_sha256": hashlib.sha256(source).hexdigest(),
            "license": "CC-BY-SA-4.0", "rejected_lemmas": rejected, "nouns": nouns}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="use a local copy of the pinned TSV export")
    parser.add_argument("--output", type=Path, default=DICTIONARY)
    args = parser.parse_args()
    source = args.source.read_bytes() if args.source else urllib.request.urlopen(SOURCE, timeout=60).read()
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        parser.error("source checksum does not match the pinned OpenRussian export")
    data = build(source)
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(encoded, mtime=0))
    print(f"Imported {len(data['nouns']):,} nouns; rejected {data['rejected_lemmas']} annotated lemmas. "
          f"{args.output.stat().st_size:,} bytes; source SHA256 {data['source_sha256']}")


if __name__ == "__main__":
    main()
