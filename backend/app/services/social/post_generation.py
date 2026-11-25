"""Geração de post social (Facebook) — Phase 16.

Responsável por:
- montar link público seguro da vaga
- aplicar política de conteúdo (sem empresa/contatos por padrão)
- gerar draft via Groq (LLM) com fallback determinístico
- converter horário BRT (America/Sao_Paulo) para datetime UTC timezone-aware
"""

from __future__ import annotations

import re
import uuid
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from app.core.config import get_settings


BRT_TZ = ZoneInfo("America/Sao_Paulo")
ACTIONABLE_SITE_URL_ERROR = (
    "Link público indisponível: configure SITE_PUBLIC_URL no servidor para gerar o rascunho com link da vaga."
)
FALLBACK_WARNING = (
    "Não foi possível gerar com IA. Usamos um modelo padrão — revise o texto antes de aprovar."
)

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,3}\)?[\s.-]?)?\d{4,5}[\s.-]?\d{4})")
_WHATS_RE = re.compile(r"\b(?:whats(?:app)?|zap|telegram)\b[^\n]*", re.IGNORECASE)
_ALLOWED_JOB_FIELDS = ("title", "city", "salary", "activities", "benefits")


class SocialPostLinkError(ValueError):
    """SITE_PUBLIC_URL ausente/inválida para montar link público do draft."""


@dataclass
class DraftGenerationResult:
    text: str
    origin: str  # "llm" | "template_fallback"
    warning: str | None = None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def build_public_job_link(job_id: uuid.UUID, settings: Any | None = None) -> str:
    settings = settings or get_settings()
    base = str(getattr(settings, "SITE_PUBLIC_URL", "") or "").strip().rstrip("/")
    parsed = urlparse(base)
    if not base or parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SocialPostLinkError(ACTIONABLE_SITE_URL_ERROR)
    return f"{base}/?vaga={job_id}"


def brt_wall_time_to_utc(date_str: str, time_str: str) -> datetime:
    """Converte horário de parede BRT (YYYY-MM-DD, HH:MM) para UTC timezone-aware."""
    if not date_str or not time_str:
        raise ValueError("Data e horário de agendamento são obrigatórios.")
    try:
        naive = datetime.strptime(f"{date_str.strip()} {time_str.strip()}", "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise ValueError("Data/horário de agendamento inválido (use YYYY-MM-DD e HH:MM).") from exc
    local_dt = naive.replace(tzinfo=BRT_TZ)
    return local_dt.astimezone(timezone.utc)


def resolve_scheduled_at(
    publish_mode: str,
    scheduled_date: str | None = None,
    scheduled_time: str | None = None,
) -> datetime:
    if publish_mode == "publish_now":
        return now_utc()
    if publish_mode == "schedule":
        return brt_wall_time_to_utc(scheduled_date or "", scheduled_time or "")
    raise ValueError("Modo de publicação inválido.")


def _clean_text(value: Any) -> str:
    text = str(value or "").strip()
    return re.sub(r"\s+", " ", text)


def _slugify_hashtag_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    token = re.sub(r"[^A-Za-z0-9]+", "", ascii_text)
    return token or "Vagas"


def _job_allowed_data(job: Any) -> dict[str, str]:
    return {field: _clean_text(getattr(job, field, None)) for field in _ALLOWED_JOB_FIELDS}


def _scrub_contacts(text: str) -> str:
    cleaned = _EMAIL_RE.sub("", text or "")
    cleaned = _PHONE_RE.sub("", cleaned)
    cleaned = _WHATS_RE.sub("", cleaned)
    # remove menções residuais a "contato" com dados soltos
    cleaned = re.sub(r"\bcontat[oa]s?\b[:\s-]*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    return cleaned.strip()


def sanitize_and_enforce_policy(
    text: str,
    job: Any,
    *,
    link: str,
    settings: Any | None = None,
) -> str:
    """Aplica política central: sem empresa/contatos e com link público."""
    settings = settings or get_settings()
    include_contact = bool(getattr(settings, "SOCIAL_POST_INCLUDE_CONTACT", False))
    allowed = _job_allowed_data(job)
    # Ignora campos proibidos do Job (company/contact_*); remove qualquer vazamento textual
    sanitized = str(text or "")
    # Remove valores explícitos proibidos se presentes
    for forbidden in (
        _clean_text(getattr(job, "company", None)),
        _clean_text(getattr(job, "contact_email", None)),
        _clean_text(getattr(job, "contact_phone", None)),
    ):
        if forbidden:
            sanitized = sanitized.replace(forbidden, "")
    if not include_contact:
        sanitized = _scrub_contacts(sanitized)
    # Garante link público presente (apenas uma vez)
    if link not in sanitized:
        base = sanitized.rstrip()
        joiner = "\n\n" if base else ""
        sanitized = f"{base}{joiner}Confira e candidate-se: {link}".strip()
    # Normaliza quebras/espaços
    sanitized = re.sub(r"[ \t]+\n", "\n", sanitized)
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized).strip()
    # Defesa final: se ainda sobrou e-mail/telefone com flag off, remove sem perder link
    if not include_contact:
        sanitized = _scrub_contacts(sanitized)
        if link not in sanitized:
            base = sanitized.rstrip()
            joiner = "\n\n" if base else ""
            sanitized = f"{base}{joiner}Confira e candidate-se: {link}".strip()
    # Usa apenas dados permitidos como base semântica indireta (company/contact nunca)
    _ = allowed
    return sanitized


def _build_hashtags(job: Any) -> list[str]:
    city = _clean_text(getattr(job, "city", None))
    tags = ["#Emprego", "#Vagas"]
    if city:
        tags.append(f"#{_slugify_hashtag_token(city)}")
    tags.append("#EmpregaNoix")
    tags.append("#Oportunidade")
    # 3-5 hashtags
    return tags[:5]


def _truncate_preserving_link(text: str, link: str, max_chars: int = 760) -> str:
    if len(text) <= max_chars:
        return text
    if link not in text:
        return text[: max(0, max_chars - 1)].rstrip() + "…"
    before, after = text.split(link, 1)
    suffix = f" {link}{after}" if after else f" {link}"
    available = max_chars - len(suffix) - 1
    if available <= 0:
        return suffix.strip()[:max_chars]
    trimmed = before.strip()
    if len(trimmed) > available:
        trimmed = trimmed[:available].rstrip() + "…"
    return f"{trimmed}{suffix}".strip()


def generate_template_fallback(job: Any, *, link: str, settings: Any | None = None) -> str:
    settings = settings or get_settings()
    title = _clean_text(getattr(job, "title", None)) or "Vaga"
    city = _clean_text(getattr(job, "city", None))
    salary = _clean_text(getattr(job, "salary", None))
    activities = _clean_text(getattr(job, "activities", None))
    benefits = _clean_text(getattr(job, "benefits", None))

    lines: list[str] = [f"💼 {title}"]
    location_line = f"📍 {city}" if city else "📍 Local a confirmar"
    lines.append(location_line)
    if salary:
        lines.append(f"💰 Salário: {salary}")
    if activities:
        highlight = activities[:140].rstrip()
        if len(activities) > 140:
            highlight += "…"
        lines.append(f"🛠️ Atividades: {highlight}")
    if benefits:
        lines.append(f"✨ Benefícios: {benefits[:120].rstrip()}")
    lines.append("")
    lines.append(f"👉 Confira e candidate-se: {link}")
    hashtags = " ".join(_build_hashtags(job))
    lines.append("")
    lines.append(hashtags)
    text = "\n".join(lines).strip()
    text = _truncate_preserving_link(text, link, max_chars=760)
    return sanitize_and_enforce_policy(text, job, link=link, settings=settings)


def _build_llm_messages(job: Any, link: str) -> list[dict[str, str]]:
    allowed = _job_allowed_data(job)
    details = [
        f"Título: {allowed.get('title') or 'Não informado'}",
        f"Cidade: {allowed.get('city') or 'Não informada'}",
        f"Salário: {allowed.get('salary') or 'Não informado'}",
        f"Atividades: {allowed.get('activities') or 'Não informado'}",
        f"Benefícios: {allowed.get('benefits') or 'Não informado'}",
        f"Link público da vaga (obrigatório): {link}",
    ]
    user = "\n".join(details)
    return [
        {
            "role": "system",
            "content": (
                "Você escreve posts de vaga para Facebook em pt-BR, tom profissional e acolhedor. "
                "Use apenas os dados fornecidos. NÃO inclua nome da empresa e NÃO inclua contatos "
                "(telefone, e-mail, WhatsApp). Inclua o link público exatamente como fornecido, "
                "CTA clara, 3 a 5 hashtags relevantes e emojis moderados. Mire ~700 caracteres."
            ),
        },
        {"role": "user", "content": user},
    ]


def _build_real_client(settings: Any) -> Any:
    api_key = str(getattr(settings, "GROQ_API_KEY", "") or "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY ausente")
    try:
        from groq import AsyncGroq  # type: ignore
    except Exception as exc:  # pragma: no cover - import guard
        raise RuntimeError("SDK Groq indisponível") from exc
    timeout = getattr(settings, "GROQ_TIMEOUT_SECONDS", 60)
    return AsyncGroq(api_key=api_key, timeout=timeout)


async def generate_draft_for_job(
    job: Any,
    settings: Any | None = None,
    *,
    client: Any | None = None,
) -> DraftGenerationResult:
    settings = settings or get_settings()
    link = build_public_job_link(job.id, settings=settings)
    try:
        if client is None:
            client = _build_real_client(settings)
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=_build_llm_messages(job, link),
            temperature=0.4,
        )
        content = ""
        choices = getattr(response, "choices", None) or []
        if choices:
            message = getattr(choices[0], "message", None)
            content = (getattr(message, "content", None) or "").strip()
        if not content:
            raise ValueError("Resposta LLM vazia")
        text = sanitize_and_enforce_policy(content, job, link=link, settings=settings)
        text = _truncate_preserving_link(text, link, max_chars=760)
        return DraftGenerationResult(text=text, origin="llm", warning=None)
    except Exception:
        fallback_text = generate_template_fallback(job, link=link, settings=settings)
        return DraftGenerationResult(
            text=fallback_text,
            origin="template_fallback",
            warning=FALLBACK_WARNING,
        )


def _normalize_instagram_city_hashtag(city: str | None) -> str:
    value = _clean_text(city)
    if not value or value.casefold() == "remoto".casefold():
        return "#remoto"
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    token = re.sub(r"[^A-Za-z0-9]+", "", ascii_text).lower()
    return f"#{token}" if token else "#cidade"


def generate_instagram_template(job: Any) -> str:
    title = _clean_text(getattr(job, "title", None)) or "Vaga"
    company = _clean_text(getattr(job, "company", None))
    city = _clean_text(getattr(job, "city", None))
    employment_type = _clean_text(
        getattr(job, "employment_type", None)
        or getattr(job, "contract_type", None)
        or getattr(job, "type", None)
    )
    salary = _clean_text(getattr(job, "salary", None))

    lines: list[str] = [f"💼 {title}"]
    if company and company.casefold() not in {"empresa confidencial", "confidencial"}:
        lines.append(f"🏢 {company}")
    lines.append(f"📍 {city}" if city else "📍 Local a confirmar")
    if employment_type:
        lines.append(f"📝 {employment_type}")
    if salary:
        lines.append(f"💰 {salary}")
    lines.append("")
    lines.append("Confira os detalhes e candidate-se: link na bio")
    lines.append("")
    lines.append(
        f"#vagas #emprego {_normalize_instagram_city_hashtag(city)} #oportunidade"
    )
    return "\n".join(lines).strip()[:2200]


async def generate_instagram_draft_for_job(
    job: Any, settings: Any | None = None
) -> DraftGenerationResult:
    _ = settings
    return DraftGenerationResult(
        text=generate_instagram_template(job)[:2200],
        origin="template_fallback",
        warning=None,
    )


__all__ = [
    "ACTIONABLE_SITE_URL_ERROR",
    "FALLBACK_WARNING",
    "DraftGenerationResult",
    "SocialPostLinkError",
    "brt_wall_time_to_utc",
    "build_public_job_link",
    "generate_draft_for_job",
    "generate_instagram_draft_for_job",
    "generate_instagram_template",
    "generate_template_fallback",
    "now_utc",
    "resolve_scheduled_at",
    "sanitize_and_enforce_policy",
]
