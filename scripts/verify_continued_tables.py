"""Verify that every retained continuation heading and its first table header share a page."""

import argparse
from pathlib import Path

import fitz


# First column of each original continuation table, in reading order.
FIRST_HEADERS = (
    "种类", "责任能力的程度", "可能有效性", "作为义务人（甲）", "基本原理",
    "种类", "行为类型", "行为类型", "财物档次", "误解的类型", "保险诈骗罪",
    "罪名", "行为类型", "非国家工作人员（甲）",
)


def check_continuations(pdf_path: Path) -> list[int]:
    pages = []
    with fitz.open(pdf_path) as document:
        for page in document:
            for block in page.get_text("blocks", sort=True):
                if block[4].strip() != "续表":
                    continue
                if len(pages) == len(FIRST_HEADERS):
                    raise ValueError(f"PDF page {page.number + 1} contains an extra continuation")
                header = FIRST_HEADERS[len(pages)]
                # All retained table heads are within 65 PDF points under the
                # caption, including wrapped headings. Exclude preceding text.
                region = fitz.Rect(0, block[3] - 1, page.rect.width, min(block[3] + 65, page.rect.height))
                if header not in "".join(page.get_textbox(region).split()):
                    raise ValueError(f"PDF page {page.number + 1}: expected “{header}” directly below “续表”")
                pages.append(page.number + 1)
    if len(pages) != len(FIRST_HEADERS):
        raise ValueError(f"Expected {len(FIRST_HEADERS)} continuation headings, found {len(pages)}")
    return pages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    try:
        page_numbers = check_continuations(parser.parse_args().pdf)
    except ValueError as error:
        parser.exit(1, str(error) + "\n")
    print(f"Verified {len(page_numbers)} continued tables on PDF pages {page_numbers}")
