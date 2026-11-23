#!/usr/bin/env python3
"""Verify and restore the complete ctexbook project using Python's standard library."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import zipfile


CHUNK = 1024 * 1024
BASE = Path(__file__).resolve().parent


def fail(message):
    raise ValueError(message)


def safe_parts(name, directory=False):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        fail("Unsafe archive path: " + repr(name))
    raw = name[:-1] if directory and name.endswith("/") else name
    pieces = raw.split("/")
    if any(p in ("", ".", "..") or ":" in p for p in pieces):
        fail("Unsafe archive path: " + repr(name))
    if PurePosixPath(raw).is_absolute():
        fail("Absolute archive path: " + repr(name))
    return pieces


def validate_digest(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        fail("Invalid SHA-256 in manifest")


def positive_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        fail("Invalid " + label)


def load_manifest():
    with (BASE / "package-manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    if manifest.get("schema_version") != 1:
        fail("Unsupported manifest schema")
    package = manifest["package"]
    validate_digest(package["sha256"])
    for key in ("size_bytes", "file_count", "checksum_file_count", "uncompressed_bytes"):
        positive_int(package[key], key)
    if len(safe_parts(package["top_level_directory"])) != 1:
        fail("Expected one top-level directory")
    if package["file_count"] != package["checksum_file_count"] + 1:
        fail("Inconsistent manifest file counts")
    parts = manifest["parts"]
    if not isinstance(parts, list) or not parts:
        fail("Empty parts list")
    names = set()
    total = 0
    for part in parts:
        name = part["name"]
        if len(safe_parts(name)) != 1 or name in names:
            fail("Invalid or duplicate part name")
        names.add(name)
        validate_digest(part["sha256"])
        positive_int(part["size_bytes"], "part size")
        total += part["size_bytes"]
    if total != package["size_bytes"]:
        fail("Part sizes do not sum to archive size")
    return manifest


def join_parts(manifest, target):
    full_hash = hashlib.sha256()
    full_size = 0
    with target.open("xb") as output:
        for part in manifest["parts"]:
            path = BASE / part["name"]
            if path.is_symlink() or not path.is_file():
                fail("Missing or non-regular part: " + part["name"])
            if path.stat().st_size != part["size_bytes"]:
                fail("Wrong size: " + part["name"])
            digest = hashlib.sha256()
            size = 0
            with path.open("rb") as source:
                while True:
                    block = source.read(CHUNK)
                    if not block:
                        break
                    output.write(block)
                    digest.update(block)
                    full_hash.update(block)
                    size += len(block)
            if size != part["size_bytes"] or digest.hexdigest() != part["sha256"]:
                fail("Part checksum mismatch: " + part["name"])
            full_size += size
            print("Verified " + part["name"], flush=True)
    package = manifest["package"]
    if full_size != package["size_bytes"] or full_hash.hexdigest() != package["sha256"]:
        fail("Full archive checksum mismatch")
    return full_hash.hexdigest()


def inspect_archive(archive, package):
    root = package["top_level_directory"]
    files = {}
    seen = set()
    total = 0
    for info in archive.infolist():
        if "\x00" in info.orig_filename:
            fail("NUL in archive path")
        pieces = safe_parts(info.filename, info.is_dir())
        if pieces[0] != root:
            fail("Unexpected top-level archive path")
        normalized = "/".join(pieces)
        if normalized in seen:
            fail("Duplicate archive path: " + normalized)
        seen.add(normalized)
        kind = stat.S_IFMT(info.external_attr >> 16)
        if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
            fail("Links and special files are not allowed: " + normalized)
        if info.flag_bits & 1:
            fail("Encrypted ZIP entries are not supported")
        if not info.is_dir():
            if len(pieces) < 2 or kind == stat.S_IFDIR:
                fail("Invalid file path: " + normalized)
            relative = "/".join(pieces[1:])
            files[relative] = info
            total += info.file_size
    if len(files) != package["file_count"] or total != package["uncompressed_bytes"]:
        fail("Archive file count or uncompressed size differs from manifest")
    checksum_name = "SHA256SUMS.json"
    if checksum_name not in files or files[checksum_name].file_size > 5 * 1024 * 1024:
        fail("Missing or oversized project checksum manifest")
    checksums = json.loads(archive.read(files[checksum_name]).decode("utf-8"))
    if not isinstance(checksums, dict) or len(checksums) != package["checksum_file_count"]:
        fail("Wrong project checksum count")
    for name, digest in checksums.items():
        safe_parts(name)
        validate_digest(digest)
    if set(files) != set(checksums) | {checksum_name} or checksum_name in checksums:
        fail("Missing or extra project files")
    return files, checksums


def check_contents(archive, files, checksums, extraction_root=None):
    for name, info in files.items():
        target = extraction_root.joinpath(*safe_parts(name)) if extraction_root else None
        if target:
            target.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        size = 0
        with archive.open(info, "r") as source:
            output = target.open("xb") if target else None
            try:
                while True:
                    block = source.read(CHUNK)
                    if not block:
                        break
                    digest.update(block)
                    size += len(block)
                    if output:
                        output.write(block)
            finally:
                if output:
                    output.close()
        if size != info.file_size:
            fail("Wrong extracted size: " + name)
        if name in checksums and digest.hexdigest() != checksums[name]:
            fail("Project checksum mismatch: " + name)
        if target and name in checksums:
            written_digest = hashlib.sha256()
            with target.open("rb") as written:
                while True:
                    block = written.read(CHUNK)
                    if not block:
                        break
                    written_digest.update(block)
            if written_digest.hexdigest() != checksums[name]:
                fail("Extracted file checksum mismatch: " + name)
    if extraction_root:
        actual = {p.relative_to(extraction_root).as_posix()
                  for p in extraction_root.rglob("*") if p.is_file()}
        if actual != set(files):
            fail("Missing or extra extracted files")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true",
                        help="Verify all parts, the ZIP and all archived files without restoring a directory")
    parser.add_argument("--destination", type=Path,
                        help="New output directory; default is criminal_law_ctexbook beside this script")
    args = parser.parse_args()
    manifest = load_manifest()
    package = manifest["package"]
    destination = (args.destination or BASE / package["top_level_directory"]).absolute()
    if not args.verify_only and (destination.exists() or destination.is_symlink()):
        fail("Destination already exists; refusing to overwrite: " + str(destination))
    if not args.verify_only:
        destination.parent.mkdir(parents=True, exist_ok=True)
    temp_parent = None if args.verify_only else destination.parent
    with tempfile.TemporaryDirectory(prefix="criminal-law-restore-", dir=temp_parent) as temporary:
        temporary = Path(temporary)
        archive_path = temporary / "project.zip"
        full_hash = join_parts(manifest, archive_path)
        extraction_root = None if args.verify_only else temporary / "extracted"
        if extraction_root:
            extraction_root.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            files, checksums = inspect_archive(archive, package)
            check_contents(archive, files, checksums, extraction_root)
        if extraction_root:
            # Never merge into an existing directory, including one created during verification.
            if destination.exists() or destination.is_symlink():
                fail("Destination appeared during verification; refusing to overwrite")
            os.rename(extraction_root, destination)
        result = {
            "status": "verified" if args.verify_only else "restored",
            "archive_sha256": full_hash,
            "archive_size_bytes": package["size_bytes"],
            "project_files": len(files),
            "file_checksums_verified": len(checksums),
            "extra_files": 0,
        }
        if not args.verify_only:
            result["destination"] = str(destination)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, RuntimeError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        sys.exit(1)
