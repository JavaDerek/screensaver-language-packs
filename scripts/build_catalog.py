#!/usr/bin/env python3
"""Build validated language archives and their GitHub download catalog."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--app", type=Path, required=True, help="application checkout with language-pack support")
parser.add_argument("--tag", required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.app.resolve()))
from screensaver.savers.word_drift import packs

root = Path(__file__).resolve().parent.parent
items = []
for source in sorted((root / "packs").iterdir()):
    metadata = json.loads((source / "pack.json").read_text())
    archive = root / "dist" / f"{metadata['id']}-{metadata['version']}.wordpack"
    packs.build(source, archive)
    raw = archive.read_bytes()
    item = {key: metadata[key] for key in ("id", "language", "version", "description", "license", "attribution")}
    item.update(url=f"https://github.com/JavaDerek/screensaver-language-packs/releases/download/{args.tag}/{archive.name}",
                size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    items.append(item)
    print(f"Validated {archive.name}: {len(raw)} bytes")
raw = json.dumps({"version": 1, "packs": items}, ensure_ascii=False, indent=2) + "\n"
packs.catalog(raw)
(root / "catalog.json").write_text(raw, encoding="utf-8")
