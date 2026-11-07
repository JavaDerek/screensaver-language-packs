# Word Drift language pack format, version 1

A language pack is a **data-only ZIP archive**, normally named `language-version.wordpack`.
Word Drift does not import or execute code from packs. A pack supplies study lists,
source attribution, full license notices and, optionally, Russian noun paradigms.
The application supplies animation, scheduling, recognition/production practice,
English-side filtering and the Russian case renderer.

The official catalog, sources and downloads are maintained separately from the app:
<https://github.com/JavaDerek/screensaver-language-packs>.

## Directory layout and manifest

The archive has `pack.json` **at its root**, without a wrapper directory. Paths use
forward slashes and are relative to this root. Example creator directory:

```text
french/
  pack.json
  vocabulary/a1.tsv
  LICENSE
  SOURCES.md
```

Creator metadata in `pack.json`:

```json
{
  "format": "word-drift-language-pack",
  "format_version": 1,
  "id": "french-community",
  "version": "1.0.0",
  "language": "French",
  "translation_language": "English",
  "description": "Beginner French words, with documented sources.",
  "license": "CC-BY-4.0",
  "license_files": ["LICENSE"],
  "attribution": "Author names and source credits; details in SOURCES.md.",
  "levels": {"A1": "vocabulary/a1.tsv"}
}
```

Use a stable ID: lowercase ASCII letters, digits and hyphens, beginning with a
letter, at most 64 characters. The display language name is independent of the ID.
One pack per study language can be installed at a time. An alternative pack for
that language requires removing the previous one; learning progress stays.
Versions are nonempty, printable strings up to 500 characters; the app offers an
update when the catalog version differs and never updates silently. Keep a pack's
ID and study-language identity stable when publishing updates.

Version 1 packs use English translations. Custom vocabulary files continue to
support other translation languages. A pack must supply at least one of `A1`,
`A2`, `B1`, `B2`, `C1`, `C2`, or `starter`; it need not supply all seven. Including
earlier levels combines whichever earlier levels that pack provides. Languages
mixed in a session must share the selected level. Label approximate or provisional
levels clearly; listing a CEFR band is not certification or independent review.

Include the complete terms of **every applicable data license**, source credits,
revisions, checksums and processing/rebuild instructions. The app's MIT license
does not relicense pack data. For example, the official Spanish data is
CC BY-NC-SA 4.0, including a noncommercial restriction. Installation is not a
license grant from the application author. Only redistribute data you may share.

## Vocabulary files and progress identity

UTF-8 TSV files use the study language in the **first column**, followed by
English. Optional metadata columns are `POS`, `Pronunciation` and `Example`.

```text
French\tEnglish\tPOS\tExample
bonjour\thello\tinterjection\tBonjour, comment allez-vous ?
```

Here `\t` means a literal tab. Every row needs both language values. Duplicate
first-column words, mismatched language headers and skipped/invalid rows reject
the pack. Files may use the app's existing CSV/semicolon parsing, but TSV is
recommended. Nouns, verbs and other POS tags use the existing vocabulary parser.
Examples may be omitted; do not invent unsupported examples or source claims.

Progress uses the normalized, case-folded first-column language/headword key,
**not the pack ID, version or translation**. Keep existing first-column spellings,
articles and stress marks when updating a pack if the same word should retain its
progress. Changing a gloss or adding an example preserves the key. Recognition
and production remain independent; both share the language's distinct-word quota.
Removing or updating packs never deletes personal lists, word schedules, pauses
or daily budgets. Reinstalling matching headwords resumes their saved progress.

## Building and checking a pack

From an application checkout (Python standard library only):

```sh
python3 scripts/language_pack.py build /path/to/french --output /tmp/french-1.0.0.wordpack
python3 scripts/language_pack.py validate /tmp/french-1.0.0.wordpack
```

The builder adds a mandatory `files` inventory to the archive's `pack.json`:

```json
"files": {
  "vocabulary/a1.tsv": {"size": 1234, "sha256": "64 lowercase hexadecimal characters"},
  "LICENSE": {"size": 567, "sha256": "64 lowercase hexadecimal characters"},
  "SOURCES.md": {"size": 890, "sha256": "64 lowercase hexadecimal characters"}
}
```

Sizes are uncompressed bytes; SHA-256 hashes the exact file bytes. The inventory
includes **every file except `pack.json`**. Build from a clean data directory with
no `.git`, symlinks or personal files. File order, timestamps and compression
settings are fixed, so identical input data and Python/zlib implementation produce
identical archives. The builder applies the installer's validation before
reporting success. `validate` uses a temporary directory and leaves your installed
packs and learning progress alone.

Settings → Language packs supports **Import pack** for a local archive and
**Download from URL** for a creator's direct HTTPS download link. CLI equivalents:

```sh
python3 scripts/language_pack.py install /tmp/french-1.0.0.wordpack
python3 scripts/language_pack.py list
python3 scripts/language_pack.py remove French
```

There are no archive directory entries, duplicate members, encrypted entries,
symlinks or other special files. Absolute paths, `..`, backslashes, colons and
control characters are rejected. ZIPs are limited to 32 MiB compressed, 128 MiB
expanded, 512 payload files and a 256 KiB manifest. Each vocabulary file is limited
to 8 MiB and 100,000 lines plus its header. Every inventory size and hash
is checked before activation. An invalid or interrupted update leaves the old
version selected. Pack installs/removals are serialized across processes, and an
atomic index replacement activates a fully validated generation. These checks
verify structure and integrity; they do not independently review vocabulary or
establish the identity of arbitrary community publishers.

## Optional Russian noun dictionary

A Russian pack can declare `"russian_nouns": "data/russian-nouns.json.gz"`.
This file must appear in `files`. It is gzip-compressed UTF-8 JSON:

```json
{
  "version": 1,
  "nouns": [{
    "lemma": "кни́га", "meaning": "book", "gender": "f", "animate": false,
    "indeclinable": false, "singular_only": false, "plural_only": false,
    "forms": {"sg_nom": ["кни́га"], "sg_gen": ["кни́ги"]}
  }]
}
```

Form keys use `sg`/`pl` and `nom`, `gen`, `dat`, `acc`, `inst`, `prep`. Values
are recorded alternatives; missing forms remain missing. The decompressed file
is capped at 96 MiB. Preserve source-specific licenses and stress distinctions.
The app's conservative Russian attention cues remain in application code. Other
language-specific grammar capabilities would need a documented future format
extension and application support; packs cannot introduce executable renderers.

An optional `source_manifest` path can reference an inventoried gzip JSON file
with the existing source rebuild/count/checksum metadata. Source snapshots,
provenance and README files may be inventoried alongside runtime data.

## Hosting a catalog on GitHub

Upload immutable, versioned archives as GitHub Release assets. Publish a small
UTF-8 `catalog.json` at a stable HTTPS URL, containing:

```json
{
  "version": 1,
  "packs": [{
    "id": "french-community",
    "language": "French",
    "version": "1.0.0",
    "description": "Beginner French words, with documented sources.",
    "license": "CC-BY-4.0",
    "attribution": "Author names; source details are included in the pack.",
    "url": "https://github.com/OWNER/REPO/releases/download/TAG/french-1.0.0.wordpack",
    "size": 12345,
    "sha256": "64 lowercase hexadecimal characters"
  }]
}
```

Catalog size and SHA-256 describe the **entire compressed archive**. Identity,
version, language and license must match its manifest. Catalog refresh and pack
downloads are explicit user actions; the screensaver never fetches data during
playback. The app ships a small catalog snapshot so users can see the official
choices before checking for updates. HTTPS and hashes protect transport/integrity;
a catalog publisher is still responsible for the content it lists.

To propose a community pack for the official catalog, open a pull request in the
language-packs repository with stable download links, source/rebuild instructions,
license notices and level-quality limitations. A standalone GitHub Release link
also works through Download from URL without being included in that catalog.
