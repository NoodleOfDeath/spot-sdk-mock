"""Append slides 11-16 to spot_interview.pptx.

Re-runnable: if the deck already has >=16 slides, deletes everything from
slide 11 onward before appending so the script can be edited and re-run.
"""
from __future__ import annotations

import copy
import sys

from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn


WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BG = RGBColor(0x1A, 0x1A, 0x2E)
BD_BLUE = RGBColor(0x00, 0x57, 0xB8)
# Lighter variant used for accent *text* — pure BD_BLUE on bg #1A1A2E only
# yields 2.48:1 contrast (below WCAG 4.5:1). BD_BLUE is fine for shape fills.
ACCENT_TEXT = RGBColor(0x6F, 0xB4, 0xFF)
AMBER = RGBColor(0xF5, 0x9E, 0x0B)
MUTED = RGBColor(0xC9, 0xD1, 0xD9)


def set_alt_text(shape, descr: str) -> None:
    """Set the descr attribute on the cNvPr element so check_508 picks it up."""
    cnvpr = shape._element.find(".//" + qn("p:cNvPr"))
    if cnvpr is None:
        cnvpr = shape._element.find(".//" + qn("a:cNvPr"))
    if cnvpr is not None:
        cnvpr.set("descr", descr)


def rename(shape, name: str) -> None:
    cnvpr = shape._element.find(".//" + qn("p:cNvPr"))
    if cnvpr is None:
        cnvpr = shape._element.find(".//" + qn("a:cNvPr"))
    if cnvpr is not None:
        cnvpr.set("name", name)


def add_bg(slide, idx: int) -> None:
    """Solid background rectangle. Named Background N so check_508 skips it."""
    rect = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Emu(0), Emu(0), Emu(12191695), Emu(6858000)
    )
    rect.line.fill.background()
    rect.fill.solid()
    rect.fill.fore_color.rgb = BG
    rename(rect, f"Background {idx}")
    set_alt_text(rect, "Decorative background")


def add_title(slide, idx: int, text: str) -> None:
    box = slide.shapes.add_textbox(Emu(548640), Emu(457200), Emu(11094415), Emu(640080))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = text
    r.font.size = Pt(32)
    r.font.bold = True
    r.font.color.rgb = WHITE
    rename(box, f"Title {idx}: {text}")


def add_text(
    slide,
    idx: int,
    top: int,
    left: int,
    width: int,
    height: int,
    paragraphs,
    *,
    name_hint: str,
    align=PP_ALIGN.LEFT,
    default_pt=18,
    default_bold=False,
    default_color=WHITE,
    default_font=None,
    descr: str | None = None,
) -> "Shape":
    """Add a text box. ``paragraphs`` is a list of:
      - str → single run with defaults
      - dict {text, size, bold, color, font, indent} for per-paragraph control
      - list[dict] → multiple runs in one paragraph
    """
    box = slide.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    for i, item in enumerate(paragraphs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        runs = item if isinstance(item, list) else [item]
        for r_item in runs:
            if isinstance(r_item, str):
                r_item = {"text": r_item}
            r = p.add_run()
            r.text = r_item["text"]
            r.font.size = Pt(r_item.get("size", default_pt))
            r.font.bold = r_item.get("bold", default_bold)
            r.font.color.rgb = r_item.get("color", default_color)
            font_name = r_item.get("font", default_font)
            if font_name:
                r.font.name = font_name
    rename(box, f"Body {idx}: {name_hint}")
    if descr:
        set_alt_text(box, descr)
    return box


def add_rect(
    slide,
    idx: int,
    *,
    top: int,
    left: int,
    width: int,
    height: int,
    fill_rgb,
    line_rgb=None,
    line_width_pt=0,
    name_hint: str = "decoration",
    descr: str = "Decorative shape",
) -> "Shape":
    rect = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Emu(left), Emu(top), Emu(width), Emu(height)
    )
    rect.fill.solid()
    rect.fill.fore_color.rgb = fill_rgb
    if line_rgb is not None:
        rect.line.color.rgb = line_rgb
        rect.line.width = Pt(line_width_pt)
    else:
        rect.line.fill.background()
    # Names that start with Background/Decoration/PageNumber/Footer are skipped
    # by check_508's alt-text + reading-order checks. We use "Decoration".
    rename(rect, f"Decoration {idx}: {name_hint}")
    set_alt_text(rect, descr)
    return rect


def add_page_number(slide, idx: int, total: int = 16) -> None:
    box = slide.shapes.add_textbox(Emu(11400000), Emu(6492240), Emu(680000), Emu(280000))
    tf = box.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    r = p.add_run()
    r.text = f"{idx} / {total}"
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = MUTED
    rename(box, f"PageNumber {idx}")


# --- per-slide builders ------------------------------------------------------


def build_slide_11(p):
    blank = p.slide_layouts[6]
    slide = p.slides.add_slide(blank)
    add_bg(slide, 11)
    add_title(slide, 11, "The Evolved Stack")

    tree = (
        "spot-mock-stack/\n"
        "├── vendor/spot-sdk/           # git submodule — never modified\n"
        "├── mocks/\n"
        "│   ├── robot_mock/            # Python gRPC mock (stub→mock→sim spectrum)\n"
        "│   │   ├── servicers/         # one file per service\n"
        "│   │   └── tests/             # robot_mock unit tests only\n"
        "│   ├── api_mock/              # Express/TS — dynamic test discovery\n"
        "│   └── web_mock/              # React + Vite + Three.js + Redux\n"
        "├── conftest.py                # root shim: --mock flag, channel injection\n"
        "├── pytest.ini                 # pythonpath for upstream helpers.py imports\n"
        "├── docker-compose.yml\n"
        "├── k8s/                       # Deployments + Services + Ingress\n"
        "└── tests/playwright/          # E2E smoke + mission_smoke + gui_smoke"
    )
    add_text(
        slide, 11,
        top=1280000, left=548640, width=11094415, height=4400000,
        paragraphs=[
            {"text": line, "font": "Menlo", "size": 14, "bold": True}
            for line in tree.splitlines()
        ],
        name_hint="filesystem tree", default_font="Menlo",
        default_pt=14, default_bold=True,
    )
    add_text(
        slide, 11,
        top=5900000, left=548640, width=11094415, height=420000,
        paragraphs=[
            [
                {"text": "→  ", "color": ACCENT_TEXT, "bold": True, "size": 16},
                {"text": "vendor/spot-sdk is read-only. All shim logic lives at the repo root.", "bold": True, "size": 16},
            ]
        ],
        name_hint="callout",
    )
    add_page_number(slide, 11)


def build_slide_12(p):
    blank = p.slide_layouts[6]
    slide = p.slides.add_slide(blank)
    add_bg(slide, 12)
    add_title(slide, 12, "Testing Infrastructure")

    columns = [
        (
            "Unit",
            "pytest mocks/robot_mock/tests/ -v",
            "Tests the mock's own behavior in isolation. Fast, deterministic, hits no network.",
        ),
        (
            "SDK Integration",
            "pytest vendor/spot-sdk/.../tests/ -v --mock",
            "Upstream tests, zero modifications. Channel-injected via root conftest.py. "
            "MockChannel-style tests auto-handled via pytest_collection_modifyitems.",
        ),
        (
            "E2E",
            "npx playwright test",
            "GUI loads, test cards render, SSE streams pytest output, RobotViewer animates, "
            "Run All Tests button drives the full suite.",
        ),
    ]
    col_w = 3650000
    gap = 200000
    base_left = 548640
    for i, (heading, cmd, body) in enumerate(columns):
        x = base_left + i * (col_w + gap)
        add_rect(
            slide, 12,
            top=1280000, left=x, width=col_w, height=4400000,
            fill_rgb=RGBColor(0x22, 0x22, 0x3E),
            line_rgb=BD_BLUE, line_width_pt=1,
            name_hint=f"{heading} card",
        )
        add_text(
            slide, 12,
            top=1380000, left=x + 180000, width=col_w - 360000, height=420000,
            paragraphs=[heading],
            name_hint=f"{heading} heading",
            default_pt=22, default_bold=True, default_color=ACCENT_TEXT,
        )
        add_text(
            slide, 12,
            top=1820000, left=x + 180000, width=col_w - 360000, height=600000,
            paragraphs=[{"text": cmd, "font": "Menlo", "size": 14, "bold": True}],
            name_hint=f"{heading} cmd", default_font="Menlo",
            default_pt=14, default_bold=True,
        )
        add_text(
            slide, 12,
            top=2520000, left=x + 180000, width=col_w - 360000, height=3000000,
            paragraphs=[body],
            name_hint=f"{heading} body",
            default_pt=18, default_bold=True,
        )

    add_text(
        slide, 12,
        top=5900000, left=548640, width=11094415, height=420000,
        paragraphs=[
            [
                {"text": "→  ", "color": ACCENT_TEXT, "bold": True, "size": 16},
                {"text": "Submodule is the source of truth. Copy-paste drift is eliminated.", "bold": True, "size": 16},
            ]
        ],
        name_hint="callout",
    )
    add_page_number(slide, 12)


def build_slide_13(p):
    blank = p.slide_layouts[6]
    slide = p.slides.add_slide(blank)
    add_bg(slide, 13)
    add_title(slide, 13, "k8s Deployment")

    services = [
        ("robot-mock", "Deployment + Service", "Port 44444 (gRPC)", "MOCK_ROBOT_PORT"),
        ("api-mock", "Deployment + Service", "Port 3001 (HTTP)", "ROBOT_MOCK_HOST · ROBOT_MOCK_PORT"),
        ("web-mock", "Deployment + Service", "Port 4000 (HTTP)", "VITE_API_BASE"),
    ]
    col_w = 3650000
    gap = 200000
    base_left = 548640
    for i, (svc, kind, port, env) in enumerate(services):
        x = base_left + i * (col_w + gap)
        add_rect(
            slide, 13,
            top=1280000, left=x, width=col_w, height=2400000,
            fill_rgb=RGBColor(0x22, 0x22, 0x3E),
            line_rgb=BD_BLUE, line_width_pt=1,
            name_hint=f"{svc} card",
        )
        add_text(
            slide, 13,
            top=1360000, left=x + 180000, width=col_w - 360000, height=480000,
            paragraphs=[svc],
            name_hint=f"{svc} heading",
            default_pt=24, default_bold=True, default_color=ACCENT_TEXT,
            default_font="Menlo",
        )
        add_text(
            slide, 13,
            top=1880000, left=x + 180000, width=col_w - 360000, height=1700000,
            paragraphs=[kind, port, env],
            name_hint=f"{svc} details",
            default_pt=18, default_bold=True,
        )

    add_text(
        slide, 13,
        top=3920000, left=548640, width=11094415, height=380000,
        paragraphs=["Ingress routing"],
        name_hint="ingress heading",
        default_pt=20, default_bold=True, default_color=ACCENT_TEXT,
    )
    ingress = [
        "/      →  web-mock:4000",
        "/api   →  api-mock:3001",
        "gRPC   →  robot-mock:44444    (sidecar via internal service DNS)",
    ]
    add_text(
        slide, 13,
        top=4360000, left=548640, width=11094415, height=1400000,
        paragraphs=[{"text": row, "font": "Menlo", "size": 16, "bold": True} for row in ingress],
        name_hint="ingress table", default_font="Menlo",
        default_pt=16, default_bold=True,
    )

    add_text(
        slide, 13,
        top=5900000, left=548640, width=11094415, height=420000,
        paragraphs=[
            [
                {"text": "→  ", "color": ACCENT_TEXT, "bold": True, "size": 16},
                {"text": "Same docker-compose services. Production-ready topology, no rewrite.", "bold": True, "size": 16},
            ]
        ],
        name_hint="callout",
    )
    add_page_number(slide, 13)


def build_slide_14(p):
    blank = p.slide_layouts[6]
    slide = p.slides.add_slide(blank)
    add_bg(slide, 14)
    add_title(slide, 14, "Stub  →  Mock  →  Simulation")

    add_text(
        slide, 14,
        top=1280000, left=548640, width=11094415, height=440000,
        paragraphs=["Not all services are equal — and they shouldn't be."],
        name_hint="subtitle",
        default_pt=20, default_bold=True, default_color=MUTED,
    )

    # Gradient-ish: 5 stops along a single bar.
    bar_top = 2200000
    bar_left = 700000
    bar_total = 10800000
    seg_w = bar_total // 5
    blues = [
        RGBColor(0x10, 0x28, 0x58),
        RGBColor(0x00, 0x47, 0x95),
        RGBColor(0x00, 0x57, 0xB8),
        RGBColor(0x33, 0x7B, 0xCC),
        RGBColor(0x66, 0x99, 0xDD),
    ]
    for i, c in enumerate(blues):
        add_rect(
            slide, 14,
            top=bar_top, left=bar_left + i * seg_w, width=seg_w, height=120000,
            fill_rgb=c, name_hint=f"spectrum stop {i+1}",
        )

    stops = [
        (bar_left + 60000, "Stub", "RobotId · Auth · Directory"),
        (bar_left + seg_w * 1 - 80000, "↔", "TimeSync"),
        (bar_left + seg_w * 2 - 80000, "Mock", "EStop · Lease · Power · Mission"),
        (bar_left + seg_w * 3 - 80000, "↔", "RobotCommand (trot gait)"),
        (bar_left + seg_w * 4 - 60000, "Simulation", "kinematics · battery drain (future)"),
    ]
    for x, label, body in stops:
        add_text(
            slide, 14,
            top=bar_top + 220000, left=x, width=seg_w, height=400000,
            paragraphs=[label],
            name_hint=f"label {label}",
            default_pt=20, default_bold=True, default_color=ACCENT_TEXT,
            align=PP_ALIGN.LEFT,
        )
        add_text(
            slide, 14,
            top=bar_top + 660000, left=x, width=seg_w + 80000, height=2400000,
            paragraphs=body.split(" · "),
            name_hint=f"items {label}",
            default_pt=16, default_bold=True,
        )

    add_text(
        slide, 14,
        top=5900000, left=548640, width=11094415, height=420000,
        paragraphs=[
            [
                {"text": "→  ", "color": ACCENT_TEXT, "bold": True, "size": 16},
                {"text": "The signal: does it update itself without being asked?", "bold": True, "size": 16},
            ]
        ],
        name_hint="callout",
    )
    add_page_number(slide, 14)


def build_slide_15(p):
    blank = p.slide_layouts[6]
    slide = p.slides.add_slide(blank)
    add_bg(slide, 15)
    add_title(slide, 15, "Human in the Loop — My Observations")

    # Amber instruction box
    add_rect(
        slide, 15,
        top=1280000, left=548640, width=11094415, height=720000,
        fill_rgb=RGBColor(0x2A, 0x22, 0x12),
        line_rgb=AMBER, line_width_pt=2,
        name_hint="instruction frame",
        descr="Amber-bordered instruction frame",
    )
    add_text(
        slide, 15,
        top=1380000, left=720000, width=10850000, height=540000,
        paragraphs=[
            [
                {"text": "Fill this slide out after your first solo review pass — ", "bold": True, "size": 18},
                {"text": "these are your words, not Claude's.", "bold": True, "size": 18, "color": AMBER},
            ]
        ],
        name_hint="instruction text",
    )

    prompts = [
        ("What Claude got right first try", "[your notes here]"),
        ("What needed correction and why", "[your notes here]"),
        ("Where the abstraction leaked", "[your notes here]"),
        ("What I'd architect differently", "[your notes here]"),
    ]
    col_w = (12191695 - 548640 * 2 - 200000) // 2
    row_h = 1700000
    for i, (heading, body) in enumerate(prompts):
        col = i % 2
        row = i // 2
        x = 548640 + col * (col_w + 200000)
        y = 2160000 + row * (row_h + 120000)
        add_rect(
            slide, 15,
            top=y, left=x, width=col_w, height=row_h,
            fill_rgb=RGBColor(0x22, 0x22, 0x3E),
            line_rgb=BD_BLUE, line_width_pt=1,
            name_hint=f"prompt frame {i+1}",
        )
        add_text(
            slide, 15,
            top=y + 80000, left=x + 160000, width=col_w - 320000, height=480000,
            paragraphs=[heading],
            name_hint=f"prompt heading {i+1}",
            default_pt=18, default_bold=True, default_color=ACCENT_TEXT,
        )
        add_text(
            slide, 15,
            top=y + 560000, left=x + 160000, width=col_w - 320000, height=row_h - 640000,
            paragraphs=[body],
            name_hint=f"prompt body {i+1}",
            default_pt=16, default_bold=True, default_color=MUTED,
        )

    add_text(
        slide, 15,
        top=5900000, left=548640, width=11094415, height=420000,
        paragraphs=[
            [
                {"text": "→  ", "color": ACCENT_TEXT, "bold": True, "size": 16},
                {"text": "A seasoned engineer's review is not optional — it's the last RALPH cycle.", "bold": True, "size": 16},
            ]
        ],
        name_hint="callout",
    )
    add_page_number(slide, 15)


def build_slide_16(p):
    blank = p.slide_layouts[6]
    slide = p.slides.add_slide(blank)
    add_bg(slide, 16)
    add_title(slide, 16, "Q & A")

    add_text(
        slide, 16,
        top=1400000, left=548640, width=11094415, height=900000,
        paragraphs=["Questions?"],
        name_hint="questions",
        default_pt=48, default_bold=True,
        align=PP_ALIGN.CENTER,
    )

    add_text(
        slide, 16,
        top=2580000, left=548640, width=11094415, height=440000,
        paragraphs=["Seeds to get us started"],
        name_hint="seeds heading",
        default_pt=20, default_bold=True, default_color=ACCENT_TEXT,
        align=PP_ALIGN.CENTER,
    )

    bullets = [
        "How does the submodule strategy keep mock tests in sync with SDK releases?",
        "Where on the stub→mock→sim spectrum does robot_mock need to go for your use case?",
        "What would it take to run this stack on actual HIL hardware instead of the mock?",
        "How does the /goal-driven workflow change code review responsibilities?",
    ]
    add_text(
        slide, 16,
        top=3120000, left=900000, width=10391695, height=2200000,
        paragraphs=[f"·  {b}" for b in bullets],
        name_hint="bullets",
        default_pt=18, default_bold=True,
    )

    add_text(
        slide, 16,
        top=5900000, left=548640, width=11094415, height=300000,
        paragraphs=["tmorgan@bostondynamics.com   ·   GitHub: @tmorgan-bd"],
        name_hint="contact",
        default_pt=16, default_bold=True, default_color=MUTED,
        align=PP_ALIGN.RIGHT,
    )

    add_page_number(slide, 16)


# --- driver -----------------------------------------------------------------


def remove_trailing_slides(p, keep: int) -> None:
    while len(p.slides) > keep:
        sld_lst = p.slides._sldIdLst
        last = list(sld_lst)[-1]
        rId = last.get(qn("r:id"))
        p.part.drop_rel(rId)
        sld_lst.remove(last)


def main(path: str) -> int:
    p = Presentation(path)
    remove_trailing_slides(p, 10)
    build_slide_11(p)
    build_slide_12(p)
    build_slide_13(p)
    build_slide_14(p)
    build_slide_15(p)
    build_slide_16(p)
    p.save(path)
    print(f"saved {path} with {len(p.slides)} slides")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "spot_interview.pptx"))
