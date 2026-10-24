#!/usr/bin/env python3
"""Validate a user-provided research import ZIP before manual adoption.

Usage: python3 scripts/validate_research_bundle.py /path/to/PULSE_Research_Import_Package_2026-10-21.zip
No writes to public/data, src/data or personal browser state.
"""
import hashlib
import json
import re
import stat
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
        referenced_members = {"manifest.json"}
        page_destinations = set()
        pdf_destinations = set()
        text_sources = set()
        for entry in manifest["research"]:
            cid, filename, digest = entry["companyId"], entry["filename"], entry["sha256"]
            ticker = entry.get("ticker")
            # The importer derives a public filename from ticker. Reject path separators,
            # traversal, whitespace ambiguity and collisions *before* any writes.
            if (not isinstance(ticker, str)
                    or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}", ticker)
                    or ticker != ticker.strip()):
                raise ValueError("Unsafe ticker for extracted page destination")
            page_destination = (ticker.replace(" ", "_") + ".pages.json").casefold()
            if page_destination in page_destinations:
                raise ValueError("Duplicate extracted page destination")
            if (not isinstance(cid, str) or not cid or cid in seen
                    or not isinstance(digest, str) or not HEX64.fullmatch(digest)
                    or not isinstance(filename, str)
                    or not re.fullmatch(r"[A-Za-z0-9_.-]+\.pdf", filename)):
                raise ValueError("Invalid source metadata")
            pdf_destination = filename.casefold()
            if pdf_destination in pdf_destinations:
                raise ValueError("Duplicate PDF destination")
            seen.add(cid)
            page_destinations.add(page_destination)
            pdf_destinations.add(pdf_destination)
            pdf_path = "originals/" + filename
            referenced_members.add(pdf_path)
            if pdf_path not in info:
                raise ValueError("Missing original PDF")
            pdf = archive.read(pdf_path)
            if not pdf.startswith(b"%PDF") or hashlib.sha256(pdf).hexdigest() != digest or len(pdf) != entry["bytes"]:
                raise ValueError("PDF integrity check failed")
            extracted_path = entry["extractedTextFilename"]
            if (not isinstance(extracted_path, str)
                    or extracted_path not in info
                    or not extracted_path.startswith("extracted/")
                    or not extracted_path.endswith(".pages.json")):
                raise ValueError("Missing extracted text")
            referenced_members.add(extracted_path)
            if extracted_path.casefold() in text_sources:
                raise ValueError("Duplicate extracted text source")
            text_sources.add(extracted_path.casefold())
            extracted = json.loads(archive.read(extracted_path))
            pages = extracted["pages"]
            if len(pages) != entry["pages"] or any(p["page"] != i + 1 or not p["text"].strip() for i, p in enumerate(pages)):
                raise ValueError("Page extraction mismatch")
        if len(manifest["research"]) != 7:
            raise ValueError("Expected seven newly supplied source PDFs")

        # A reviewed bundle has exactly the manifest and its referenced inputs.
        # Ignore neither hidden payloads nor filesystem-type claims in ZIP headers.
        optional_directories = {"originals/", "extracted/"}
        if set(info) - referenced_members - optional_directories:
            raise ValueError("Unexpected unreferenced archive member")
        for name, member in info.items():
            if member.is_dir() != (name in optional_directories):
                raise ValueError("Unexpected archive directory entry")
            if member.create_system == 3:
                file_type = stat.S_IFMT(member.external_attr >> 16)
                expected_type = stat.S_IFDIR if member.is_dir() else stat.S_IFREG
                if file_type not in (0, expected_type):
                    raise ValueError("Unsupported archive member type")
    return len(seen)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: validate_research_bundle.py FILE.zip")
    print("Source PDFs validated:", validate_bundle(sys.argv[1]))
