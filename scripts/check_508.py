#!/usr/bin/env python3
"""Section 508 / WCAG 2.1 AA compliance checker for a .pptx deck.

Usage: python scripts/check_508.py <path-to-pptx>

Exits 0 only when all checks pass and prints `PASS: all 508 checks passed`.
Exits 1 with one or more `FAIL: <slide> — <description>` lines otherwise.
"""

import re
import sys

from pptx import Presentation


# WCAG sRGB relative luminance.
def _to_lin(c: float) -> float:
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb):
    r, g, b = (v / 255.0 for v in rgb)
    return 0.2126 * _to_lin(r) + 0.7152 * _to_lin(g) + 0.0722 * _to_lin(b)


def contrast_ratio(fg, bg):
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


# Theme background — confirmed from build_deck.py
BG_RGB = (0x1A, 0x1A, 0x2E)

A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"


def _cNvPr(shape):
    for el in shape.element.iter():
        tag = el.tag
        if isinstance(tag, str) and tag.endswith("}cNvPr"):
            return el
    return None


def _shape_name(shape):
    cnvpr = _cNvPr(shape)
    if cnvpr is not None and cnvpr.get("name"):
        return cnvpr.get("name")
    return shape.name or ""


def _shape_descr(shape):
    cnvpr = _cNvPr(shape)
    if cnvpr is None:
        return ""
    return cnvpr.get("descr") or ""


def _rgb_tuple(rgb):
    s = str(rgb)
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _is_decorative(name):
    name = (name or "").strip()
    return name.startswith(("Background", "Decoration", "PageNumber", "Footer"))


def _iter_runs(text_frame):
    for para in text_frame.paragraphs:
        for run in para.runs:
            yield para, run


def check(path):
    prs = Presentation(path)
    fails = []

    def fail(slide_num, msg):
        line = f"FAIL: {slide_num} — {msg}"
        print(line)
        fails.append(line)

    # ---- 1. Slide titles ----
    titles_ok = True
    for i, slide in enumerate(prs.slides, 1):
        has_title = False
        for shape in slide.shapes:
            name = _shape_name(shape)
            if name.startswith("Title") and shape.has_text_frame:
                if shape.text_frame.text.strip():
                    has_title = True
                    break
        if not has_title:
            fail(i, "missing or empty title placeholder")
            titles_ok = False
    if titles_ok:
        print("PASS: slide titles")

    # ---- 2. Reading order ----
    # Heuristic: when shapes are sorted top→bottom, left→right, the slide
    # title appears in the first quartile of that order. Decorative shapes
    # are excluded from the count.
    ro_ok = True
    for i, slide in enumerate(prs.slides, 1):
        shapes = [s for s in slide.shapes if not _is_decorative(_shape_name(s))]
        if not shapes:
            continue

        def sort_key(s):
            return ((s.top or 0), (s.left or 0))

        ordered = sorted(shapes, key=sort_key)
        title_pos = None
        for idx, s in enumerate(ordered):
            if _shape_name(s).startswith("Title"):
                title_pos = idx
                break
        if title_pos is None:
            fail(i, "no title shape found for reading order")
            ro_ok = False
            continue
        if title_pos > max(1, len(ordered) // 4):
            fail(i,
                 f"title not near top of reading order ({title_pos + 1}/{len(ordered)})")
            ro_ok = False
    if ro_ok:
        print("PASS: reading order")

    # ---- 3. Alt text ----
    alt_ok = True
    for i, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            name = _shape_name(shape)
            if _is_decorative(name):
                continue
            if shape.has_text_frame and shape.text_frame.text.strip():
                # Text content is its own accessible name.
                continue
            descr = _shape_descr(shape)
            if not descr.strip():
                fail(i, f"alt text missing on shape '{name}'")
                alt_ok = False
                continue
            if re.match(r"^(Picture|Image|Shape|Rectangle|Oval|Arrow)\s*\d*$",
                        name.strip()):
                fail(i, f"shape '{name}' has generic name")
                alt_ok = False
    if alt_ok:
        print("PASS: alt text")

    # ---- 4. Color contrast ----
    cc_ok = True
    seen_bad = set()
    for i, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for _, run in _iter_runs(shape.text_frame):
                try:
                    rgb = run.font.color.rgb
                except (AttributeError, TypeError):
                    rgb = None
                if rgb is None:
                    continue
                fg = _rgb_tuple(rgb)
                ratio = contrast_ratio(fg, BG_RGB)
                if ratio < 4.5:
                    key = (i, str(rgb))
                    if key not in seen_bad:
                        seen_bad.add(key)
                        fail(i,
                             f"contrast {ratio:.2f}:1 for text color #{rgb} "
                             f"(below 4.5:1)")
                        cc_ok = False
    if cc_ok:
        print("PASS: color contrast")

    # ---- 5. Tables ----
    tbl_ok = True
    for i, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if not shape.has_table:
                continue
            tbl = shape.table
            # python-pptx exposes first_row property on table for header.
            if not getattr(tbl, "first_row", False):
                fail(i, "table missing header-row marker (first_row)")
                tbl_ok = False
                continue
            # Verify title/summary on the underlying tbl element.
            tbl_el = shape.element.find(f".//{A_NS}tbl")
            if tbl_el is not None:
                tbl_pr = tbl_el.find(f"{A_NS}tblPr")
                if tbl_pr is None:
                    fail(i, "table missing tblPr (title/summary)")
                    tbl_ok = False
    if tbl_ok:
        print("PASS: tables")

    # ---- 6. Hyperlinks ----
    hl_ok = True
    for i, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for _, run in _iter_runs(shape.text_frame):
                hlink = run.hyperlink
                if hlink is None or hlink.address is None:
                    continue
                if not run.font.underline:
                    fail(i, f"hyperlink '{run.text[:24]}' not underlined")
                    hl_ok = False
    if hl_ok:
        print("PASS: hyperlinks")

    # ---- 7. Font size ----
    fs_ok = True
    fs_reports = 0
    for i, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            name = _shape_name(shape)
            if _is_decorative(name):
                continue
            if not shape.has_text_frame:
                continue
            for _, run in _iter_runs(shape.text_frame):
                size = run.font.size
                if size is None:
                    continue
                pts = size.pt
                if pts >= 18:
                    continue
                if pts >= 14 and run.font.bold:
                    continue
                if fs_reports < 5:
                    fail(i,
                         f"font {pts:g}pt on '{run.text[:32]}' below "
                         f"18pt body / 14pt bold minimum")
                    fs_reports += 1
                fs_ok = False
    if fs_ok:
        print("PASS: font sizes")

    # ---- 8. Notes-only content ----
    nt_ok = True
    for i, slide in enumerate(prs.slides, 1):
        if not slide.has_notes_slide:
            continue
        notes = slide.notes_slide.notes_text_frame.text.strip()
        if not notes:
            continue
        slide_text = " ".join(
            shape.text_frame.text
            for shape in slide.shapes
            if shape.has_text_frame
        )
        # Critical content only in notes if notes are substantial AND
        # slide visible text is too sparse to convey the message.
        if len(notes) > 200 and len(slide_text) < 100:
            fail(i, "speaker notes contain content not on the slide")
            nt_ok = False
    if nt_ok:
        print("PASS: notes content")

    if fails:
        print(f"\n{len(fails)} failure(s).")
        sys.exit(1)

    print("PASS: all 508 checks passed")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: check_508.py <path-to-pptx>", file=sys.stderr)
        sys.exit(2)
    check(sys.argv[1])
