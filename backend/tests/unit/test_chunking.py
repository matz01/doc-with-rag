"""Unit tests for chunking: pure, deterministic block-to-chunk planning."""

from app.ingestion.chunking import ChunkPlan, chunk_blocks
from app.ingestion.parsing import ParsedBlock


def test_chunks_a_block_larger_than_the_target_into_overlapping_windows() -> None:
    """A block longer than target_chars is cut into windows that overlap."""
    long_block = ParsedBlock(text="word " * 400, section="Specs")  # 2000 chars

    chunks = chunk_blocks([long_block], target_chars=1000, overlap_chars=200)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.section == "Specs"
        assert len(chunk.text) < 1000 + 50
    for previous, following in zip(chunks[:-1], chunks[1:], strict=True):
        assert following.text.startswith(previous.text[-200:])


def test_merges_consecutive_blocks_of_the_same_section_up_to_the_target() -> None:
    """Small blocks of the same section are merged into one chunk, \\n\\n-joined."""
    blocks = [
        ParsedBlock(text="first " * 20, section="Policy"),
        ParsedBlock(text="second " * 15, section="Policy"),
        ParsedBlock(text="third " * 18, section="Policy"),
    ]

    chunks = chunk_blocks(blocks, target_chars=1400)

    assert len(chunks) == 1
    assert chunks[0].section == "Policy"
    assert chunks[0].text == ("first " * 20 + "\n\n" + "second " * 15 + "\n\n" + "third " * 18)


def test_never_mixes_two_sections_in_one_chunk() -> None:
    """A chunk boundary is forced at every section change."""
    blocks = [
        ParsedBlock(text="policy one " * 9, section="Policy"),
        ParsedBlock(text="policy two " * 9, section="Policy"),
        ParsedBlock(text="specs one " * 10, section="Specs"),
        ParsedBlock(text="specs two " * 10, section="Specs"),
    ]

    chunks = chunk_blocks(blocks, target_chars=1400, overlap_chars=200)

    assert len(chunks) == 2
    assert chunks[0].section == "Policy"
    assert chunks[0].text == "policy one " * 9 + "\n\n" + "policy two " * 9
    assert chunks[1].section == "Specs"
    assert chunks[1].text == "specs one " * 10 + "\n\n" + "specs two " * 10


def test_keeps_chunk_text_non_empty_for_empty_and_whitespace_blocks() -> None:
    """Empty and whitespace-only blocks are dropped, never emitted as chunks."""
    blocks = [ParsedBlock(text=""), ParsedBlock(text="   ")]

    chunks = chunk_blocks(blocks)

    assert chunks == []


def test_is_deterministic_for_identical_inputs() -> None:
    """Calling chunk_blocks twice on the same input returns equal chunk lists."""
    blocks = [
        ParsedBlock(text="word " * 300, section="Specs"),
        ParsedBlock(text="policy one " * 9, section="Policy"),
        ParsedBlock(text="policy two " * 9, section="Policy"),
        ParsedBlock(text="unsectioned block"),
    ]

    first_run = chunk_blocks(blocks)
    second_run = chunk_blocks(blocks, target_chars=1400, overlap_chars=200)

    assert first_run == second_run
    assert all(isinstance(chunk, ChunkPlan) for chunk in first_run)
