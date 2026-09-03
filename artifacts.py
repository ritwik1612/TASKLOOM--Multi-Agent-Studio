from __future__ import annotations

import re
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from paths import resource_path


INK = colors.HexColor("#151526")
BLUE = colors.HexColor("#1026E8")
PAPER = colors.HexColor("#F7F4EC")
MUTED = colors.HexColor("#626173")
RULE = colors.HexColor("#D8DCFF")
FONT_DIR = resource_path("FONTS")
OLIVERA = "MAF Olivera"
PRODUCT_SANS = "MAF Product Sans"
PRODUCT_SANS_BOLD = "MAF Product Sans Bold"


def _register_fonts() -> None:
    if OLIVERA in pdfmetrics.getRegisteredFontNames():
        return
    pdfmetrics.registerFont(TTFont(OLIVERA, str(FONT_DIR / "Olivera_Demo.ttf")))
    pdfmetrics.registerFont(TTFont(PRODUCT_SANS, str(FONT_DIR / "product sans" / "product-sans-regular.ttf")))
    pdfmetrics.registerFont(TTFont(PRODUCT_SANS_BOLD, str(FONT_DIR / "product sans" / "product-sans-bold.ttf")))
    pdfmetrics.registerFontFamily(PRODUCT_SANS, normal=PRODUCT_SANS, bold=PRODUCT_SANS_BOLD)


def _inline_markup(text: str) -> str:
    """Convert the small Markdown subset emitted by the app into safe ReportLab markup."""
    safe = escape(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", safe)
    return safe.replace("  ", "&nbsp;&nbsp;")


def build_artifact_pdf(markdown_text: str, title: str = "TASKLOOM ARTIFACT") -> bytes:
    """Create a UI-themed, in-memory PDF for an accepted artifact."""
    _register_fonts()
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.82 * inch,
        leftMargin=0.82 * inch,
        topMargin=1.2 * inch,
        bottomMargin=0.82 * inch,
        title=title,
        author="Taskloom",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ArtifactTitle",
        parent=styles["Title"],
        fontName=OLIVERA,
        fontSize=24,
        leading=27,
        textColor=INK,
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "ArtifactHeading",
        parent=styles["Heading2"],
        fontName=OLIVERA,
        fontSize=16,
        leading=19,
        textColor=BLUE,
        spaceBefore=13,
        spaceAfter=7,
    )
    body_style = ParagraphStyle(
        "ArtifactBody",
        parent=styles["BodyText"],
        fontName=PRODUCT_SANS,
        fontSize=10.8,
        leading=16,
        textColor=INK,
        spaceAfter=9,
    )
    bullet_style = ParagraphStyle(
        "ArtifactBullet",
        parent=body_style,
        leftIndent=18,
        firstLineIndent=-11,
        bulletColor=BLUE,
    )

    story = [Paragraph(_inline_markup(title), title_style)]
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 5))
            continue
        if match := re.match(r"^#{1,6}\s+(.+)$", line):
            story.append(Paragraph(_inline_markup(match.group(1)), heading_style))
        elif match := re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)(.+)$", line):
            story.append(Paragraph(_inline_markup(match.group(1)), bullet_style, bulletText="-"))
        else:
            story.append(Paragraph(_inline_markup(line), body_style))

    def add_page_furniture(canvas, doc) -> None:
        canvas.saveState()
        width, height = letter
        canvas.setFillColor(PAPER)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.8)
        canvas.line(document.leftMargin, height - 0.58 * inch, width - document.rightMargin, height - 0.58 * inch)
        canvas.setStrokeColor(BLUE)
        canvas.setLineWidth(1.1)
        canvas.line(width - 1.55 * inch, height - 0.45 * inch, width - 0.86 * inch, height - 0.31 * inch)
        canvas.circle(width - 0.84 * inch, height - 0.3 * inch, 2.3, fill=1, stroke=0)
        canvas.setFillColor(INK)
        canvas.setFont(OLIVERA, 11)
        canvas.drawString(document.leftMargin, height - 0.39 * inch, "TASKLOOM")
        canvas.setFillColor(MUTED)
        canvas.setFont(PRODUCT_SANS_BOLD, 6.8)
        canvas.drawString(document.leftMargin + 0.86 * inch, height - 0.385 * inch, "MULTI-AGENT LANGUAGE STUDIO")
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.8)
        canvas.line(document.leftMargin, 0.54 * inch, width - document.rightMargin, 0.54 * inch)
        canvas.setFillColor(MUTED)
        canvas.setFont(PRODUCT_SANS, 8)
        canvas.drawString(document.leftMargin, 0.33 * inch, "ONE TASK. MANY MINDS.")
        canvas.drawRightString(width - document.rightMargin, 0.33 * inch, f"PAGE {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=add_page_furniture, onLaterPages=add_page_furniture)
    return buffer.getvalue()
