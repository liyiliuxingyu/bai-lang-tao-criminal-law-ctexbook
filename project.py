#!/usr/bin/env python3
"""Build the retypeset textbook and short study guide on a verified archive."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
BOOKS = ("retypeset", "mathematical")
MODELS = ("verify_math_models.py", "verify_derivation_models.py", "verify_derivations.py")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def run(script, *args, cwd):
    # The model checkers use Python assertions. Run them with assertions enabled,
    # even if the caller's interactive environment uses python -O.
    env = os.environ.copy()
    env.pop("PYTHONOPTIMIZE", None)
    print(f"Running {script.name}", flush=True)
    subprocess.run([sys.executable, str(script), *map(str, args)], cwd=cwd, env=env, check=True)


def restore_current(work):
    run(ROOT / "restore_project.py", "--destination", work, cwd=ROOT)
    for name in ("tex", "scripts"):
        source = ROOT / name
        if not source.is_dir():
            raise ValueError(f"Current source tree is missing: {source}")
        # These two trees are complete mirrors. A deletion in Git must take
        # effect instead of silently falling back to an old archived file.
        shutil.rmtree(work / name)
        shutil.copytree(source, work / name, ignore=IGNORE)
    for name in ("data/figures", "data/editorial"):
        source = ROOT / name
        if source.is_dir():
            shutil.copytree(source, work / name, dirs_exist_ok=True, ignore=IGNORE)


def tex_hashes(work):
    return {p.relative_to(work).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((work / "tex").rglob("*.tex"))}


def check_regenerated_sources(before, work):
    after = tex_hashes(work)
    different = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
    if different:
        raise ValueError("Regeneration differs from the editable source:\n" + "\n".join(different))


def inspect_pdf(path, pdf_module):
    with pdf_module.open(path) as doc:
        if doc.is_repaired or not len(doc):
            raise ValueError(f"Damaged or empty PDF: {path.name}")
        characters = 0
        for page in doc:
            if page.get_image_info():
                raise ValueError(f"Raster image found: {path.name} page {page.number + 1}")
            text = page.get_text()
            if "关注公众号" in "".join(text.split()):
                raise ValueError(f"Promotional footer found: {path.name} page {page.number + 1}")
            characters += len(text.strip())
        if not characters:
            raise ValueError(f"No extractable text: {path.name}")
        return {"pages": len(doc), "characters": characters, "raster_images": 0}


def check_compile(work, name):
    log = (work / "output" / f"{name}.log").read_text(errors="replace")
    patterns = {
        "overfull_hbox": r"Overfull \\hbox",
        "overfull_vbox": r"Overfull \\vbox",
        "missing_characters": "Missing character:",
        "unresolved_references": r"(?:LaTeX Warning: (?:Reference|Citation).*?undefined|There were undefined (?:references|citations))",
        "rerun_required": r"(?:Label\(s\) may have changed|Rerun to get (?:cross-references|outlines) right)",
    }
    counts = {key: len(re.findall(pattern, log)) for key, pattern in patterns.items()}
    if any(counts.values()):
        raise ValueError(f"{name}: typesetting check failed: {counts}")
    return counts


def copy_result(source, destination):
    # Readers should see either the previous or the complete new file.
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as staging:
        temporary = Path(staging.name)
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("compile", "rebuild", "verify"))
    parser.add_argument("book", nargs="?", choices=(*BOOKS, "all"), default="all",
                        help="select a book for compile; rebuild and verify process both")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build" / "output",
                        help="publish successful PDFs and, for verify, verification.json here")
    parser.add_argument("--cache-dir", type=Path, default=None,
                        help="parent for the disposable private build (default: system temporary directory)")
    args = parser.parse_args()
    if args.action != "compile" and args.book != "all":
        parser.error("rebuild and verify process both books; select a single book with compile")
    verify = args.action == "verify"
    if verify:
        try:
            import pymupdf
        except ImportError:
            parser.error("verify requires PyMuPDF >= 1.24; install it with python -m pip install PyMuPDF")

    if args.cache_dir and any(args.cache_dir.resolve().is_relative_to(ROOT / tree)
                              for tree in ("tex", "scripts", "data/figures", "data/editorial")):
        parser.error("--cache-dir cannot be inside a source tree that will be copied")
    if args.cache_dir:
        args.cache_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir.resolve()
    books = BOOKS if args.book == "all" else (args.book,)
    with tempfile.TemporaryDirectory(prefix="criminal-law-build-", dir=args.cache_dir) as temporary:
        work = Path(temporary).resolve() / "project"
        restore_current(work)
        for name in books:
            (work / "output" / f"{name}.pdf").unlink(missing_ok=True)
        scripts = work / "scripts"
        if args.action == "compile":
            run(scripts / "compile.py", *books, cwd=work)
        else:
            before = tex_hashes(work) if verify else {}
            run(scripts / "rebuild_all.py", cwd=work)
            if verify:
                check_regenerated_sources(before, work)
        report = {}
        for name in books:
            report[name] = check_compile(work, name)
            if verify:
                report[name].update(inspect_pdf(work / "output" / f"{name}.pdf", pymupdf))
        if verify:
            for model in MODELS:
                run(scripts / model, cwd=work)
            run(scripts / "verify_continued_tables.py", work / "output/retypeset.pdf", cwd=work)
            report["continued_tables_checked"] = True
            report["model_checks"] = list(MODELS)
            report["regenerated_tex_matches"] = True
            (work / "output" / "verification.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        output.mkdir(parents=True, exist_ok=True)
        results = [f"{name}.pdf" for name in books]
        if verify:
            results.append("verification.json")
        for filename in results:
            copy_result(work / "output" / filename, output / filename)
            print(output / filename)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
