from kb.chunker import chunk_text


def test_chunking_non_empty():
    chunks = chunk_text("hello world " * 200, chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0


def test_empty_returns_none():
    assert chunk_text("", 100, 10) == []
