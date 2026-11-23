"""Deterministic Instagram job card renderer (Phase 29, IMAG-02/D-01..D-08).

Renders 1080x1350 JPEG sRGB cards from Job data only. No contacts, no upload/logo,
no timestamps/random IDs. Bundled fonts only.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

CARD_TEMPLATE_VERSION = "ig-card-v1"
CARD_WIDTH = 1080
CARD_HEIGHT = 1350
CARD_BG = "#0f0a1a"
CARD_SURFACE = "#1a1025"
CARD_PURPLE = "#8b5cf6"
CARD_PURPLE_SOFT = "#a78bfa"
CARD_TEXT = "#e2e8f0"
CARD_MUTED = "#b8a9cc"
MAX_BYTES = 8 * 1024 * 1024

_FONT_REGULAR_NAME = "DejaVuSans.ttf"
_FONT_BOLD_NAME = "DejaVuSans-Bold.ttf"


def get_bundled_font_paths() -> tuple[Path, Path]:
    """Return absolute paths to bundled DejaVu fonts.

    Raises:
        FileNotFoundError: with clear internal error if bundled fonts are missing.
    """
    fonts_dir = Path(__file__).resolve().parents[3] / "assets" / "fonts"
    regular = fonts_dir / _FONT_REGULAR_NAME
    bold = fonts_dir / _FONT_BOLD_NAME
    missing = [str(p) for p in (regular, bold) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Bundled IG card fonts missing; rendering requires repo-bundled fonts only: "
            + ", ".join(missing)
        )
    return regular, bold


def _load_font(path: str | Path, size: int) -> ImageFont.FreeTypeFont:
    font_path = Path(path)
    if not font_path.exists():
        raise FileNotFoundError(
            f"Bundled IG card font missing: {font_path}. Bundled fonts only; no fallback."
        )
    return ImageFont.truetype(str(font_path), size=size)


def _text_or_empty(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    words = normalized.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width or not current:
            if width <= max_width:
                current = candidate
            else:
                # Hard-wrap very long tokens deterministically by characters.
                if current:
                    lines.append(current)
                    current = ""
                chunk = ""
                for ch in word:
                    cand2 = chunk + ch
                    b2 = draw.textbbox((0, 0), cand2, font=font)
                    if (b2[2] - b2[0]) <= max_width or not chunk:
                        chunk = cand2
                    else:
                        lines.append(chunk)
                        chunk = ch
                current = chunk
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    x: int,
    y: int,
    max_width: int,
    font: ImageFont.ImageFont,
    fill: str,
    line_spacing: int = 8,
    max_lines: int | None = None,
) -> int:
    lines = _wrap_text(draw, text, font, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            last = lines[-1]
            ellipsis = "…"
            while last:
                candidate = f"{last.rstrip()} {ellipsis}".strip()
                bbox = draw.textbbox((0, 0), candidate, font=font)
                if (bbox[2] - bbox[0]) <= max_width:
                    lines[-1] = candidate
                    break
                last = last[:-1]
            else:
                lines[-1] = ellipsis
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), line, font=font)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y


def _collect_card_lines(job: Any) -> dict[str, str]:
    title = _text_or_empty(getattr(job, "title", None)) or "Vaga"
    company = _text_or_empty(getattr(job, "company", None))
    city = _text_or_empty(getattr(job, "city", None))
    contract_type = _text_or_empty(
        getattr(job, "contract_type", None)
        or getattr(job, "employment", None)
        or getattr(job, "type", None)
    )
    salary = _text_or_empty(getattr(job, "salary", None))
    return {
        "title": title,
        "company": company,
        "city": city,
        "contract_type": contract_type,
        "salary": salary,
    }


def render_ig_card(job: Any, *, font_regular_path: str | Path, font_bold_path: str | Path) -> bytes:
    """Render a deterministic 1080x1350 JPEG Instagram card.

    The card contains essential job info only (D-07) and never includes contacts.
    """
    regular_path = Path(font_regular_path)
    bold_path = Path(font_bold_path)
    if not regular_path.exists() or not bold_path.exists():
        missing = [str(p) for p in (regular_path, bold_path) if not p.exists()]
        raise FileNotFoundError(
            "Bundled IG card fonts missing; rendering requires repo-bundled fonts only: "
            + ", ".join(missing)
        )

    img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), CARD_BG)
    draw = ImageDraw.Draw(img)

    # Surface panel
    panel_margin = 56
    panel_top = 180
    panel_bottom = CARD_HEIGHT - 120
    draw.rounded_rectangle(
        [panel_margin, panel_top, CARD_WIDTH - panel_margin, panel_bottom],
        radius=28,
        fill=CARD_SURFACE,
        outline=CARD_PURPLE,
        width=2,
    )

    font_brand = _load_font(bold_path, 44)
    font_kicker = _load_font(regular_path, 30)
    font_title = _load_font(bold_path, 64)
    font_body = _load_font(regular_path, 36)
    font_body_bold = _load_font(bold_path, 36)
    font_cta = _load_font(bold_path, 42)
    font_footer = _load_font(regular_path, 28)

    # Header brand
    draw.text((panel_margin, 72), "EmpregaNoix", font=font_brand, fill=CARD_PURPLE_SOFT)
    draw.text((panel_margin, 124), "Vaga de emprego", font=font_kicker, fill=CARD_MUTED)

    data = _collect_card_lines(job)
    content_x = panel_margin + 48
    content_w = CARD_WIDTH - (content_x * 2)
    y = panel_top + 56

    y = _draw_wrapped(
        draw,
        data["title"],
        x=content_x,
        y=y,
        max_width=content_w,
        font=font_title,
        fill=CARD_TEXT,
        line_spacing=12,
        max_lines=4,
    )
    y += 20

    if data["company"]:
        draw.text((content_x, y), "Empresa", font=font_kicker, fill=CARD_MUTED)
        y += 42
        y = _draw_wrapped(
            draw,
            data["company"],
            x=content_x,
            y=y,
            max_width=content_w,
            font=font_body_bold,
            fill=CARD_TEXT,
            line_spacing=8,
            max_lines=2,
        )
        y += 18

    if data["city"]:
        draw.text((content_x, y), "Local", font=font_kicker, fill=CARD_MUTED)
        y += 42
        y = _draw_wrapped(
            draw,
            data["city"],
            x=content_x,
            y=y,
            max_width=content_w,
            font=font_body,
            fill=CARD_TEXT,
            line_spacing=8,
            max_lines=2,
        )
        y += 18

    if data["contract_type"]:
        draw.text((content_x, y), "Tipo / contrato", font=font_kicker, fill=CARD_MUTED)
        y += 42
        y = _draw_wrapped(
            draw,
            data["contract_type"],
            x=content_x,
            y=y,
            max_width=content_w,
            font=font_body,
            fill=CARD_TEXT,
            line_spacing=8,
            max_lines=2,
        )
        y += 18

    if data["salary"]:
        draw.text((content_x, y), "Salário", font=font_kicker, fill=CARD_MUTED)
        y += 42
        _draw_wrapped(
            draw,
            data["salary"],
            x=content_x,
            y=y,
            max_width=content_w,
            font=font_body,
            fill=CARD_TEXT,
            line_spacing=8,
            max_lines=3,
        )

    # CTA footer
    cta_y = panel_bottom - 132
    draw.rounded_rectangle(
        [content_x, cta_y, CARD_WIDTH - content_x, cta_y + 84],
        radius=18,
        fill=CARD_PURPLE,
    )
    cta_text = "link na bio"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=font_cta)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_h = cta_bbox[3] - cta_bbox[1]
    cta_x = content_x + ((CARD_WIDTH - content_x - content_x) - cta_w) // 2
    draw.text((cta_x, cta_y + (84 - cta_h) // 2 - 4), cta_text, font=font_cta, fill="#ffffff")

    draw.text(
        (panel_margin, CARD_HEIGHT - 76),
        "EmpregaNoix — vagas sem cadastro",
        font=font_footer,
        fill=CARD_MUTED,
    )

    # Encode JPEG deterministically; reduce quality in steps if needed.
    for quality in range(90, 69, -5):
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        data_bytes = buf.getvalue()
        if len(data_bytes) <= MAX_BYTES:
            return data_bytes

    raise ValueError("IG card image exceeds 8MB even after quality reduction")
