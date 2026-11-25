"""Compile the detailed guide with XeLaTeX and the Latin Modern font map."""
import argparse
import os
import shutil
import subprocess
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "build" / "guide.pdf")
    destination = parser.parse_args().output.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    work = root / "build"
    work.mkdir(exist_ok=True)
    env = dict(os.environ)
    env.setdefault("SOURCE_DATE_EPOCH", "1794009600")
    for name in ("xelatex", "xdvipdfmx"):
        if not shutil.which(name):
            raise SystemExit(f"Missing TeX Live program: {name}")
    for _ in range(3):
        subprocess.run(
            ["xelatex", "-no-pdf", "-interaction=nonstopmode", "-halt-on-error",
             "-file-line-error", f"-output-directory={work}", "main.tex"],
            cwd=root / "src", env=env, check=True,
        )
    subprocess.run(["xdvipdfmx", "-q", "-f", "lm.map", "-o", "compiled.pdf", "main.xdv"],
                   cwd=work, env=env, check=True)
    pdf = work / "compiled.pdf"
    if pdf != destination:
        temporary = destination.with_suffix(".tmp.pdf")
        shutil.copyfile(pdf, temporary)
        temporary.replace(destination)
    print(destination)


if __name__ == "__main__":
    main()
