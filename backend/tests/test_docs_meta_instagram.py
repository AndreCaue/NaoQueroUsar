from pathlib import Path


DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "META-INTEGRATION-TESTING.md"


def test_meta_instagram_ops_doc_contains_required_phase29_contract() -> None:
    content = DOC_PATH.read_text(encoding="utf-8")

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
        "handoff" in content.lower()
        or "não marcar como aprovado sem execução real" in content.lower()
    ), "Missing manual verification handoff boundary"
