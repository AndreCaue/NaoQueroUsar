import uuid
from types import SimpleNamespace

import pytest

from app.services.social.post_generation import (
    ACTIONABLE_SITE_URL_ERROR,
    SocialPostLinkError,
    build_public_job_link,
    sanitize_and_enforce_policy,
)


def _settings(site_url="https://site.exemplo/", include_contact=False):
    return SimpleNamespace(
        SITE_PUBLIC_URL=site_url,
        SOCIAL_POST_INCLUDE_CONTACT=include_contact,
    )


def _job():
    return SimpleNamespace(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        title="Operador de Caixa",
        company="Empresa Secreta LTDA",
        activities="Atender clientes e operar caixa",
        requirements="Ensino médio",
        salary="R$ 2.000",
        benefits="VT e VR",
        city="Belo Horizonte",
        contact_email="contato@empresa.com",
        contact_phone="+55 31 99999-0000",
    )


def test_build_public_job_link_uses_site_public_url_and_job_id():
    settings = _settings("https://site.exemplo/")
    link = build_public_job_link(uuid.UUID("11111111-1111-1111-1111-111111111111"), settings=settings)
    assert link == "https://site.exemplo/?vaga=11111111-1111-1111-1111-111111111111"


@pytest.mark.parametrize("site_url", ["", "   ", "not-a-url", "ftp://site.exemplo"])
def test_build_public_job_link_rejects_missing_or_invalid_site_url(site_url):
    settings = _settings(site_url=site_url)
    with pytest.raises(SocialPostLinkError) as exc:
        build_public_job_link(uuid.uuid4(), settings=settings)
    assert str(exc.value) == ACTIONABLE_SITE_URL_ERROR
    assert str(exc.value) == "Link público indisponível: configure SITE_PUBLIC_URL no servidor para gerar o rascunho com link da vaga."


def test_sanitize_policy_removes_company_and_contact_by_default():
    job = _job()
    settings = _settings(include_contact=False)
    link = build_public_job_link(job.id, settings=settings)
    dirty_text = (
        "Vaga na Empresa Secreta LTDA. Fale com contato@empresa.com ou +55 31 99999-0000. "
        f"Link: {link}"
    )
    sanitized = sanitize_and_enforce_policy(dirty_text, job, link=link, settings=settings)
    assert "Empresa Secreta LTDA" not in sanitized
    assert "contato@empresa.com" not in sanitized
    assert "+55 31 99999-0000" not in sanitized
    assert "99999-0000" not in sanitized
    assert link in sanitized


def test_sanitize_policy_keeps_contact_out_even_if_include_flag_false_explicit():
    job = _job()
    settings = _settings(include_contact=False)
    link = build_public_job_link(job.id, settings=settings)
    text = f"WhatsApp: 31999990000 Email: contato@empresa.com {link}"
    sanitized = sanitize_and_enforce_policy(text, job, link=link, settings=settings)
    assert "contato@empresa.com" not in sanitized
    assert "31999990000" not in sanitized
    assert "99999-0000" not in sanitized
    assert settings.SOCIAL_POST_INCLUDE_CONTACT is False
