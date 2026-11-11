"""Unit tests for the extraction blocklist rule (backend authority)."""

import pytest

from app.services.extraction.blocklist import (
    BLOCKED_TERM,
    BLOCKED_TERM_ERROR,
    is_blocked_text,
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
        (
            "Vaga: Auxiliar de limpeza — contato rh@empresa.com\n\n"
            "Bairro: Centro\nNome citado: jacira chavare\nSalário: R$ 1.800"
        ),
    ],
)
def test_bloqueia_variacoes(text):
    assert is_blocked_text(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "",
        "JACIRA",
        "CHAVARE",
        "Vaga para desenvolvedor backend em São Paulo — rh@acme.com.br",
    ],
)
def test_permite_texto_sem_termo(text):
    assert is_blocked_text(text) is False


def test_mensagem_pt_br_cita_o_termo():
    assert BLOCKED_TERM in BLOCKED_TERM_ERROR
    assert BLOCKED_TERM_ERROR.endswith("antes de extrair.")
