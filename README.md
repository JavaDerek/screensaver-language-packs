# Word Drift language packs

Optional language data for [Screensaver / Word Drift](https://github.com/JavaDerek/screensaver).
The application downloads only the packs a user chooses in **Settings → Language
packs**. Installed packs work offline. Personal vocabulary and learning progress
are stored separately and survive removing, updating or reinstalling packs.

| Language | Contents | Data license |
| --- | --- | --- |
| [Russian](packs/russian/README.md) | A1–C2 lists, original starter, and about 27,000 recorded noun paradigms | CC BY-SA 4.0; source notices included |
| [Spanish](packs/spanish/README.md) | 4,013 source-backed headwords in approximate A1–C2 study bands, plus original starter | CC BY-NC-SA 4.0, including noncommercial terms; source notices included |

Russian A1–B2 use teacher-selected SMARTool vocabulary with OpenRussian additions.
Spanish bands use ELELex graded-textbook evidence with dictionary-checked meanings.
C1/C2 selections are provisional for both languages. These are vocabulary packs,
not complete courses or exam syllabuses. Preserve all separate licenses and source
credits; the application/script MIT license does not relicense the data.

## Downloads and community packs

[Releases](https://github.com/JavaDerek/screensaver-language-packs/releases) provide
versioned `.wordpack` ZIP assets. `catalog.json` supplies download URLs, archive
sizes and SHA-256 hashes for Settings. The application ships a small catalog
snapshot; checking for new catalog versions and downloading data are explicit
user actions. No downloads occur during screensaver playback.

The public [format v1 specification](FORMAT.md) describes the manifest, TSV columns,
stable progress keys, integrity checks, licenses and optional grammar data.
Community authors can host their own GitHub Release assets and share the direct
HTTPS link, usable through **Download from URL**, or distribute an archive for
**Import pack**. To propose inclusion in this catalog, open a pull request with
source attribution, full redistribution licenses, rebuild instructions and
honest level/quality limitations. Packs contain data and cannot execute code.

## Rebuild release archives and catalog

Use Python 3 and a sibling application checkout with language-pack support:

```sh
python3 scripts/build_catalog.py --app ../screensaver --tag packs-2026.11.07
```

This builds deterministic `.wordpack` archives under `dist/`, validates the same
constraints as the installer, and regenerates `catalog.json`. `--app` locates the
application's standard-library pack builder; no GTK/display is needed. Copy the
catalog snapshot into the app when releasing new default catalog metadata.

Full data validation from the application checkout:

```sh
WORD_DRIFT_TEST_PACKS="/path/to/screensaver-language-packs/dist" \
  python3 -m unittest discover -s tests -t .
```

The application normally runs offline using small licensed regression samples;
this command additionally checks every Spanish provenance entry, source snapshot,
output checksum and importer/selection checksum against the full release data.

## Rebuild vocabulary from original sources

Original source snapshots and full attribution remain inside each pack's data
tree, rather than the application distribution. Import/selection scripts are
preserved under `scripts/`. See [Russian noun sources](packs/russian/data/README.md),
[Russian levels](packs/russian/data/levels/README.md), and
[Spanish sources](packs/spanish/data/spanish/README.md) for limitations and pinned
inputs. When running importers here, make the application importable and choose
an explicit output in this source tree, for example:

```sh
PYTHONPATH=../screensaver python3 scripts/import_russian_nouns.py \
  --output packs/russian/data/russian-nouns.json.gz
PYTHONPATH=../screensaver python3 scripts/import_russian_levels.py \
  --output packs/russian/data/levels
PYTHONPATH=../screensaver python3 scripts/import_spanish_levels.py \
  --output packs/spanish/data/spanish
```

Importers verify pinned upstream inputs; the Spanish importer can retain verified
downloads for offline rebuilds as documented in its source README. Default importer
output is `dist/`, preventing accidental rebundling into the application. Ordinary
pack downloads need no source rebuild or upstream connection.

Bump the pack version when changing any distributed file. Build and validate before
creating a GitHub release. Upload immutable versioned assets without replacing an
existing release's files; publish the catalog only for artifacts that are being
released. The catalog hash covers the entire compressed archive, while each pack
manifest inventories every payload file and its exact size/hash.
