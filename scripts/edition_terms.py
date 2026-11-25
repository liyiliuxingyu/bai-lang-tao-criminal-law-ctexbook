"""Apply individually image-verified OCR corrections in their source-page blocks."""

import json
import re
from functools import lru_cache
from pathlib import Path


PAGE = re.compile(r"(?m)^% Source PDF physical page (\d+);[^\n]*\n")


@lru_cache(maxsize=1)
def _review():
    path = Path(__file__).resolve().parents[1] / "data/editorial/terms.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _apply_page(text: str, page: str, review: dict) -> str:
    term = review["term_correction"]
    expected = term["source_pages"].get(page)
    if expected:
        count = text.count(term["before"])
        if count not in (0, expected["corrections"]):
            raise ValueError(f"Term correction count changed on source page {page}: {count}")
        if count:
            text = text.replace(term["before"], term["after"])
        elif text.count(term["after"]) < expected["corrections"]:
            raise ValueError(f"Reviewed term text missing on source page {page}")
    for correction in review["adjacent_corrections"]:
        if correction["source_pdf_page"] != int(page):
            continue
        before, after = correction["before"], correction["after"]
        count = text.count(before)
        if count == 1:
            text = text.replace(before, after)
        elif count or text.count(after) != 1:
            raise ValueError(f"OCR correction locator changed on source page {page}: {before!r}")
    return text


def apply_terms(chapter_tex: str) -> str:
    """Correct reviewed terms after footnote relocation, retaining all TeX marks.

    The page markers locate the verified source blocks. Existing correct 谴责
    occurrences stay correct, including mixed old and correct terms in one row.
    Applying this function to an already corrected chapter has no effect.
    """
    review = _review()
    pieces = PAGE.split(chapter_tex)
    output = [pieces[0]]
    for marker, number, body in zip(PAGE.finditer(chapter_tex), pieces[1::2], pieces[2::2]):
        output.extend((marker.group(), _apply_page(body, number, review)))
    return "".join(output)
