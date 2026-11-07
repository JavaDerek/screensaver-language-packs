# Bundled Russian vocabulary packs

These are offline vocabulary study packs, not complete TORFL exam syllabuses or
a certification of CEFR proficiency. A1–B2 have a teacher-selected foundation;
C1 and C2 are deliberately smaller **advanced starter selections with approximate
level assignments**, not validated CEFR word inventories.

| Pack | Words in this pack | Including earlier levels |
| --- | ---: | ---: |
| A1 | 534 | 534 |
| A2 | 579 | 1,113 |
| B1 | 944 | 2,057 |
| B2 | 2,055 | 4,112 |
| C1 starter (approximate) | 110 | 4,222 |
| C2 starter (approximate) | 147 | 4,369 |

Headwords appear only once across these packs. The same stressed first-column
spelling is used in individual and cumulative selections, preserving identical
progress keys. Matching entries in custom files also retain their progress;
existing custom files are never rewritten or replaced. Different stress or
spelling in a custom file may identify a different entry, as before.
The `POS` column retains the source's part of speech as metadata. Nouns get the
word-only main display even if the declension dictionary has no matching forms.

## Sources and licenses

**SMARTool data for English-speaking learners of Russian** supplies the A1–B2
foundation, English glosses and Russian examples. The dataset is published under
[CC BY 4.0](CC-BY-4.0), with its disclaimer of warranties. Authors: Radovan Bast,
Laura A. Janda, Mikhail Kopotev, Olga Lyashevskaya, James D. McDonald, Tore Nesset,
Ekaterina Rakhilina, Svetlana Sokolova, Evgeniia Sudarikova, Francis M. Tyers,
Valentina Zhukova and Elizaveta Kibisova.

- Dataset DOI: <https://doi.org/10.18710/QNAPNE>
- Methodology and data: <https://github.com/smartool/data-rus-eng>
- Pinned revision: `c20223c008c278c9399d8442f52948fae9c82c1c`
- Input files: `SMARTool_data_A1.csv`, `SMARTool_data_A2.csv`,
  `SMARTool_data_B1.csv`, `SMARTool_data_B2.csv`.

**OpenRussian**, by Michel Helms, the OpenRussian team and contributors, supplies
stress, additional parts of speech, and dictionary glosses for the advanced
starters. It combines Wiktionary, Starling and contributor corrections. The data
and our adaptations are under **CC BY-SA 4.0**, with the full terms and warranty
disclaimer in [the accompanying license](../CC-BY-SA-4.0).

- Data access and original sources: <https://en.openrussian.org/dictionary-data>
- Dictionary export: <https://github.com/Badestrand/russian-dictionary>
- Pinned revision for `nouns.csv`, `verbs.csv`, `adjectives.csv`, `others.csv`:
  `50e210c4803237779cb562bc1abcea529066031c`
- `openrussian-source.json.gz` preserves a public word-list snapshot retrieved
  on 2026-11-04 from `https://en.openrussian.org/_api2/api/wordlists/all`, with
  the `level`, `start` and `lang=en` parameters. It contains all six source
  bands for provenance; only A1–B2 are used directly in the resulting packs.

The **combined/adapted TSV packs are licensed CC BY-SA 4.0**, separately from the
application's MIT license. Keep these credits and license notices when sharing
them. The source manifest records input URLs, checksums, counts, parts of speech,
and source contributions.

## Processing and limitations

- Extract dictionary headwords from SMARTool's repeated example rows; retain
  the teacher-assigned level and a source example. These level assignments take
  precedence over OpenRussian's lower-level supplements.
- Resolve stress from explicit source data. When alternative stress patterns
  exist, require a unique English-gloss match; omit unresolved cases rather than
  guess. Normalize Unicode and preserve ё.
- Reject missing or mixed Russian/English glosses and entries that are not
  single headwords. Keep only the first occurrence of each headword across levels.
- Add lower-level OpenRussian words absent from SMARTool, including pronouns,
  adverbs, prepositions and numerals.
- OpenRussian's unmodified C1/C2 bands include everyday words, so those bands
  are not bundled as authoritative advanced vocabulary. Instead,
  `scripts/russian_advanced_headwords.py` selects formal, abstract and literary
  vocabulary. Its C1/C2 difficulty assignments are provisional and have not
  received an independent teacher or exam-board review. Dictionary stress and
  English glosses are still required, and words already present below are omitted.
- Source dictionaries can contain mistakes; these packs are not exhaustive.
  Counts and skipped-entry statistics are in `manifest.json.gz`.

## Rebuild

From the repository root:

```sh
python3 scripts/import_russian_levels.py
```

The script downloads the pinned SMARTool and OpenRussian CSVs and verifies their
checksums. It uses the bundled snapshot without querying the live API. For an
offline rebuild, supply `--source-dir /path/to/downloads`, containing the four
`SMARTool_data_*.csv` files and `openrussian-{nouns,verbs,adjectives,others}.csv`.
`--output /path/to/output` writes a separate set for comparison. Outputs are
deterministic for the same sources and selection code.

Normal app use requires no downloads, account, or extra Python dependencies.
