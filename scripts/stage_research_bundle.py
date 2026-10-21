#!/usr/bin/env python3
"""Stage validated PULSE user research sources without publishing them.

python3 scripts/stage_research_bundle.py package.zip --output work/research-staging
The command intentionally refuses to write inside public/, src/, or data/.
"""
import argparse
import json
from pathlib import Path
import zipfile
from validate_research_bundle import validate_bundle


def stage_bundle(bundle: str, output: str) -> int:
    validate_bundle(bundle)
    destination = Path(output).resolve()
    repo = Path(__file__).resolve().parent.parent
    forbidden = [repo / p for p in ("public", "src", "data", ".git")]
    if any(destination == base or base in destination.parents for base in forbidden):
        raise ValueError("Refusing to stage directly into published source directories")
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        for source in manifest["research"]:
            for name in ("originals/" + source["filename"], source["extractedTextFilename"]):
                target = (destination / name).resolve()
                if destination not in target.parents:
                    raise ValueError("Invalid destination")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))
        (destination / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(manifest["research"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle")
    parser.add_argument("--output", default="work/research-staging")
    args = parser.parse_args()
    print("Staged unverified research sources:", stage_bundle(args.bundle, args.output))
