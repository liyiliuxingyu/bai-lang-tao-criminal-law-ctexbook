"""Restore the opening panels using their observed boundaries in the scan."""
from pathlib import Path
import re


OPENING = r'\OriginalPanel{特别提示}'
BEGIN = r'\begin{EditionOpeningPanel}'
END = r'\end{EditionOpeningPanel}'


def apply_panels(project: Path, chapter_numbers=range(1, 26)) -> None:
    chapters = Path(project) / 'tex' / 'chapters'
    for number in chapter_numbers:
        path = chapters / f'chapter{number:02d}.tex'
        text = path.read_text(encoding='utf-8')
        if text.count(BEGIN) == text.count(END) == 1 and OPENING not in text:
            continue
        if text.count(OPENING) != 1 or BEGIN in text or END in text:
            raise ValueError(f'{path.name}: expected one unwrapped opening panel')
        before, after = text.split(OPENING)
        if number == 20:
            # The scan places the note belonging to the final table cell outside the frame.
            table = r'\InsertDiagram{figures/manual_table_p316_1.tex}'
            content, separator, rest = after.partition(table)
            if not separator:
                raise ValueError(f'{path.name}: opening table is missing')
            content += separator
        else:
            # Chapter 3 proceeds directly to its opening question, chapter 25 to a subsection.
            pattern = r'^\[问题' if number == 3 else r'^\\(?:sub)?section\*?\{'
            boundary = re.search(pattern, after, re.MULTILINE)
            if boundary is None:
                raise ValueError(f'{path.name}: opening-panel boundary is missing')
            content, rest = after[:boundary.start()], after[boundary.start():]
        if not content.strip() or re.search(r'^% Source PDF physical page', content, re.MULTILINE):
            raise ValueError(f'{path.name}: opening content does not fit its source page')
        path.write_text(before + BEGIN + '\n' + content.strip() + '\n' + END
                        + '\n\n' + rest.lstrip('\n'), encoding='utf-8')
