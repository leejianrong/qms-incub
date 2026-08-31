from qms_incub.ingestion.chunking import chunk_text


def test_chunk_text_splits_long_text_under_target_size() -> None:
    # ~5000 words, well over the default 512-token chunk size.
    long_text = " ".join(f"sentence number {i}." for i in range(1200))

    chunks = chunk_text(long_text, chunk_size=100, chunk_overlap=10)

    assert len(chunks) > 1
    for chunk in chunks:
        # Rough token proxy: word count should stay near the target size.
        assert len(chunk.split()) <= 150


def test_chunk_text_returns_single_chunk_for_short_text() -> None:
    chunks = chunk_text("A short policy statement.")
    assert chunks == ["A short policy statement."]


def test_chunk_text_empty_string_returns_no_chunks() -> None:
    assert chunk_text("") == []
