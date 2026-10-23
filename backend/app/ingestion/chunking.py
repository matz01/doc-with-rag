"""Chunking: turn parsed blocks into embedding-sized chunks carrying their section.

Deterministic by construction: a pure function of the input blocks, no randomness and
no document-order surprises — re-ingesting an unchanged document must produce exactly
the same chunks, or the `content_hash` skip cannot be trusted.
"""

from dataclasses import dataclass

from app.ingestion.parsing import ParsedBlock


@dataclass(frozen=True)
class ChunkPlan:
    """One chunk of text ready for embedding; `section` is inherited from its blocks."""

    text: str
    section: str | None = None


def chunk_blocks(
    blocks: list[ParsedBlock],
    target_chars: int = 1400,
    overlap_chars: int = 200,
) -> list[ChunkPlan]:
    """Split parsed blocks into chunks, deterministically.

    Policy: blocks are slides and tables (already section-sized); chunking groups
    consecutive blocks of the same section up to `target_chars`, never mixing sections;
    a single block larger than the target is cut into overlapping character windows.
    Window cuts stay raw character positions on purpose: they keep the pinned
    overlap relation exactly, and semantic quality comes from bge-m3, not from
    word-boundary cosmetics.
    """
    chunks: list[ChunkPlan] = []
    group: list[str] = []
    # Sentinel start: no block seen yet, so even a None-section block may open a group.
    group_section: str | None = None
    group_started = False
    group_chars = 0

    def flush() -> None:
        nonlocal group, group_started, group_chars
        if group:
            chunks.append(ChunkPlan(text="\n\n".join(group), section=group_section))
        group = []
        group_started = False
        group_chars = 0

    for block in blocks:
        if not block.text.strip():
            continue
        if block.section != group_section or not group_started:
            flush()
        group_section = block.section
        group_started = True
        if len(block.text) > target_chars:
            for window in _sliding_windows(block.text, target_chars, overlap_chars):
                chunks.append(ChunkPlan(text=window, section=block.section))
        else:
            # +2 accounts for the "\n\n" separator this block would add when joined.
            if group and group_chars + len(block.text) + 2 > target_chars:
                flush()
                group_section = block.section
            group.append(block.text)
            group_chars += len(block.text)
    flush()
    return chunks


def _sliding_windows(text: str, target_chars: int, overlap_chars: int) -> list[str]:
    """Cut `text` into windows of at most `target_chars`, sharing `overlap_chars` tails.

    The step is target minus overlap, so the pinned invariant holds exactly: window n+1
    begins with the last `overlap_chars` of window n.
    """
    step = max(target_chars - overlap_chars, 1)
    windows = []
    start = 0
    while True:
        window = text[start : start + target_chars]
        # A window that only repeats the previous tail adds no new content.
        if len(window) <= overlap_chars and windows:
            break
        windows.append(window)
        if start + target_chars >= len(text):
            break
        start += step
    return windows
