"""Bind notes to reviewed source anchors after OCR paragraphs and diagrams are generated.

The mapping stores short locators, never copies of entire note texts. The note
wording and TeX emphasis always come from the current generated page. A changed
or ambiguous locator stops the build so that an editor can verify it again.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

PAGE = re.compile(r'(?m)^% Source PDF physical page (\d+);[^\n]*\n')
OCR_NOTE = r'\SourceFootnote{'
LABELS = '①②③④⑤'


@lru_cache(maxsize=1)
def _anchors():
    path = Path(__file__).resolve().parents[1] / 'data/editorial/footnote_anchors.json'
    return json.loads(path.read_text(encoding='utf-8'))


def _unique(text, excerpt, page):
    if text.count(excerpt) != 1:
        raise ValueError(f'Footnote locator changed on source page {page}: {excerpt!r}')
    return text.index(excerpt)


def _unwrap_ocr_notes(text):
    # One OCR wrapper may cover parts of several genuine reader notes.
    while OCR_NOTE in text:
        start = text.index(OCR_NOTE)
        body = start + len(OCR_NOTE)
        pos = body
        depth = 1
        while depth and pos < len(text):
            if text[pos] == '\\':
                pos += 2
                continue
            depth += (text[pos] == '{') - (text[pos] == '}')
            pos += 1
        if depth:
            raise ValueError('Unbalanced OCR note argument')
        text = text[:start] + text[body:pos - 1] + text[pos:]
    return text


def _page_notes(text, page, specs):
    text = _unwrap_ocr_notes(text)
    starts = [_unique(text, s['body'], page) for s in specs]
    if starts != sorted(set(starts)):
        raise ValueError(f'Footnote sequence changed on source page {page}')
    main = text[:starts[0]].rstrip()
    edits = []
    table_notes = {}
    end_notes = []
    for i, spec in enumerate(specs):
        start = starts[i] + len(spec['printed_label'])
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        content = text[start:end].strip()
        if 'trailing_label' in spec:
            extra = spec['trailing_label']
            if not content.endswith(extra):
                raise ValueError(f'Unrecognized OCR note ending on source page {page}')
            content = content[:-len(extra)].strip()
        # On two pages the end of a reference title was recognized as a heading.
        content = content.replace(r'\subsubsection*{（二）》。}', '（二）》。')
        if 'table' in spec:
            diagram = r'\InsertDiagram{' + spec['table'] + '}'
            after_diagram = _unique(main, diagram, page) + len(diagram)
            table_notes.setdefault(after_diagram, []).append(
                r'\SourceFootnote{\textbf{表注' + LABELS[i] + r'}\quad ' + content + '}'
            )
            continue
        anchor = spec['anchor']
        right = _unique(main, anchor, page) + len(anchor)
        left = right - len(spec['mark'])
        if spec.get('extended'):
            # These two source notes contain whole comparison tables. Keep each
            # table at readable text width and link the associated extended note.
            key = f'extended-note-{page}-{i+1}'
            edits.append((left, right, r'\hypertarget{' + key + '-ref}{}' +
                          r'\textsuperscript{\hyperlink{' + key + '}{附注}}'))
            end_notes.append(r'\par\noindent\hypertarget{' + key + '}{' +
                             r'\hyperlink{' + key + r'-ref}{\textbf{附注}}}\quad ' + content)
            continue
        line_start = main.rfind('\n', 0, left) + 1
        if re.match(r'\\(?:sub)*section\*\{', main[line_start:left]) and main[right:right+1] == '}':
            # Keep the note material out of the heading argument.
            edits.append((left, right+1, r'\protect\footnotemark}\footnotetext{' + content + '}'))
        elif page == 19 and i == 1:
            # Two ornamental chevrons followed by the note number were recognized
            # on a separate line. The scan places that note on the quiz heading.
            fragment = r'\OriginalPanel{典型真题}' + '\n\n' + r'\ensuremath{>}\ensuremath{>}②'
            begin = _unique(main, fragment, page)
            edits.append((begin, begin + len(fragment), r'\OriginalPanel{典型真题\footnotemark}\footnotetext{' + content + '}'))
        else:
            edits.append((left, right, r'\footnote{' + content + '}'))
    for after_diagram, notes in table_notes.items():
        edits.append((after_diagram, after_diagram, '\n' + '\n'.join(notes)))
    last = len(main)
    for start, end, replacement in sorted(edits, reverse=True):
        if end > last:
            raise ValueError(f'Overlapping footnote anchors on source page {page}')
        main = main[:start] + replacement + main[end:]
        last = start
    return '\n\n'.join([main, *end_notes]) + '\n\n'


def apply_footnotes(chapter_tex: str) -> str:
    """Transform a freshly generated chapter, before wrapping its special panels."""
    sections = PAGE.split(chapter_tex)
    output = [sections[0]]
    matches = PAGE.finditer(chapter_tex)
    for mark, number, body in zip(matches, sections[1::2], sections[2::2]):
        specs = _anchors().get(number)
        output.extend((mark.group(), _page_notes(body, int(number), specs) if specs else body))
    return ''.join(output)
