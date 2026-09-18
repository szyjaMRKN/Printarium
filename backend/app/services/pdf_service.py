"""Generowanie PDF po stronie serwera (raporty i dokumenty sprzedaży)."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import get_settings
from app.core.dates import format_pl_date
from app.core.money import format_pln
from app.core.version import APP_NAME, APP_VERSION
from app.models.enums import label as enum_label

FONT_CANDIDATES = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/TTF/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"),
    (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ),
]

ASCII_FALLBACK = str.maketrans(
    {
        "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o", "ś": "s", "ź": "z", "ż": "z",
        "Ą": "A", "Ć": "C", "Ę": "E", "Ł": "L", "Ń": "N", "Ó": "O", "Ś": "S", "Ź": "Z", "Ż": "Z",
    }
)


@lru_cache
def _fonts() -> tuple[str, str, bool]:
    """Zwraca (font, font_bold, czy_obsluguje_polskie_znaki)."""
    settings = get_settings()
    candidates = list(FONT_CANDIDATES)
    if settings.pdf_font_path:
        bold_guess = settings.pdf_font_path.replace(".ttf", "-Bold.ttf")
        candidates.insert(0, (settings.pdf_font_path, bold_guess))
    for regular, bold in candidates:
        if Path(regular).exists():
            pdfmetrics.registerFont(TTFont("AppFont", regular))
            bold_name = "AppFont"
            if Path(bold).exists():
                pdfmetrics.registerFont(TTFont("AppFont-Bold", bold))
                bold_name = "AppFont-Bold"
            return "AppFont", bold_name, True
    # Awaryjnie fonty wbudowane — bez polskich znaków, więc tekst jest transliterowany.
    return "Helvetica", "Helvetica-Bold", False


def safe_text(value: object) -> str:
    text = "" if value is None else str(value)
    if not _fonts()[2]:
        return text.translate(ASCII_FALLBACK)
    return text


def _styles() -> dict[str, ParagraphStyle]:
    font, font_bold, _ = _fonts()
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName=font_bold, fontSize=16, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=font_bold, fontSize=11, spaceAfter=4),
        "normal": ParagraphStyle("normal", parent=base["Normal"], fontName=font, fontSize=9, leading=12),
        "small": ParagraphStyle("small", parent=base["Normal"], fontName=font, fontSize=7.5, leading=10,
                                textColor=colors.HexColor("#555555")),
        "right": ParagraphStyle("right", parent=base["Normal"], fontName=font, fontSize=9, alignment=TA_RIGHT),
        "right_bold": ParagraphStyle(
            "right_bold", parent=base["Normal"], fontName=font_bold, fontSize=10, alignment=TA_RIGHT
        ),
    }


def _format_cell(value: object, kind: str) -> str:
    if kind == "money":
        return format_pln(int(value or 0))
    if kind == "date":
        if isinstance(value, date):
            return format_pl_date(value)
        return safe_text(value)
    if kind == "int":
        return str(int(value or 0))
    if isinstance(value, str):
        return safe_text(enum_label(value) if value.islower() and "_" in value else value)
    return safe_text(value)


def _table_style(font: str, font_bold: str) -> TableStyle:
    return TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, 0), font_bold),
            ("FONTNAME", (0, 1), (-1, -1), font),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )


def build_report_pdf(report, *, period_label: str = "") -> bytes:
    """Raport tabelaryczny w PDF."""
    from io import BytesIO

    font, font_bold, _ = _fonts()
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4) if len(report.columns) > 6 else A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=safe_text(report.title),
        author=safe_text(APP_NAME),
    )

    story = [Paragraph(safe_text(report.title), styles["title"])]
    if period_label:
        story.append(Paragraph(safe_text(f"Okres: {period_label}"), styles["normal"]))
    story.append(Spacer(1, 6))

    header = [Paragraph(safe_text(title), styles["normal"]) for _, title, _ in report.columns]
    data = [header]
    for row in report.rows:
        data.append(
            [
                Paragraph(_format_cell(row.get(key), kind), styles["normal"])
                for key, _, kind in report.columns
            ]
        )
    if not report.rows:
        data.append([Paragraph(safe_text("Brak danych w wybranym okresie."), styles["normal"])] +
                    [""] * (len(report.columns) - 1))

    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(_table_style(font, font_bold))
    story.append(table)

    if report.summary:
        story.append(Spacer(1, 8))
        for key, value in report.summary.items():
            title = next((col[1] for col in report.columns if col[0] == key), key)
            story.append(Paragraph(safe_text(f"Razem — {title}: {format_pln(value)}"), styles["right_bold"]))

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            safe_text(
                f"Wygenerowano w aplikacji {APP_NAME} {APP_VERSION}. "
                "Dokument pomocniczy — nie zastępuje porady podatkowej."
            ),
            styles["small"],
        )
    )
    doc.build(story)
    return buffer.getvalue()


def build_document_pdf(document) -> bytes:
    """Rachunek / faktura bez VAT."""
    from io import BytesIO

    font, font_bold, _ = _fonts()
    styles = _styles()
    seller = document.seller_snapshot or {}
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=safe_text(f"{enum_label(document.document_type)} {document.number}"),
        author=safe_text(seller.get("name") or APP_NAME),
    )

    title = f"{enum_label(document.document_type).upper()} nr {document.number}"
    story = [Paragraph(safe_text(title), styles["title"])]
    story.append(
        Paragraph(
            safe_text(
                f"Data wystawienia: {format_pl_date(document.issue_date)}  |  "
                f"Data sprzedaży: {format_pl_date(document.sale_date)}"
                + (f"  |  Termin płatności: {format_pl_date(document.due_date)}" if document.due_date else "")
            ),
            styles["normal"],
        )
    )
    story.append(Spacer(1, 10))

    seller_lines = [
        seller.get("name", ""),
        seller.get("address", ""),
        " ".join(part for part in (seller.get("postal_code", ""), seller.get("city", "")) if part),
        f"NIP: {seller.get('nip')}" if seller.get("nip") else "",
        seller.get("email", ""),
        seller.get("phone", ""),
    ]
    buyer_lines = [
        document.buyer_name,
        document.buyer_address or "",
        f"NIP: {document.buyer_nip}" if document.buyer_nip else "",
        document.buyer_email or "",
    ]
    parties = Table(
        [
            [Paragraph(safe_text("Sprzedawca"), styles["h2"]), Paragraph(safe_text("Nabywca"), styles["h2"])],
            [
                Paragraph(safe_text("<br/>".join(line for line in seller_lines if line)), styles["normal"]),
                Paragraph(safe_text("<br/>".join(line for line in buyer_lines if line)), styles["normal"]),
            ],
        ],
        colWidths=[85 * mm, 85 * mm],
    )
    parties.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(parties)
    story.append(Spacer(1, 10))

    data = [
        [
            Paragraph(safe_text(text), styles["normal"])
            for text in ("Lp.", "Nazwa", "Ilość", "J.m.", "Cena", "Wartość")
        ]
    ]
    for index, item in enumerate(document.items_snapshot or [], start=1):
        data.append(
            [
                Paragraph(str(index), styles["normal"]),
                Paragraph(safe_text(item.get("name", "")), styles["normal"]),
                Paragraph(str(item.get("quantity", 0)), styles["normal"]),
                Paragraph(safe_text(item.get("unit", "szt.")), styles["normal"]),
                Paragraph(format_pln(int(item.get("unit_price_gr", 0))), styles["normal"]),
                Paragraph(format_pln(int(item.get("total_gr", 0))), styles["normal"]),
            ]
        )
    table = Table(data, colWidths=[12 * mm, 74 * mm, 16 * mm, 14 * mm, 28 * mm, 30 * mm], repeatRows=1)
    table.setStyle(_table_style(font, font_bold))
    story.append(table)
    story.append(Spacer(1, 8))
    story.append(Paragraph(safe_text(f"Razem do zapłaty: {format_pln(document.total_gr)}"), styles["right_bold"]))

    details = []
    if document.payment_method:
        details.append(f"Forma płatności: {enum_label(document.payment_method)}")
    if seller.get("bank_account"):
        details.append(f"Numer rachunku: {seller['bank_account']}")
    if document.paid_note:
        details.append(document.paid_note)
    if document.ksef_number:
        details.append(f"Numer KSeF: {document.ksef_number}")
    elif document.ksef_status and document.ksef_status != "nie_dotyczy":
        details.append(f"KSeF: {enum_label(document.ksef_status)}")
    if document.notes:
        details.append(document.notes)
    if seller.get("footer_note"):
        details.append(seller["footer_note"])

    if details:
        story.append(Spacer(1, 8))
        story.append(
            KeepTogether(
                [Paragraph(safe_text(line), styles["normal"]) for line in details]
            )
        )

    story.append(Spacer(1, 16))
    signatures = Table(
        [
            [
                Paragraph(safe_text("..............................<br/>Podpis osoby upoważnionej do wystawienia"), styles["small"]),
                Paragraph(safe_text("..............................<br/>Podpis osoby upoważnionej do odbioru"), styles["small"]),
            ]
        ],
        colWidths=[85 * mm, 85 * mm],
    )
    story.append(signatures)
    doc.build(story)
    return buffer.getvalue()
