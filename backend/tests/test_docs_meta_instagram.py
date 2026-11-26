from pathlib import Path


DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "META-INTEGRATION-TESTING.md"


def test_meta_instagram_ops_doc_contains_required_phase29_contract() -> None:
    content = DOC_PATH.read_text(encoding="utf-8")
    content_lower = content.lower()

    required_strings = [
        "instagram_basic",
        "instagram_content_publish",
        "MEDIA_PUBLIC_BASE_URL",
        "instagram_business_account",
        "missing_linkage",
        "missing_permissions",
        "Reconectar",
    ]

    for expected in required_strings:
        assert expected in content, f"Missing required doc string: {expected}"

    assert (
        "handoff" in content_lower
        or "não marcar como aprovado sem execução real" in content_lower
    ), "Missing manual verification handoff boundary"

    # HARD-02 (Phase 32): rastreabilidade operacional IG publish / handoff
    hard02_required = [
        "ig_rate_limit_blocked",
        "content_publishing_limit",
        "IG_PUBLISH_HTTP_TIMEOUT_SECONDS",
    ]
    for expected in hard02_required:
        assert expected in content, f"Missing HARD-02 required doc string: {expected}"

    assert "não executado" in content_lower, "Missing HARD-02 handoff not-executed boundary"
