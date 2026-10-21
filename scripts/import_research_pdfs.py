#!/usr/bin/env python3
"""Import reviewed PDF bytes from the user-provided source ZIP into public/research/.

Requires a local checked-out feature branch and explicit CLI invocation.
No automatic source-data verification and no valuation promotion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from validate_research_bundle import validate_bundle

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "public" / "research"


def install(bundle: str, dry_run: bool = True) -> list[str]:
    validate_bundle(bundle)
    with zipfile.ZipFile(bundle) as z:
        manifest = json.loads(z.read("manifest.json"))
        tasks = []
        for entry in manifest["research"]:
            source = z.read("originals/" + entry["filename"])
            destination = TARGET / entry["filename"]
            if destination.exists():
                prior = destination.read_bytes()
                if hashlib.sha256(prior).hexdigest() != entry["sha256"]:
                    raise ValueError("Conflicting existing PDF: " + destination.name)
                continue
            tasks.append((destination, source))
        if not dry_run:
            TARGET.mkdir(parents=True, exist_ok=True)
            for path, source in tasks:
                path.write_bytes(source)
                if hashlib.sha256(path.read_bytes()).hexdigest() != hashlib.sha256(source).hexdigest():
                    raise RuntimeError("Post-write checksum mismatch: " + path.name)
        return [path.name for path, _ in tasks]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", help="User-provided PULSE Research Import Package ZIP")
    parser.add_argument("--apply", action="store_true", help="Write verified PDFs (dry-run by default)")
    args = parser.parse_args()
    files = install(args.bundle, dry_run=not args.apply)
    print(("Imported" if args.apply else "Would import") + ": " + ", ".join(files or ["none (identical files already exist)"]))
    print("Analyst research remains UNVERIFIED, and valuations are NOT changed.")
