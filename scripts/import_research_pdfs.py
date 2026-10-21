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
PAGES_TARGET = ROOT / "public" / "research-pages"


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
        # Page text has its own namespace and must be validated before any write.
        page_tasks = []
        for entry in manifest["research"]:
            text = z.read(entry["extractedTextFilename"])
            pages = json.loads(text)["pages"]
            if len(pages) != entry["pages"]:
                raise ValueError("Extracted page count mismatch")
            target = PAGES_TARGET / (entry["ticker"] + ".pages.json")
            if target.exists() and target.read_bytes() != text:
                raise ValueError("Conflicting page text: " + target.name)
            if not target.exists():
                page_tasks.append((target, text))
        if not dry_run:
            TARGET.mkdir(parents=True, exist_ok=True)
            PAGES_TARGET.mkdir(parents=True, exist_ok=True)
            for path, source in tasks:
                path.write_bytes(source)
                if hashlib.sha256(path.read_bytes()).hexdigest() != hashlib.sha256(source).hexdigest():
                    raise RuntimeError("Post-write checksum mismatch: " + path.name)
        if not dry_run:
            for path, text in page_tasks:
                path.write_bytes(text)
        return [path.name for path, _ in tasks] + [path.name for path, _ in page_tasks]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", help="User-provided PULSE Research Import Package ZIP")
    parser.add_argument("--apply", action="store_true", help="Write verified PDFs (dry-run by default)")
    args = parser.parse_args()
    files = install(args.bundle, dry_run=not args.apply)
    print(("Imported" if args.apply else "Would import") + ": " + ", ".join(files or ["none (identical files already exist)"]))
    print("Analyst research remains UNVERIFIED, and valuations are NOT changed.")
