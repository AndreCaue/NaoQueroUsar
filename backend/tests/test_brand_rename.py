"""Guard (BRND-01): no leftover legacy brand tokens in frontend/backend source."""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXCLUDED_DIRS = {"node_modules", ".next", "__pycache__", ".venv", ".planning"}
EXCLUDED_FILES = {"uv.lock", "test_brand_rename.py"}
SUFFIXES = {".py", ".toml", ".ini", ".md", ".ps1", ".yaml", ".yml", ".ts", ".tsx", ".js", ".jsx", ".css", ".example"}
NEEDLES = ("NaoQueroUsar", "NQU", "suportenqs")

def _is_excluded(path: pathlib.Path) -> bool:
    if path.name in EXCLUDED_FILES:
        return True
    return any(part in EXCLUDED_DIRS for part in path.parts)

def _scan(root: pathlib.Path) -> list[tuple[str, str]]:
    offenders = []
    if not root.exists():
        return offenders
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if _is_excluded(p):
            continue
        if p.suffix not in SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for needle in NEEDLES:
            if needle in text:
                offenders.append((str(p), needle))
    return offenders

def test_no_leftover_brand():
    offenders = _scan(ROOT / "frontend") + _scan(ROOT / "backend")
    assert not offenders, offenders
