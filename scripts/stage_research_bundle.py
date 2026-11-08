#!/usr/bin/env python3
"""Stage validated PULSE research sources without publishing or overwriting files.

python3 scripts/stage_research_bundle.py package.zip --output work/research-staging
Staging requires a new destination and is all-or-nothing on the same filesystem.
"""
import argparse
import json
from pathlib import Path
import tempfile
import zipfile

from validate_research_bundle import validate_bundle


def stage_bundle(bundle: str, output: str) -> int:
    # Validate the complete archive before making any destination directories.
    count = validate_bundle(bundle)
    destination = Path(output).expanduser().absolute()
    resolved = destination.resolve()
    repo = Path(__file__).resolve().parent.parent
    work = repo / "work"

    # Within the repository only work/<new-name> is an acceptable staging
    # location. Never stage over the repository root, code, docs or public data.
    if resolved == repo or (repo in resolved.parents and work not in resolved.parents):
        raise ValueError("Staging inside the repository is restricted to work/")
    if destination.exists() or destination.is_symlink():
        raise ValueError("Staging destination already exists; choose a new directory")

    destination.parent.mkdir(parents=True, exist_ok=True)
    # Build in a private sibling directory; a failed read/write/rename leaves
    # the requested output absent rather than partially populated.
    with tempfile.TemporaryDirectory(
        prefix=".pulse-research-stage-", dir=destination.parent
    ) as temporary:
        staging = Path(temporary).resolve()
        with zipfile.ZipFile(bundle) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            for source in manifest["research"]:
                names = ("originals/" + source["filename"], source["extractedTextFilename"])
                for name in names:
                    target = (staging / name).resolve()
                    if staging not in target.parents:
                        raise ValueError("Invalid destination")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(name))
            (staging / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        # Refuse accidental replacement of an earlier review. The rename is
        # atomic on the same filesystem; this is not a multi-user locking API.
        if destination.exists() or destination.is_symlink():
            raise ValueError("Staging destination appeared during preparation")
        staging.rename(destination)
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle")
    parser.add_argument("--output", default="work/research-staging")
    args = parser.parse_args()
    print("Staged unverified research sources:", stage_bundle(args.bundle, args.output))
