# Russian noun dictionary

`russian-nouns.json.gz` is an adapted, compressed snapshot of the OpenRussian
dictionary by Michel Helms (Badestrand), the OpenRussian team and contributors.
The upstream combines Wiktionary, Starling and user contributions. Thank you to
the contributors who made these data freely reusable.

- Website: <https://en.openrussian.org/dictionary-data>
- Source repository: <https://github.com/Badestrand/russian-dictionary>
- Source file: `nouns.csv` (a tab-separated file despite its name)
- Pinned revision: `50e210c4803237779cb562bc1abcea529066031c`
- Source SHA256: `c388f9e6dde51932832be8d7e9afdbe9f0acee72fcf70677f0fe25ea61293c84`
- License for these dictionary data and our adaptations: **Creative Commons
  Attribution-ShareAlike 4.0 International**, not the application's MIT license.
  The full terms, including the disclaimer of warranties, are in
  [CC-BY-SA-4.0](CC-BY-SA-4.0), also available at
  <https://creativecommons.org/licenses/by-sa/4.0/>.

The snapshot contains 26,936 noun entries and 281,165 populated case/number
cells. Entries can represent different senses or stress patterns of the same
spelling. It is a historical backup: upstream recommends its current TogetherDB
exports for newer data. This snapshot is deliberately pinned so installation and
runtime need no network access, account, or third-party Python dependency.
It is not a fully audited dictionary. 2,529 entries have no usable forms;
other entries can have partial paradigms, unmarked stress, or source errors.

## Adaptations

The importer keeps noun headwords, English glosses, gender, animacy, number
restrictions, indeclinability and the six main cases in both numbers. It converts
apostrophe stress notation to Unicode combining acutes and splits explicit
alternatives. Annotated/starred forms are rejected rather than having their
annotations silently stripped. Forty-six annotated/invalid headwords are omitted.
Explicitly indeclinable nouns reuse their headword, but missing forms of other
nouns are never generated. Alternative forms may differ in register or sense.

Two corrections are applied in `scripts/import_russian_nouns.py`, checked against
the current source on 2026-11-04:

- [год](https://en.openrussian.org/ru/год): restore the ordinary prepositional
  singular `го́де` and plural paradigm `го́ды`, `лет / годо́в`, `года́м`, `го́ды`,
  `года́ми`, `года́х`. The backup mixed in the separate locative and a different
  plural series. The special locative `в году́` is not labeled as a main case here.
- [ветер](https://en.openrussian.org/ru/ветер): restore the ordinary plural
  `ве́тры`, `ве́тров`, `ве́трам`, `ве́тры`, `ве́трами`, `ве́трах` and clear the
  singular-only flag. The separate locative is not folded into the prepositional.

The application derives attention cues at runtime. These annotations compare
forms to a deliberately limited model of common productive endings, and compare
stress with the headword. They are learning aids, not authoritative irregularity
labels. Unknown patterns are left unclassified. More complete source data or
future corrections can change which forms are highlighted.

## Rebuild

From the repository root:

```sh
python3 scripts/import_russian_nouns.py
# Or use an already downloaded copy of the exact pinned source:
python3 scripts/import_russian_nouns.py --source /path/to/nouns.csv
python3 -m screensaver noun-forms
python3 -m screensaver noun-forms челове́к
```

The importer verifies the source checksum before writing. Source revision,
checksum and license are also recorded inside the generated data. To update the
snapshot, review the new schema and data, update the pin/checksum and corrections,
rebuild, run the tests, and update this attribution and coverage information.
