# .cursor/skills/md-docx-export/scripts/build_reference_docx.py
"""Build Pandoc reference.docx with KP compact typography (9pt body, narrow page)."""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.shared import Cm, Pt

OUT = Path(__file__).resolve().parent.parent / "assets" / "kp-compact-reference.docx"

# Body 9pt; headings scale up proportionally
FONT = "Calibri"
BODY_PT = 9
HEADING_PT = {1: 16, 2: 13, 3: 11, 4: 10, 5: 9, 6: 9}
# Narrow layout (~14cm text width on A4)
MARGIN_CM = 1.5


def _set_style(doc: Document, name: str, size_pt: int, *, bold: bool = False, space_before: int = 0, space_after: int = 6) -> None:
    style = doc.styles[name]
    font = style.font
    font.name = FONT
    font.size = Pt(size_pt)
    font.bold = bold
    pf = style.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.15


def main() -> None:
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(MARGIN_CM)
        section.bottom_margin = Cm(MARGIN_CM)
        section.left_margin = Cm(MARGIN_CM)
        section.right_margin = Cm(MARGIN_CM)

    _set_style(doc, "Normal", BODY_PT, space_after=4)
    _set_style(doc, "Title", HEADING_PT[1], bold=True, space_after=8)
    _set_style(doc, "Subtitle", HEADING_PT[2], space_after=6)
    for level in range(1, 7):
        _set_style(
            doc,
            f"Heading {level}",
            HEADING_PT[level],
            bold=level <= 3,
            space_before=10 if level == 1 else 8,
            space_after=4,
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("Install python-docx: cd backend && pipenv run pip install python-docx", file=sys.stderr)
        sys.exit(1)
