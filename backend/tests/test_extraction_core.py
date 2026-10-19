"""Unit tests for the pure-logic extraction foundation (plan 02-01, task 2).

Covers: pt-BR phone normalization, normalized-containment grounding,
delimiter-aware chunking under a token budget, and the strict LLM-output
Pydantic models. No network, no DB, no FastAPI — pure functions only.
"""

import random

import pytest
from pydantic import ValidationError

from app.services.extraction.chunking import chunk_text, estimate_tokens
from app.services.extraction.grounding import is_grounded, normalize_for_grounding
from app.services.extraction.phones import normalize_phone
from app.services.extraction.schema import ExtractedJobRaw, JobCandidate

# ---------------------------------------------------------------------------
# phones.normalize_phone — pt-BR formats → E.164, or None (never raise)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("(11) 9 1234-5678", "+5511912345678"),
        ("11 91234-5678", "+5511912345678"),
        ("+55 11 91234-5678", "+5511912345678"),
        ("1134567890", "+551134567890"),          # landline, 10 digits
        ("912345678", None),                      # no DDD → ambiguous, reject
        ("abc", None),
        (None, None),
        ("", None),
        ("..11.91234.5678", "+5511912345678"),    # leading dots stripped
        ("+55 (11) 98765-4321", "+5511987654321"),
        ("5511912345678", "+5511912345678"),      # bare country code accepted
        ("119123456", None),                      # 9 local digits without DDD
        ("0011912345678", None),                  # invalid
    ],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


def test_normalize_phone_never_raises_on_garbage():
    for junk in (123, object(), "☎☎☎", "++5511912345678"):
        assert normalize_phone(junk) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# grounding — normalized containment check
# ---------------------------------------------------------------------------

def test_normalize_strips_accents_punct_and_emoji():
    assert normalize_for_grounding("São Paulo — 📞 ") == "sao paulo"
    assert normalize_for_grounding("São Paulo — 📞 ") == normalize_for_grounding("sao paulo")


def test_normalize_keeps_contact_and_salary_chars():
    out = normalize_for_grounding("Envie p/ rh.empresa+x@dominio.com R$ 2.500,00")
    assert "@dominio.com" in out
    assert "2.500" in out
    assert "+" in out


def test_normalize_is_idempotent():
    s = normalize_for_grounding("Vaga @urgente!!! R$ 2.500 — São Paulo")
    assert normalize_for_grounding(s) == s


def test_is_grounded_true_when_normalized_phrase_in_source():
    source = normalize_for_grounding("Vaga Urgente!!! Operador de produção — ligar 91234-5678")
    assert is_grounded("Vaga Urgente!!!", source) is True


def test_is_grounded_false_for_absent_phrase():
    source = normalize_for_grounding("Vaga Urgente!!! Operador")
    assert is_grounded("Empresa Inexistente Ltda", source) is False


def test_is_grounded_false_for_empty_needle():
    source = normalize_for_grounding("qualquer coisa")
    assert is_grounded("", source) is False
    assert is_grounded("   ", source) is False


# ---------------------------------------------------------------------------
# chunking — budget-aware, delimiter-preserving, lossless
# ---------------------------------------------------------------------------

def _random_paste(rng: random.Random) -> str:
    words = [
        "vaga", "urgente", "operador", "auxiliar", "tecnico", "@email.com",
        "+55119", "sao", "paulo", "678", "R$", "estagio", "escala-6x1",
    ]
    lines = []
    for _ in range(rng.randint(5, 60)):
        n = rng.randint(1, 8)
        lines.append(" ".join(rng.choice(words) for _ in range(n)))
        if rng.random() < 0.15:
            lines.append("")
    return "\n".join(lines)


def test_chunk_concat_preserves_all_content_seeded_property():
    """10 randomized pastes × 3 budgets: no character lost (modulo whitespace)."""
    rng = random.Random(42)
    pastes = [_random_paste(rng) for _ in range(10)]
    for text in pastes:
        for budget in (20, 100, 500):
            chunks = chunk_text(text, budget)
            assert all(c.strip() for c in chunks), "no empty chunks"
            assert " ".join("".join(chunks).split()) == " ".join(text.split())
            # Every chunk fits the budget (words are short → always possible).
            assert all(estimate_tokens(c) <= budget for c in chunks)


def test_chunk_empty_and_whitespace_only():
    assert chunk_text("", 100) == []
    assert chunk_text("   \n\n  \t ", 100) == []


def test_chunk_oversized_unsplittable_block_is_emitted():
    text = "x" * 100  # no whitespace anywhere
    assert chunk_text(text, 10) == [text]


def test_chunk_prefers_blank_line_boundaries():
    text = "primeiro paragrafo com vaga\n\nsegundo paragrafo com salario"
    chunks = chunk_text(text, 12)
    assert len(chunks) == 2
    # Cut lands exactly on the paragraph boundary: first chunk is the whole
    # first paragraph; the second carries the separator and the rest.
    assert chunks[0] == "primeiro paragrafo com vaga"
    assert chunks[1].strip() == "segundo paragrafo com salario"
    assert "".join(chunks) == text  # contiguous exact slices


def test_chunk_splits_on_lines_never_mid_word():
    text = "linha um dois tres\nlinha quatro cinco\nlinha seis sete"
    chunks = chunk_text(text, 10)  # whole exceeds budget; each line fits
    assert len(chunks) == 2
    original_lines = text.split("\n")
    for c in chunks:
        for line in c.strip().split("\n"):
            if line:
                assert line in original_lines


def test_estimate_tokens_is_chars_over_four():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 14000) == 3500


# ---------------------------------------------------------------------------
# schema — strict LLM-output models reject structurally invalid rows
# ---------------------------------------------------------------------------

GOOD_ROW = {
    "title": "Operador de Produção",
    "company": "Empresa X",
    "activities": "Operar máquina.",
    "requirements": "Ensino médio.",
    "salary": "R$ 2.000",
    "benefits": "VR, VT",
    "city": "São Paulo",
    "contact_email": "rh@empresa.com",
    "contact_phone": "+5511912345678",
}


def test_extracted_job_raw_accepts_valid_row():
    row = ExtractedJobRaw.model_validate(GOOD_ROW)
    assert row.title == "Operador de Produção"
    assert row.contact_phone == "+5511912345678"


def test_extracted_job_raw_accepts_nullable_fields_absent_from_dict():
    row = ExtractedJobRaw.model_validate({"title": "Vaga", "city": "Remoto"})
    assert row.company is None


def test_extracted_job_raw_rejects_missing_title():
    bad = {k: v for k, v in GOOD_ROW.items() if k != "title"}
    with pytest.raises(ValidationError):
        ExtractedJobRaw.model_validate(bad)


def test_extracted_job_raw_rejects_extra_key():
    with pytest.raises(ValidationError):
        ExtractedJobRaw.model_validate({**GOOD_ROW, "hacker_field": "x"})


def test_job_candidate_adds_provenance_fields():
    cand = JobCandidate.model_validate(
        {**GOOD_ROW, "source_snippet": "…ligar 91234-5678", "raw_city": "SÃO PAULO"}
    )
    assert cand.source_snippet == "…ligar 91234-5678"
    assert cand.raw_city == "SÃO PAULO"
    assert cand.title == GOOD_ROW["title"]
