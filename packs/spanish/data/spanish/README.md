# Bundled Spanish vocabulary packs

These offline packs replace the initial 160 generated entries with **4,013
source-backed headwords**, plus the original 40-word starter selection with
rebuilt, dictionary-checked meanings. Playback requires no downloads.

| Pack | Words | Including earlier levels |
| --- | ---: | ---: |
| A1 | 1,021 | 1,021 |
| A2 | 1,085 | 2,106 |
| B1 | 885 | 2,991 |
| B2 | 533 | 3,524 |
| C1 advanced starter (approximate) | 267 | 3,791 |
| C2 proficiency starter (approximate) | 222 | 4,013 |

**Every Spanish level assignment is approximate.** A1–B2 use published
frequencies from graded textbooks and readers. Unlike Russian's SMARTool
teacher-assigned foundation, these are derived study bands, not individual
teacher/exam-board CEFR judgments. C1/C2 are explicitly provisional, curated
advanced selections, as in the Russian packs. Neither language's packs are
complete courses or exam syllabuses.

## Sources and separate data licenses

The combined/adapted Spanish packs, snapshots and provenance are under
**[CC BY-NC-SA 4.0](CC-BY-NC-SA-4.0)**. This includes a **noncommercial
restriction**, unlike the Russian packs' CC BY-SA terms. Application code remains
MIT. Keep these credits, original notices and warranty disclaimers when sharing
the data. Sources retain their own terms below; inclusion implies no endorsement.

### ELELex — graded-textbook evidence and POS

[ELELex](https://cental.uclouvain.be/cefrlex/elelex/), from the **Centre de
traitement automatique du langage (CENTAL), UCLouvain**, records normalized word
frequencies and document counts in textbook reading activities and simplified
readers at A1–C1. The publisher reports 14,290 lexical items, with simplified
FreeLing POS labels. The download page requests citation of ELELex with a
reference article forthcoming; no unprovided author list or paper is invented.

- Publisher/methodology/terms: <https://cental.uclouvain.be/cefrlex/elelex/download/>.
- Input: <https://cental.uclouvain.be/cefrlex/static/resources/es/ELELex.tsv>.
- License: [CC BY-NC-SA 4.0](CC-BY-NC-SA-4.0).
- Retrieved **2026-11-06**, losslessly preserved in `elelex-source.tsv.gz`.
  Its raw SHA-256 is pinned. This URL is unversioned: rebuilds use the bundled
  snapshot, rather than silently accepting upstream changes.

### Spanish dictionary — Multilingual Central Repository 3.0

**MCR Spanish WordNet** supplies attested headwords, POS, concept/sense links and
occasional Spanish examples. Credit **Aitor Gonzalez-Agirre, Egoitz Laparra and
German Rigau**, *Multilingual Central Repository version 3.0: upgrading a very
large lexical knowledge base*, 6th Global WordNet Conference, 2012.

- Project: <https://adimen.si.ehu.es/web/MCR/>.
- Distribution: <https://github.com/omwn/omw-data/tree/main/wns/mcr>.
- Pinned revision: `406bf83b3c507a3d1f26e88252d5d66893fd36bf`.
- Input: `wns/mcr/wn-data-spa.tab`; checksum in importer/manifest.
- Spanish data: [CC BY 3.0](CC-BY-3.0); [original MCR notice](MCR-LICENSE).

Credit the **Open Multilingual Wordnet** distribution: **Francis Bond and Ryan
Foster**, *Linking and extending an open multilingual wordnet*, ACL 2013,
1352–1362, <https://aclanthology.org/P13-1132/>.

### English dictionary — Princeton WordNet 3.0

**Princeton University WordNet 3.0**, copyright **2006 Princeton University**,
supplies English lemmas, definitions, tagged English sense frequencies and
inflection exceptions. Shared synsets link these meanings to Spanish; English
CEFR labels are never translated into Spanish difficulty levels.

- Project: <https://wordnet.princeton.edu/>.
- Terms and warranty disclaimer: [WORDNET-LICENSE](WORDNET-LICENSE).
- Distribution: `packages/corpora/wordnet.zip` in <https://github.com/nltk/nltk_data>,
  pinned to `550b6625bcef1f2abff2ff770a5a0d272c9c6b2a`, with checksum verification.
- The importer uses the standard library; there is no NLTK runtime dependency.

### Bilingual cross-check — MUSE

**Facebook Research's MUSE** Spanish–English and English–Spanish dictionaries
provide corroborating lexical pairs and function-word meanings not well covered
by WordNet. Credit **Facebook, Inc.**, **Alexis Conneau, Guillaume Lample,
Marc'Aurelio Ranzato, Ludovic Denoyer and Hervé Jégou**, *Word Translation Without
Parallel Data*, 2017 / ICLR 2018: <https://arxiv.org/abs/1710.04087>.

- Project/methodology: <https://github.com/facebookresearch/MUSE#ground-truth-bilingual-dictionaries>.
- Inputs: <https://dl.fbaipublicfiles.com/arrival/dictionaries/es-en.txt> and
  <https://dl.fbaipublicfiles.com/arrival/dictionaries/en-es.txt>.
- License: [CC BY-NC 4.0](CC-BY-NC-4.0), also in the project's LICENSE.
- Retrieved **2026-11-06**, preserved losslessly in `muse-source.txt.gz` and
  `muse-reverse-source.txt.gz`, with pinned raw checksums.

MUSE describes these as ground-truth evaluation dictionaries produced with an
internal translation tool. They are **not claimed to be teacher-reviewed Spanish
curricula or independently perfect translations**. We require dictionary
agreement and omit unresolved conflicts instead of trusting every pair.

## Processing, evidence and limitations

`scripts/import_spanish_levels.py` deterministically:

1. Verifies all input hashes; normalizes Unicode to NFC while preserving accents
   and ñ; expands underscore separators; rejects proper names, malformed
   headwords and ambiguous/unsupported POS tags.
2. Selects the earliest A1–C1 band with **at least three documents**, **five
   normalized occurrences per million**, and **10% of the sum of the five
   normalized level frequencies**. This is our documented study heuristic, not
   ELELex's own word-level classification or CEFR certification. Incidental early
   appearances are insufficient. All observations are retained in provenance.
3. Requires same-POS Spanish/English WordNet matches and corroborating MUSE
   translations. Inflected English pairs can yield a base form only when a
   matching same-POS synset confirms it. Tagged English sense frequencies break
   ties; they never determine Spanish difficulty. With no MUSE entry, only a
   single unambiguous dictionary synset is accepted. Conflicts and unresolved
   polysemy are omitted.
4. Restricts function-word translations to the corresponding English grammatical
   category: determiner **este** can mean **this**, but not noun **east**. Reviewed
   core selections cover **poder → can**, **ir → to go**, **deber → must** and
   **muy → very**, each requiring attestation in the pinned lexical sources.
   Reviewed false-friend selections prefer **pretender → to intend**,
   **sensible → sensitive**, **simpático → nice** and **largo → long** over rare
   or misleading senses. Dictionary synsets must still attest each chosen word;
   the first three also record a Cambridge bilingual reference in provenance.
5. Chooses the dominant corpus POS when alternatives exist; deduplicates headwords
   across levels; retains up to three distinct corroborated meanings.
6. Restricts C1 to the explicit advanced selection so sparsely attested everyday
   words such as **mosca** and **redondo** do not become advanced vocabulary.
   Adds dictionary-backed candidates from `scripts/spanish_advanced_headwords.py`,
   omitting headwords already admitted below. C1/C2 editorial assignments have
   not received independent teacher review.
7. Retains a Spanish example only if it literally contains the headword; a shared
   concept's example may otherwise use a synonym. Missing examples are left empty,
   not generated or machine-translated.

TSVs contain `Spanish`, `English`, `POS` and `Example`. New nouns use source
lemmas without guessing articles or inflections. Earlier article-bearing
spellings are retained when their headword/POS survives, solely for stable
progress keys. Original corpus gender tags and other fields remain in provenance.

`provenance.json.gz` records every output's source lemma, POS, band observations,
meaning-selection method, bilingual evidence and selected synsets/English
definitions. It separately records all 40 original starter keys with newly
verified meanings; this starter makes no CEFR claim.
`manifest.json.gz` records input URLs/revisions/hashes, output hashes and counts,
POS totals, examples, rejection counts, processing/selection code hashes, and
legacy-key coverage. Keys omitted by stricter checks remain in saved progress;
no personal file, setting or progress record is rewritten.

Source dictionaries can contain errors, regional senses and coverage gaps.
WordNet concept links are not a complete learner dictionary. These safeguards
make results auditable and reject known bad matches; they do not substitute for
independent teacher review of every entry. Russian also retains documented
source limitations and provisional advanced selections.

## Rebuild and validate

From the repository root, using Python 3 and its standard library:

```sh
python3 scripts/import_spanish_levels.py
```

The build reads the bundled ELELex/MUSE snapshots and downloads two pinned
WordNet inputs. Preserve verified downloads for offline rebuilds:

```sh
python3 scripts/import_spanish_levels.py --download-sources /tmp/spanish-sources
python3 scripts/import_spanish_levels.py --source-dir /tmp/spanish-sources --output /tmp/spanish-rebuilt
```

The source directory contains `ELELex.tsv`, `mcr-spa.tab`, `wordnet.zip`,
`muse-es-en.txt` and `muse-en-es.txt`. Wrong inputs fail before any output is
written. `--output` writes generated TSVs, provenance and manifest in a separate
directory. Outputs are byte-identical for identical inputs/selection code,
including fixed-timestamp gzip files. Keep the documented source credits and
license notices with redistributed data.

The offline tests check snapshot hashes, every output's evidence, same-POS
meanings, known bad/advanced matches, duplicates, starter keys, corruption
rejection and deterministic fixture builds:

```sh
python3 -m unittest tests.test_languages tests.test_spanish_sources
```
