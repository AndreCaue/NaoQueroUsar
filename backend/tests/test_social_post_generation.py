import uuid
from types import SimpleNamespace

import pytest

from app.services.social.post_generation import (
    FALLBACK_WARNING,
    build_public_job_link,
    generate_draft_for_job,
    generate_instagram_draft_for_job,
    generate_instagram_template,
)


def _settings(site_url="https://site.exemplo/"):
    return SimpleNamespace(
        SITE_PUBLIC_URL=site_url,
        GROQ_API_KEY="gsk_test",
        GROQ_MODEL="openai/gpt-oss-20b",
        GROQ_TIMEOUT_SECONDS=30,
        SOCIAL_POST_INCLUDE_CONTACT=False,
    )


def _job():
    return SimpleNamespace(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        title="Auxiliar de Estoque",
        company="Empresa Confidencial SA",
        activities="Organizar estoque e separar pedidos",
        requirements=None,
        salary="R$ 1.800",
        benefits="Vale transporte",
        city="São Paulo",
        contact_email="rh@confidencial.com",
        contact_phone="+55 11 98888-7777",
    )


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, *, content=None, exc=None):
        self._content = content
        self._exc = exc

    async def create(self, **kwargs):
        if self._exc:
            raise self._exc
        return _FakeResponse(self._content)


class _FakeChat:
    def __init__(self, *, content=None, exc=None):
        self.completions = _FakeCompletions(content=content, exc=exc)


class _FakeGroqClient:
    def __init__(self, *, content=None, exc=None):
        self.chat = _FakeChat(content=content, exc=exc)


@pytest.mark.asyncio
async def test_generate_draft_uses_llm_result_when_available_and_policy_safe():
    job = _job()
    settings = _settings()
    link = build_public_job_link(job.id, settings=settings)
    llm_text = (
        "💼 Auxiliar de Estoque em São Paulo na Empresa Confidencial SA. "
        "Contato rh@confidencial.com / +55 11 98888-7777. "
        f"Candidate-se: {link} #Emprego #Vagas #SaoPaulo"
    )
    client = _FakeGroqClient(content=llm_text)

    result = await generate_draft_for_job(job, settings=settings, client=client)

    assert result.origin == "llm"
    assert result.warning is None
    assert link in result.text
    assert "Empresa Confidencial SA" not in result.text
    assert "rh@confidencial.com" not in result.text
    assert "98888-7777" not in result.text


@pytest.mark.asyncio
async def test_generate_draft_falls_back_to_template_on_llm_failure():
    job = _job()
    settings = _settings()
    link = build_public_job_link(job.id, settings=settings)
    client = _FakeGroqClient(exc=RuntimeError("groq indisponível"))

    result = await generate_draft_for_job(job, settings=settings, client=client)

    assert result.origin == "template_fallback"
    assert result.warning == FALLBACK_WARNING
    assert "Confira e candidate-se:" in result.text
    assert link in result.text
    assert "#" in result.text  # hashtags
    assert "Empresa Confidencial SA" not in result.text
    assert "rh@confidencial.com" not in result.text
    assert "98888-7777" not in result.text


@pytest.mark.asyncio
async def test_generation_uses_only_allowed_job_fields_no_company_or_contacts():
    job = _job()
    settings = _settings()
    # Mesmo com resposta LLM pobre, o resultado final deve permanecer policy-safe
    client = _FakeGroqClient(content="Texto genérico sem link")

    result = await generate_draft_for_job(job, settings=settings, client=client)

    # Usa Job persistido no fluxo e nunca expõe campos proibidos
    assert result.origin == "llm"
    assert "Empresa Confidencial SA" not in result.text
    assert "rh@confidencial.com" not in result.text
    assert "98888-7777" not in result.text
    assert build_public_job_link(job.id, settings=settings) in result.text
    # Campos permitidos do job permanecem a fonte segura (company/contact excluídos)
    assert job.title == "Auxiliar de Estoque" and job.company not in result.text
    assert job.contact_email not in result.text and job.contact_phone not in result.text


def _ig_job(**overrides):
    base = {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "title": "Auxiliar de Estoque",
        "company": "Loja Exemplo",
        "city": "São Paulo",
        "salary": "R$ 1.800",
        "employment_type": "CLT",
        "contact_email": "rh@exemplo.com",
        "contact_phone": "+55 11 98888-7777",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_generate_instagram_template_deterministic_safe_contract():
    job = _ig_job()

    text = generate_instagram_template(job)

    assert "link na bio" in text.lower()
    assert "#vagas" in text
    assert "#emprego" in text
    assert "#oportunidade" in text
    assert "#saopaulo" in text
    assert len(text) <= 2200
    assert "rh@exemplo.com" not in text
    assert "98888-7777" not in text
    assert "+55 11 98888-7777" not in text


def test_generate_instagram_template_does_not_leak_contacts_or_invent_confidential_company():
    confidential = _ig_job(
        company="Empresa Confidencial",
        contact_email="sigiloso@empresa.com",
        contact_phone="(11) 97777-6666",
    )
    absent_company = _ig_job(
        company=None,
        contact_email="outro@empresa.com",
        contact_phone="11999990000",
    )

    confidential_text = generate_instagram_template(confidential)
    absent_text = generate_instagram_template(absent_company)

    for text, job in ((confidential_text, confidential), (absent_text, absent_company)):
        assert "sigiloso@empresa.com" not in text
        assert "outro@empresa.com" not in text
        assert "97777-6666" not in text
        assert "11999990000" not in text
        assert job.contact_email not in text
        assert (job.contact_phone or "") not in text
        assert "link na bio" in text.lower()
        assert len(text) <= 2200

    assert "Empresa Confidencial" not in confidential_text
    assert "🏢" not in absent_text


@pytest.mark.asyncio
async def test_generate_instagram_draft_for_job_returns_safe_template_fallback_contract():
    job = _ig_job()

    result = await generate_instagram_draft_for_job(job)

    assert result.origin == "template_fallback"
    assert result.warning is None
    assert result.text
    assert len(result.text) <= 2200
    assert "link na bio" in result.text.lower()
    assert "rh@exemplo.com" not in result.text
    assert "98888-7777" not in result.text
