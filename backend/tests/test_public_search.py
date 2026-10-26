"""Search, city filter and sort integration tests (SRCH-01/02/03).

Two layers live in this file:

1. **Database contract** (migration ``0003``): ``jobs.search_text`` is produced
   by the ``jobs_set_search_text()`` trigger and must include ``requirements``.
   The backfill must refresh existing rows *without* bumping ``updated_at`` and
   must leave the ``jobs_updated_at`` trigger enabled.
2. **HTTP contract**: ``q``/``city``/``sort`` on ``GET /api/v1/public/jobs``,
   including wildcard escaping, the city alias table, the AND composition and
   the deterministic ``created_at, id`` ordering that keeps paging stable.

The suite runs against the real Postgres test branch; every assertion goes
through ``flush()`` (or the HTTP layer) so it sees what the trigger actually
wrote — never an in-memory Python value.
"""

from datetime import datetime, timezone

from sqlalchemy import text

from app.models.job import Job, JobStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _job(**overrides) -> Job:
    """A published, contact-bearing job that passes both CHECK constraints."""
    defaults = {
        "title": "Vaga de Teste",
        "city": "Remoto",
        "contact_phone": "+55 11 90000-0100",
        "status": JobStatus.published,
    }
    defaults.update(overrides)
    return Job(**defaults)


async def _insert(db_session, **overrides) -> Job:
    job = _job(**overrides)
    db_session.add(job)
    await db_session.flush()
    return job


# Canonical DB spellings — the extraction pipeline writes these values
# (``ALLOWED_CITIES`` in ``app/services/extraction/extractor.py``).
SAO_PAULO = "São Paulo"
RIO = "Rio de Janeiro"


# ---------------------------------------------------------------------------
# Trigger / migration 0003 (search_text includes requirements)
# ---------------------------------------------------------------------------


async def test_trigger_search_text_includes_requirements(db_session):
    job = _job(
        title="Analista Sênior",
        requirements="Kubernetes e Terraform",
        contact_phone="+55 11 90000-0101",
    )
    db_session.add(job)
    await db_session.flush()
    await db_session.refresh(job)

    assert job.search_text is not None
    assert "kubernetes" in job.search_text
    assert "analista senior" in job.search_text


async def test_trigger_updates_search_text_on_requirements_change(db_session):
    job = _job(
        title="Desenvolvedor(a) Backend",
        requirements="Kubernetes e Terraform",
        contact_phone="+55 11 90000-0102",
    )
    db_session.add(job)
    await db_session.flush()
    await db_session.refresh(job)
    assert "kubernetes" in job.search_text

    job.requirements = "Java e Spring Boot"
    await db_session.flush()
    await db_session.refresh(job)

    assert "java" in job.search_text
    assert "kubernetes" not in job.search_text


async def test_trigger_function_definition_has_requirements(db_session):
    """Proves migration 0003 was applied to this database, not just written."""
    prosrc = await db_session.scalar(
        text("SELECT prosrc FROM pg_proc WHERE proname = 'jobs_set_search_text'")
    )

    assert prosrc is not None
    assert "requirements" in prosrc


async def test_backfill_preserves_updated_at(db_session):
    job = _job(
        title="Auxiliar Administrativo",
        company="Empresa Backfill",
        activities="Rotinas administrativas.",
        requirements="Excel intermediário",
        contact_phone="+55 11 90000-0103",
    )
    db_session.add(job)
    await db_session.flush()
    await db_session.refresh(job)
    before = job.updated_at

    await db_session.execute(text("ALTER TABLE jobs DISABLE TRIGGER jobs_updated_at"))
    await db_session.execute(
        text(
            "UPDATE jobs SET search_text = immutable_unaccent(lower("
            "coalesce(title, '') || ' ' || coalesce(company, '') || ' ' || "
            "coalesce(activities, '') || ' ' || coalesce(requirements, ''))) "
            "WHERE id = :id"
        ),
        {"id": job.id},
    )
    await db_session.execute(text("ALTER TABLE jobs ENABLE TRIGGER jobs_updated_at"))

    await db_session.refresh(job)
    assert job.updated_at == before
    assert "excel" in job.search_text


async def test_updated_at_trigger_is_enabled(db_session):
    state = await db_session.scalar(
        text("SELECT tgenabled FROM pg_trigger WHERE tgname = 'jobs_updated_at'")
    )
    # ``pg_trigger.tgenabled`` is a ``"char"`` column; asyncpg hands it back as
    # a single byte rather than a str.
    if isinstance(state, (bytes, bytearray)):
        state = state.decode()

    assert state == "O"


# ---------------------------------------------------------------------------
# SRCH-01 — accent/case-insensitive search over the normalized search_text
# ---------------------------------------------------------------------------


async def test_search_matches_title_ignoring_case(db_session, client):
    await _insert(db_session, title="ANALISTA de Dados", city="Remoto")
    await _insert(db_session, title="Vendedor de Loja", city="Remoto")

    resp = await client.get("/api/v1/public/jobs", params={"q": "analista"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_search_matches_company_ignoring_accents(db_session, client):
    await _insert(
        db_session,
        title="Vaga Administrativa",
        company="São Paulo Consultoria",
        city="Remoto",
    )
    await _insert(
        db_session, title="Vaga de Logística", company="Rio Express", city="Remoto"
    )

    for term in ("sao paulo", "São Paulo", "SAO PAULO"):
        resp = await client.get("/api/v1/public/jobs", params={"q": term})
        assert resp.status_code == 200, term
        assert resp.json()["total"] == 1, term


async def test_search_matches_requirements_only(db_session, client):
    await _insert(
        db_session,
        title="Desenvolvedor(a) Backend",
        requirements="Kubernetes e Terraform",
        city="Remoto",
    )
    await _insert(db_session, title="Recepcionista", city="Remoto")

    resp = await client.get("/api/v1/public/jobs", params={"q": "kubernetes"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Desenvolvedor(a) Backend"


async def test_search_trims_whitespace(db_session, client):
    await _insert(db_session, title="Analista Financeiro", city="Remoto")
    await _insert(db_session, title="Motorista Entregador", city="Remoto")

    resp = await client.get("/api/v1/public/jobs", params={"q": "  analista  "})
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_search_wildcards_are_literal(db_session, client):
    # T-04-03: ``%`` and ``_`` are LIKE metacharacters and must be escaped.
    await _insert(db_session, title="Aumento de 100% garantido", city="Remoto")
    await _insert(db_session, title="Analista de Dados", city="Remoto")

    percent = await client.get("/api/v1/public/jobs", params={"q": "%"})
    assert percent.status_code == 200
    assert percent.json()["total"] == 1
    assert percent.json()["items"][0]["title"] == "Aumento de 100% garantido"

    literal = await client.get("/api/v1/public/jobs", params={"q": "100%"})
    assert literal.status_code == 200
    assert literal.json()["total"] == 1

    underscore = await client.get("/api/v1/public/jobs", params={"q": "_"})
    assert underscore.status_code == 200
    assert underscore.json()["total"] == 0


# ---------------------------------------------------------------------------
# SRCH-02 — city filter (slug, canonical and accented label; unknown ignored)
# ---------------------------------------------------------------------------


async def test_city_filter_accepts_slug_canonical_and_label(db_session, client):
    sp = await _insert(db_session, title="Vaga São Paulo", city=SAO_PAULO)
    await _insert(db_session, title="Vaga Rio", city=RIO)

    for value in ("sao-paulo", "Sao Paulo", "sao paulo", "São Paulo"):
        resp = await client.get("/api/v1/public/jobs", params={"city": value})
        assert resp.status_code == 200, value
        body = resp.json()
        assert body["total"] == 1, value
        assert body["items"][0]["id"] == str(sp.id), value


async def test_unknown_city_is_ignored(db_session, client):
    await _insert(db_session, title="Vaga São Paulo", city=SAO_PAULO)
    await _insert(db_session, title="Vaga Rio", city=RIO)

    resp = await client.get("/api/v1/public/jobs", params={"city": "atlantida"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


async def test_q_and_city_combine_with_and(db_session, client):
    sp_analista = await _insert(
        db_session, title="Analista de Dados", city=SAO_PAULO
    )
    await _insert(db_session, title="Vendedor de Loja", city=SAO_PAULO)
    await _insert(db_session, title="Analista de Suporte", city=RIO)

    resp = await client.get(
        "/api/v1/public/jobs", params={"q": "analista", "city": "sao-paulo"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == str(sp_analista.id)


# ---------------------------------------------------------------------------
# SRCH-03 — deterministic date sort (created_at + id tie-break)
# ---------------------------------------------------------------------------


def _at(day: int) -> datetime:
    return datetime(2026, 10, day, 12, 0, tzinfo=timezone.utc)


async def test_sort_recentes_is_the_default_and_antigas_reverses_it(
    db_session, client
):
    await _insert(db_session, title="Vaga 01 Out", created_at=_at(1))
    await _insert(db_session, title="Vaga 05 Out", created_at=_at(5))
    await _insert(db_session, title="Vaga 03 Out", created_at=_at(3))

    default = await client.get("/api/v1/public/jobs")
    assert default.status_code == 200
    assert [i["title"] for i in default.json()["items"]] == [
        "Vaga 05 Out",
        "Vaga 03 Out",
        "Vaga 01 Out",
    ]

    recentes = await client.get("/api/v1/public/jobs", params={"sort": "recentes"})
    assert [i["title"] for i in recentes.json()["items"]] == [
        "Vaga 05 Out",
        "Vaga 03 Out",
        "Vaga 01 Out",
    ]

    antigas = await client.get("/api/v1/public/jobs", params={"sort": "antigas"})
    assert [i["title"] for i in antigas.json()["items"]] == [
        "Vaga 01 Out",
        "Vaga 03 Out",
        "Vaga 05 Out",
    ]


async def test_unknown_sort_falls_back_to_recentes(db_session, client):
    await _insert(db_session, title="Vaga Antiga", created_at=_at(1))
    await _insert(db_session, title="Vaga Nova", created_at=_at(9))

    resp = await client.get("/api/v1/public/jobs", params={"sort": "banana"})
    assert resp.status_code == 200
    assert [i["title"] for i in resp.json()["items"]] == [
        "Vaga Nova",
        "Vaga Antiga",
    ]


async def test_tie_break_returns_distinct_ids_across_pages(db_session, client):
    # Same-transaction rows share ``now()``; without the id tie-break a small
    # ``limit`` can repeat one row and drop another (Pitfall 3).
    same_instant = _at(2)
    jobs = [
        await _insert(
            db_session, title=f"Vaga Empatada {n}", created_at=same_instant
        )
        for n in range(3)
    ]
    expected = {str(job.id) for job in jobs}

    seen: list[str] = []
    for page in (1, 2, 3):
        resp = await client.get(
            "/api/v1/public/jobs", params={"limit": 1, "page": page}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["items"]) == 1
        seen.append(body["items"][0]["id"])

    assert len(set(seen)) == 3
    assert set(seen) == expected


# ---------------------------------------------------------------------------
# total consistency and the contact-free payload
# ---------------------------------------------------------------------------


async def test_total_matches_the_same_filters_as_items(db_session, client):
    await _insert(db_session, title="Analista Um", city=SAO_PAULO)
    await _insert(db_session, title="Analista Dois", city=SAO_PAULO)
    await _insert(db_session, title="Vendedor", city=SAO_PAULO)

    resp = await client.get(
        "/api/v1/public/jobs", params={"q": "analista", "limit": 1}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1


async def test_filtered_payload_has_no_contact_fields(db_session, client):
    await _insert(
        db_session,
        title="Analista de Dados",
        contact_email="segredo@example.com",
        contact_phone=None,
    )
    await _insert(db_session, title="Vendedor de Loja", city="Remoto")

    resp = await client.get("/api/v1/public/jobs", params={"q": "analista"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    for item in items:
        assert "contact_email" not in item
        assert "contact_phone" not in item

