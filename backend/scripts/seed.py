"""Seed one published job for manual verification (D-22).

Run from ``backend/`` (uses ``DATABASE_URL`` from the environment/.env):

    uv run python scripts/seed.py

The job carries a phone contact so the ``at_least_one_contact`` CHECK
passes, and is created with ``status=published`` so it shows up in
``GET /api/v1/public/jobs`` immediately.
"""

import asyncio
import sys
from pathlib import Path

# Make ``app`` importable when this file is run directly
# (``python scripts/seed.py`` puts ``scripts/`` — not ``backend/`` — on
# sys.path).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import async_session_factory  # noqa: E402
from app.models.job import Job, JobStatus  # noqa: E402


async def main() -> None:
    async with async_session_factory() as session:
        job = Job(
            title="Analista de Suporte — SEED",
            company="NQU Seed",
            activities="Atendimento ao cliente e suporte técnico de primeiro nível.",
            requirements="Boa comunicação e disponibilidade para escala.",
            salary="A combinar",
            benefits=None,
            city="Remoto",
            contact_email=None,
            contact_phone="+55 11 90000-0000",
            status=JobStatus.published,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        print(f"Seeded published job id={job.id}")


if __name__ == "__main__":
    asyncio.run(main())
