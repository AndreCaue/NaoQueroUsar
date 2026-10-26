"""Dev-only seed of published demo jobs (D-02).

Phase 5 owns the real approval flow (``pending -> published``); until then this
script is the only way to see a populated board in the browser.

Safety is by construction — there is no HTTP endpoint, no limiter import and no
way to reach production by accident:

1. refuses unless ``settings.ENV == "dev"``;
2. refuses unless the ``DATABASE_URL`` host is local or ends in ``.neon.tech``;
3. refuses to write without ``--yes`` (``--dry-run`` never writes).

Only the host is ever printed — never the URL, never the password.

Reruns are idempotent: every demo row carries :data:`MARKER` in
``source_snippet``, and the write path deletes by that marker before inserting.
``search_text`` is never written here: the database trigger owns it (D-04).

Usage (from ``backend/``)::

    .\\.venv\\Scripts\\python.exe scripts\\seed_public_demo.py --dry-run
    .\\.venv\\Scripts\\python.exe scripts\\seed_public_demo.py --yes
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make ``app`` importable when this file is run directly (``python
# scripts/seed_public_demo.py`` puts ``scripts/`` — not ``backend/`` — on
# sys.path), mirroring scripts/seed.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.session import async_session_factory  # noqa: E402
from app.models.job import Job, JobStatus  # noqa: E402
from app.services.extraction.extractor import ALLOWED_CITIES  # noqa: E402

MARKER = "SEED_PUBLIC_DEMO"
_DEFAULT_COUNT = 30  # > page size (24) so page 2 exists (B-05)
_MAX_COUNT = 60

_TITLES = (
    "Analista de Dados",
    "Desenvolvedor(a) Front-end",
    "Auxiliar Administrativo",
    "Motorista Entregador",
    "Vendedor(a) de Loja",
    "Designer Gráfico",
    "Técnico(a) de Suporte",
    "Analista Financeiro",
    "Recepcionista",
    "Assistente de Marketing",
    "Auxiliar de Logística",
    "Analista de RH",
)

_COMPANIES = (
    "Acme Recrutamento",
    "Grupo Horizonte",
    "Nexo Tecnologia",
    "Loja Central",
    "Rede Sul Serviços",
    "Oficina do Bairro",
    "Consultoria Alfa",
)

_ACTIVITIES = (
    "Montar relatórios semanais e acompanhar indicadores de vendas.",
    "Desenvolver interfaces acessíveis e responsivas junto ao time de produto.",
    "Organizar documentos, atender telefonemas e apoiar a rotina do escritório.",
    "Realizar entregas na região com veículo próprio e conferir romaneios.",
    "Atender clientes no balcão, repor mercadorias e organizar a vitrine.",
    "Criar peças para redes sociais e materiais impressos da campanha.",
    "Resolver chamados de primeiro nível por telefone e chat.",
    "Conferir contas a pagar e a receber e apoiar o fechamento mensal.",
    "Receber visitantes, controlar a agenda e encaminhar ligações.",
    "Apoiar campanhas digitais, atualizar o site e acompanhar métricas.",
)

_REQUIREMENTS = (
    "Excel intermediário, atenção a detalhes e boa comunicação.",
    "React, TypeScript e noções de acessibilidade (WCAG).",
    "Ensino médio completo e organização com documentos.",
    "CNH categoria B e disponibilidade para escala aos sábados.",
    "Experiência com atendimento ao público e disponibilidade de horário.",
    "Domínio de Figma e portfólio de peças digitais.",
    "Conhecimentos de Windows, redes básicas e atendimento remoto.",
    "Excel avançado e experiência com rotinas financeiras.",
    "Boa dicção, simpatia e organização.",
    "Noções de SEO, Meta Ads e escrita em português.",
)

_BENEFITS = (
    "Vale-transporte e vale-refeição.",
    "Plano de saúde e auxílio home office.",
    "Vale-transporte e cesta básica.",
    "Ajuda de custo para combustível.",
    "Comissão por vendas e desconto na loja.",
    None,
    "Plano odontológico e day off no aniversário.",
    "Vale-refeição e participação nos lucros.",
    None,
    "Vale-transporte e curso interno de capacitação.",
)

_SALARIES = (
    "R$ 2.500,00",
    "A combinar",
    "R$ 3.200,00",
    "R$ 1.800,00",
    "R$ 2.100,00 + comissão",
)


def _is_allowed_host(host: str) -> bool:
    """Local or a Neon branch — never a deployed/shared database."""
    normalized = (host or "").strip().lower()
    return normalized in {"localhost", "127.0.0.1"} or normalized.endswith(
        ".neon.tech"
    )


def _build_job(index: int, now: datetime) -> Job:
    """One demo row: alternating phone/e-mail, deterministic backdating."""
    contact_phone: str | None = None
    contact_email: str | None = None
    if index % 2 == 0:
        contact_phone = f"+55119000001{index:02d}"
    else:
        contact_email = f"demo{index:02d}@example.com"

    return Job(
        title=_TITLES[index % len(_TITLES)],
        # A few rows omit company/salary so the card exercises its fallbacks.
        company=None if index % 5 == 0 else _COMPANIES[index % len(_COMPANIES)],
        activities=_ACTIVITIES[index % len(_ACTIVITIES)],
        requirements=_REQUIREMENTS[index % len(_REQUIREMENTS)],
        salary=None if index % 7 == 0 else _SALARIES[index % len(_SALARIES)],
        benefits=_BENEFITS[index % len(_BENEFITS)],
        city=ALLOWED_CITIES[index % len(ALLOWED_CITIES)],
        contact_email=contact_email,
        contact_phone=contact_phone,
        status=JobStatus.published,
        source_snippet=MARKER,
        created_at=now - timedelta(days=index % 13, hours=index),
    )


async def _write(count: int) -> int:
    """Delete previous demo rows by marker, then insert ``count`` fresh ones."""
    now = datetime.now(timezone.utc)
    async with async_session_factory() as session:
        await session.execute(delete(Job).where(Job.source_snippet == MARKER))
        for index in range(count):
            session.add(_build_job(index, now))
        await session.commit()
    return count


def _print_dry_run(host: str, count: int) -> None:
    cities = ", ".join(
        f"{ALLOWED_CITIES[index % len(ALLOWED_CITIES)]}"
        for index in range(count)
    )
    titles = "; ".join(_TITLES[index % len(_TITLES)] for index in range(count))
    print(f"marker: {MARKER}")
    print(f"host: {host}")
    print(f"count: {count}")
    print(f"cities: {cities}")
    print(f"titles: {titles}")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed dev-only published demo jobs (D-02)."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="confirm the write against the resolved host",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the plan and exit without touching the database",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=_DEFAULT_COUNT,
        help=f"how many jobs to insert (1..{_MAX_COUNT}, default {_DEFAULT_COUNT})",
    )
    args = parser.parse_args(argv)
    if not 1 <= args.count <= _MAX_COUNT:
        raise SystemExit(f"--count deve estar entre 1 e {_MAX_COUNT}")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    settings = get_settings()
    if settings.ENV != "dev":
        raise SystemExit("seed_public_demo só roda com ENV=dev")

    host = make_url(settings.DATABASE_URL).host or ""
    if not _is_allowed_host(host):
        raise SystemExit(
            f"host {host!r} não é local nem .neon.tech — abortado"
        )

    if not args.yes and not args.dry_run:
        raise SystemExit(f"alvo: {host} — rode com --yes para confirmar")

    if args.dry_run:
        _print_dry_run(host, args.count)
        return 0

    inserted = asyncio.run(_write(args.count))
    print(
        f"seed_public_demo: {inserted} vagas published no host {host} "
        f"(marcador {MARKER})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
