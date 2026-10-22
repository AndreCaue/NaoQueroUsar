from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Payload of the admin login (Phase 3, SECR-03).

    The Cloudflare Turnstile token is **mandatory**: the login only issues a
    JWT after the token is verified server-side, so a login without it is a
    422 (D-15/D-17).
    """

    password: str
    cf_token: str = Field(min_length=1, max_length=2048)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
