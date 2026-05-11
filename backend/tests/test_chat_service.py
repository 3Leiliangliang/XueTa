from app.services.chat_service import split_message_for_stream


def test_split_message_for_stream_splits_chinese_text() -> None:
    content = "这是一个用于测试流式分片的回答。它会被拆成多个小块，以便前端逐步接收。"

    chunks = split_message_for_stream(content, chunk_size=12)

    assert len(chunks) >= 2
    assert "".join(chunks) == content
    assert all(len(chunk) <= 12 for chunk in chunks)


def test_split_message_for_stream_preserves_newlines() -> None:
    content = "第一行\n第二行\n第三行"

    chunks = split_message_for_stream(content, chunk_size=6)

    assert "".join(chunks) == content
    assert any("\n" in chunk for chunk in chunks)
