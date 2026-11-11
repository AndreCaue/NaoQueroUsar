"""Unit tests for the extraction term-removal rule (backend authority)."""

import pytest

from app.services.extraction.blocklist import (
    REMOVED_TERM,
    TERM_REMOVED_ALERT,
    strip_blocked_terms,
)


@pytest.mark.parametrize(
    "text",
    [
        "JACIRA CHAVARE",
        "jacira chavare",
        "Jacira Chavare",
        "JACIRA   CHAVARE",
        "JACIRA\nCHAVARE",
        "JACIRA\tCHAVARE",
        "JACIRA CHAVÁRE",
        "  jacira chavare  ",
    ],
)
def test_remove_variacoes(text):
    assert strip_blocked_terms(text) == ""


def test_remove_multiplas_ocorrencias():
    out = strip_blocked_terms(
        "Vaga 1: jacira chavare / Vaga 2: JACIRA CHAVARE"
    )
    assert "jacira" not in out.casefold()
    assert "chavare" not in out.casefold()
    assert "Vaga 1:" in out
    assert "Vaga 2:" in out
    assert strip_blocked_terms("jacira chavare jacira chavare") == ""


def test_preserva_texto_ao_redor():
    blob = (
        "Vaga: Auxiliar de limpeza — contato rh@empresa.com\n\n"
        "Bairro: Centro\nNome citado: jacira chavare\nSalário: R$ 1.800"
    )
    out = strip_blocked_terms(blob)
    assert out.startswith("Vaga: Auxiliar de limpeza — contato rh@empresa.com")
    assert out.endswith("Salário: R$ 1.800")
    assert "rh@empresa.com" in out
    assert "Bairro: Centro" in out
    assert "jacira" not in out.casefold()
    assert "chavare" not in out.casefold()
    assert out.strip() != ""


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Vaga para desenvolvedor backend em São Paulo — rh@acme.com.br",
        "JACIRA",
        "CHAVARE",
        "Acentuação e\tquebras\npreservadas — ação, coração",
    ],
)
def test_texto_sem_termo_fica_intacto(text):
    assert strip_blocked_terms(text) == text


def test_so_o_termo_vira_string_vazia():
    assert strip_blocked_terms("JACIRA CHAVARE") == ""
    assert strip_blocked_terms("  Jacira\nChavare  ") == ""


def test_alerta_pt_br_cita_o_termo():
    assert REMOVED_TERM in TERM_REMOVED_ALERT
    assert "removido" in TERM_REMOVED_ALERT
