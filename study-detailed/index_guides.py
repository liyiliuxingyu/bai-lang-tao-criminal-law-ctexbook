"""Regenerate the lecture concordance from the two PDFs' bookmarks."""
import argparse
import re
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parent
LECTURE = re.compile(r"^(第[一二三四五六七八九十]+讲) ")
SECTION = re.compile(r"^第[一二三四五六七八九十]+节 ")
SHORT_LECTURE = re.compile(r"^(\d+\.\d+) (第[一二三四五六七八九十]+讲)[：:]")
APPENDIX = "逐讲扩展规则"


def page_link(path, page):
    return f"[{page}]({path}#page={page})"


def make_index():
    with pymupdf.open(ROOT / "guide.pdf") as pdf:
        long_toc = pdf.get_toc()
    with pymupdf.open(ROOT.parent / "criminal-law-mathematical.pdf") as pdf:
        short_toc = pdf.get_toc()
    short = {}
    for level, title, page in short_toc:
        match = SHORT_LECTURE.match(title)
        if level == 2 and match:
            short[match[2]] = (match[1], page)

    chapters, section_rows, rules = [], [], {}
    current = None
    in_rules = False
    for level, title, page in long_toc:
        match = LECTURE.match(title)
        if level == 1:
            in_rules = title == APPENDIX
            current = None
            if match:
                current = match[1]
                chapters.append((current, title, page))
        elif level == 2 and in_rules and match:
            rules[match[1]] = page
        elif level == 2 and current:
            section_rows.append((current, title, page))
    names = [tag for tag, _, _ in chapters]
    named = [row for row in section_rows if SECTION.match(row[1])]
    if len(names) != 25 or set(names) != set(short) or set(names) != set(rules):
        raise ValueError("The two guides and the rule appendix must each have the same 25 lecture numbers")
    if len(named) != 106:
        raise ValueError(f"Expected 106 numbered section headings, found {len(named)}")

    lines = [
        "# 简册、详册与教材对照索引", "",
        "页数按 PDF 阅读器从封面起计。简册以每讲为一个单元；同一讲内各节共用简册入口。"
        "详册另列每一节及该讲扩展规则的起始页。点击各讲末列可查看对应的可编辑源码。", "",
        "## 二十五讲", "",
        "| 讲次与主题 | 简册节次 | 简册页 | 详册页 | 扩展规则页 | 源码 |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for i, (tag, title, page) in enumerate(chapters, 1):
        number, short_page = short[tag]
        lines.append(
            f"| {title} | {number} | {page_link('../criminal-law-mathematical.pdf', short_page)} | "
            f"{page_link('guide.pdf', page)} | {page_link('guide.pdf', rules[tag])} | "
            f"[教材](../tex/chapters/chapter{i:02d}.tex) · [详册](src/chapters/ch{i:02d}.tex) |"
        )
    lines += [
        "", "## 一百零六个具名节", "",
        "下表按教材顺序列出编号节。教材第三讲直接论述犯罪客体，详册另分“犯罪客体”与“保障人权”两题；这两题单列于表下。", "",
        "| 讲次 | 节名 | 简册对应讲页 | 详册本节页 |", "| --- | --- | ---: | ---: |",
    ]
    for tag, title, page in named:
        lines.append(f"| {tag} | {title} | {page_link('../criminal-law-mathematical.pdf', short[tag][1])} | {page_link('guide.pdf', page)} |")
    lines += ["", "第三讲的两个研习专题："]
    for tag, title, page in section_rows:
        if not SECTION.match(title):
            lines += ["", f"- {title}，详册第 {page_link('guide.pdf', page)} 页。"]
    lines += ["", "## 推导、训练与记忆", ""]
    for level, title, page in long_toc:
        if level == 1 and not LECTURE.match(title):
            lines.append(f"- {title}，详册第 {page_link('guide.pdf', page)} 页。")
    for level, title, page in short_toc:
        if level == 2 and title.startswith(("8.7 ", "9.2 ", "9.3 ", "9.4 ")):
            lines.append(f"- {title.split(' ', 1)[1]}，简册第 {page_link('../criminal-law-mathematical.pdf', page)} 页。")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    path = ROOT / "concordance.md"
    content = make_index()
    if parser.parse_args().check:
        if path.read_text(encoding="utf-8") != content:
            raise SystemExit("Concordance differs from the PDF bookmarks")
    else:
        path.write_text(content, encoding="utf-8")
