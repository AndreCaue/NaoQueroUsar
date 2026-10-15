# Deferred Items — Phase 01

Items acknowledged during execution and carried forward (out of scope for the
plan that discovered them).

| Category | Item | Reason deferred | Discovered in |
|----------|------|-----------------|---------------|
| Dependency hygiene | Replace `passlib[bcrypt]>=1.7.4,<2.0.0` with a direct `bcrypt` (or `argon2-cffi`) dependency and re-lock (`uv lock`) | passlib 1.7.4 is unmaintained and incompatible with the locked `bcrypt==5.0.0`; plan 01-03 worked around it by using `bcrypt` directly. Cleaning the dependency requires `uv`/`pip`, neither available in the executor environment. | plan 01-03 (task 1) |
