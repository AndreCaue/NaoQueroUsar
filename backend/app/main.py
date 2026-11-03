from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.ratelimit import RateLimitExceeded, limiter, rate_limit_exceeded_handler
from app.core.scheduler import shutdown_scheduler, start_scheduler
from app.db.session import engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # LIFE-02: the daily expiry sweep runs inside this process (D-01). The
    # scheduler is stopped before the engine is disposed so no sweep starts
    # against a closed pool during shutdown.
    start_scheduler()
    try:
        yield
    finally:
        # WR-05: stop the scheduler and drain in-flight sweeps BEFORE the
        # pool is disposed — dispose() must never close connections under a
        # running DELETE.
        await shutdown_scheduler()
        await engine.dispose()


def create_app() -> FastAPI:
    configure_logging(settings.ENV)

    app = FastAPI(title="NQU API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
        # `Retry-After` is not CORS-safelisted, so the reveal 429 countdown
        # would silently fall back to 10s without this (D-10b/T-04-16).
        expose_headers=["Retry-After"],
        allow_credentials=False,
    )

    # Rate limiting: the limiter instance lives on the app state and the 429
    # answer is ours — slowapi's default handler replies in English with a
    # body the frontend cannot read.
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
