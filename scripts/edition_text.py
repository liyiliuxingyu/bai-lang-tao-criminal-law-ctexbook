"""Verified corrections and continued-table headings for the reading edition."""

import re


_CONTINUATION = re.compile(
    r"^续表\n(?:[ \t]*\n)*\\InsertDiagram\{(figures/manual_table_[^}\n]+\.tex)\}$",
    re.MULTILINE,
)


def apply_text(chapter_tex: str) -> str:
    """Apply these editorial changes to one generated chapter, idempotently."""
    chapter_tex = _CONTINUATION.sub(r"\\ContinuedTable{\1}", chapter_tex)
    chapter_tex = chapter_tex.replace("5.排除犯罪事由1-排除违法事由", "5.排除犯罪事由I-排除违法事由")
    # Keep the original three figures visible. The two transactions determine
    # their net sum, but do not tell us which figure the author intended.
    return re.sub(
        r"^(例2，甲贪污了100万元，用来炒股，一个月后赚了50万元，两个月后又赔了10万元，"
        r"截至案发时，共赚了30万元。犯罪所得是100万元，犯罪所得的收益是30万元。)$",
        lambda match: match[0]
        + r"\footnote{编校注：按题面列出的两笔盈亏计算，净收益为 \(50-10=40\) 万元。"
          r"原书在本例中两次写作“30万元”。}",
        chapter_tex,
        flags=re.MULTILINE,
    )
