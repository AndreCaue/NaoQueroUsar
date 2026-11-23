"""IMAG-02/IMAG-03: deterministic IG card rendering and hash behavior."""

from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

from PIL import Image

from app.services.social.image_card import (
    CARD_HEIGHT,
    CARD_WIDTH,
    MAX_BYTES,
    get_bundled_font_paths,
    render_ig_card,
)
from app.services.social.image_media import compute_ig_card_hash


def _job(**overrides):
    base = {
        "title": "Auxiliar de Cozinha",
        "company": "EmpregaNoix Foods",
        "city": "São Paulo",
        "salary": "R$ 2.000,00",
        "contract_type": "CLT",
        "contact_email": "contato@example.com",
        "contact_phone": "+55 11 99999-0000",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_ig_card_is_deterministic_and_valid_jpeg() -> None:
    regular, bold = get_bundled_font_paths()
    job = _job()

    data1 = render_ig_card(job, font_regular_path=regular, font_bold_path=bold)
    data2 = render_ig_card(job, font_regular_path=regular, font_bold_path=bold)

    assert data1 == data2
    assert len(data1) < MAX_BYTES
    assert data1.startswith(b"\xff\xd8\xff")

    with Image.open(BytesIO(data1)) as img:
        assert img.format == "JPEG"
        assert img.size == (CARD_WIDTH, CARD_HEIGHT)
        assert img.size == (1080, 1350)
        assert img.mode == "RGB"


def test_ig_card_hash_changes_for_relevant_fields_only() -> None:
    base = _job()
    changed_title = _job(title="Atendente de Loja")
    changed_contact = _job(contact_email="outro@example.com", contact_phone="+55 21 98888-7777")

    base_hash = compute_ig_card_hash(base)
    title_hash = compute_ig_card_hash(changed_title)
    contact_hash = compute_ig_card_hash(changed_contact)

    assert base_hash == title_hash or base_hash != title_hash  # explicit check below
    assert base_hash != title_hash
    assert base_hash == contact_hash
    assert len(base_hash) == 16
