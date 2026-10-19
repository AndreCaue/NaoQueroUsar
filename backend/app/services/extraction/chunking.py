"""Delimiter-aware chunker keeping each chunk under a token budget.

Threat T-02-03 (DoS): pure function, bounded input upstream by
``EXTRACT_MAX_TEXT_BYTES``, no unbounded loops (every split strictly
decreases the slice being packed).

Token estimate: ``len(text) // 4`` — a documented heuristic
(``EXTRACT_CHUNK_MAX_TOKENS=3500`` ≈ 14K chars ≈ safely under Groq's free
8K TPM with headroom for prompt overhead).

Strategy (all chunks are contiguous exact slices of the input — no text is
ever dropped or reordered):
1. Split on blank-line (paragraph) boundaries first; small paragraphs are
   packed whole (splitting prefers the blank-line boundary over any point
   inside a paragraph).
2. A paragraph larger than the budget is split on ``\\n`` line boundaries;
   an oversized single line is split on whitespace (word) boundaries.
3. Hard floor: a single un-splittable token larger than the budget is
   still emitted as its own chunk — text is NEVER dropped and no
   whitespace-only/empty chunk is ever produced.

Contract (losslessness): chunks tile the input, so whitespace-normalized
concatenation equals the whitespace-normalized original:
    ``' '.join(''.join(chunks).split()) == ' '.join(text.split())``
"""

import re

_PARAGRAPH = re.compile(r"\n\s*\n+")
_LINE = re.compile(r"[^\n]+\n*")
_WORD_OR_SPACE = re.compile(r"\s+|\S+")


def estimate_tokens(text: str) -> int:
    """Heuristic token estimate: ~4 characters per token (len // 4)."""
    return len(text) // 4


def _expand_block(
    text: str, start: int, end: int, budget: int
) -> list[tuple[int, int, str]]:
    """Tile one content block into packable items (each ≤ budget when possible).

    Level 1: the block itself. Level 2: lines (never mid-word). Level 3:
    whitespace/word runs. A token larger than the budget becomes its own
    item (hard floor — emitted, never dropped).
    """
    if end - start <= budget:
        return [(start, end, "content")]

    lines = [(start + m.start(), start + m.end(), "content")
             for m in _LINE.finditer(text[start:end])]
    if all(e2 - s2 <= budget for s2, e2, _ in lines):
        return lines

    words = []
    for m in _WORD_OR_SPACE.finditer(text[start:end]):
        kind = "ws" if m.group().isspace() else "content"
        words.append((start + m.start(), start + m.end(), kind))
    return words


def chunk_text(text: str, max_tokens: int) -> list[str]:
    """Split ``text`` into contiguous chunks of at most ``max_tokens`` each.

    Returns ``[]`` for empty/whitespace-only input. Chunks tile the input
    exactly (joined they reconstruct it), paragraph boundaries are
    preferred cut points, and no empty chunk is ever emitted.
    """
    if not text or not text.strip():
        return []
    budget = max(max_tokens * 4, 1)

    # Level 1: paragraph segments (content + separator) tiling the text.
    segments: list[tuple[int, int, str]] = []
    last = 0
    for m in _PARAGRAPH.finditer(text):
        if m.start() > last:
            segments.append((last, m.start(), "content"))
        segments.append((m.start(), m.end(), "ws"))
        last = m.end()
    if last < len(text):
        segments.append((last, len(text), "content"))

    # Expand oversized content blocks; collect all items (still a tiling).
    items: list[tuple[int, int, str]] = []
    for start, end, kind in segments:
        if kind == "ws":
            items.append((start, end, "ws"))
        else:
            items.extend(_expand_block(text, start, end, budget))

    # Greedy pack. A whitespace separator is tentatively part of the
    # current chunk; if the next content item overflows, the cut lands at
    # the paragraph/word boundary (content_end) so the separator travels
    # with the following chunk and every chunk stays ≤ budget.
    chunks: list[str] = []
    slice_start = 0
    content_end = -1  # end of the last content item in the current slice
    for start, end, kind in items:
        if kind == "ws":
            continue
        if content_end >= 0 and end - slice_start > budget:
            chunks.append(text[slice_start:content_end])
            slice_start = content_end
        content_end = end

    tail = text[slice_start:]
    if tail.strip():
        chunks.append(tail.rstrip())
    return chunks
