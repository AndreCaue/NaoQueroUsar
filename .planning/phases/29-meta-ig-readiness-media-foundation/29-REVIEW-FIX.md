---
phase: 29-meta-ig-readiness-media-foundation
fixed_at: 2026-11-23T14:30:41-03:00
review_path: .planning/phases/29-meta-ig-readiness-media-foundation/29-REVIEW.md
iteration: 1
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 29: Code Review Fix Report

**Fixed at:** 2026-11-23T14:30:41-03:00
**Source review:** .planning/phases/29-meta-ig-readiness-media-foundation/29-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 2
- Fixed: 2
- Skipped: 0

## Fixed Issues

### WR-01: Dead disconnect code contains a hardcoded Fernet-key-shaped constant

**Files modified:** `backend/app/services/social/meta_oauth.py`
**Commit:** a00f142
**Applied fix:** Removed the unreachable `if False` dead branch that built an encrypted token with a hardcoded Fernet-key-shaped literal, and removed the misleading comment. `disconnect_meta` now only deletes the active Facebook `SocialAccount` record (if present), clears pending OAuth rows, flushes, and returns the disconnected response.

### WR-02: IG media upsert is vulnerable to concurrent insert race

**Files modified:** `backend/app/crud/social_media.py`
**Commit:** 6f51683
**Applied fix:** Replaced the check-then-insert/flush upsert with a PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` on `uq_social_media_assets_job_provider_version`, returning the `SocialMediaAsset`. This makes concurrent cache-miss requests for the same `job_id + provider + version_hash` safe and prevents `IntegrityError`/500 responses. Existing callers (`image_media.py` prepare/public paths) continue to own transaction commit behavior.

---

_Fixed: 2026-11-23T14:30:41-03:00_
_Fixer: OpenCode (gsd-code-fixer)_
_Iteration: 1_
