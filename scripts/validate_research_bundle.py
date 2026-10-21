#!/usr/bin/env python3
"""Validate a user-provided research import ZIP before manual adoption.

Usage: python3 scripts/validate_research_bundle.py /path/to/PULSE_Research_Import_Package_2026-10-21.zip
No writes to public/data, src/data or personal browser state.
"""
import hashlib
import json
import re
import sys
import zipfile

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def validate_bundle(bundle):
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive entries")
        if any(name.startswith("/") or ".." in name.split("/") or "\\" in name for name in names):
            raise ValueError("Unsafe archive entry name")
        info = {i.filename: i for i in archive.infolist()}
        if len(names) > 32 or sum(i.file_size for i in info.values()) > 20 * 1024 * 1024:
            raise ValueError("Archive exceeds safe bounds")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("version") != 1 or not isinstance(manifest.get("research"), list):
            raise ValueError("Unexpected manifest")
        seen = set()
        for entry in manifest["research"]:
            cid, filename, digest = entry["companyId"], entry["filename"], entry["sha256"]
            if cid in seen or not HEX64.fullmatch(digest) or not re.fullmatch(r"[A-Za-z0-9_.-]+\.pdf", filename):
                raise ValueError("Invalid source metadata")
            seen.add(cid)
            pdf_path = "originals/" + filename
            if pdf_path not in info:
                raise ValueError("Missing original PDF")
            pdf = archive.read(pdf_path)
            if not pdf.startswith(b"%PDF") or hashlib.sha256(pdf).hexdigest() != digest or len(pdf) != entry["bytes"]:
                raise ValueError("PDF integrity check failed")
            extracted_path = entry["extractedTextFilename"]
            if extracted_path not in info or not extracted_path.startswith("extracted/") or not extracted_path.endswith(".pages.json"):
                raise ValueError("Missing extracted text")
            extracted = json.loads(archive.read(extracted_path))
            pages = extracted["pages"]
            if len(pages) != entry["pages"] or any(p["page"] != i + 1 or not p["text"].strip() for i, p in enumerate(pages)):
                raise ValueError("Page extraction mismatch")
        if len(manifest["research"]) != 7:
            raise ValueError("Expected seven newly supplied source PDFs")
    return len(seen)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: validate_research_bundle.py FILE.zip")
    print("Source PDFs validated:", validate_bundle(sys.argv[1]))
