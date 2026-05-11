from app.services.llm import service as llm_service


def test_generate_chat_reply_returns_none_when_completion_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(llm_service, "_create_completion", lambda **_: None)

    assert llm_service.generate_chat_reply("解释一下极限") is None



def test_generate_note_summary_parses_json_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        llm_service,
        "_create_completion",
        lambda **_: (
            '{"summary_text":"这份笔记讲了极限定义。","suggestions":["补例题","补易错点","补概念对比"]}',
            "gpt-test",
        ),
    )

    result = llm_service.generate_note_summary(
        title="极限笔记",
        content_markdown="定义\n性质\n例题",
    )

    assert result is not None
    summary_text, suggestions, model_name = result
    assert summary_text == "这份笔记讲了极限定义。"
    assert suggestions == {"suggestions": ["补例题", "补易错点", "补概念对比"]}
    assert model_name == "gpt-test"



def test_generate_note_summary_fills_default_suggestions(monkeypatch) -> None:
    monkeypatch.setattr(
        llm_service,
        "_create_completion",
        lambda **_: (
            '{"summary_text":"这份笔记重点在函数单调性。","suggestions":["补典型例题"]}',
            "gpt-test",
        ),
    )

    result = llm_service.generate_note_summary(
        title="单调性",
        content_markdown="定义\n判定\n应用",
    )

    assert result is not None
    summary_text, suggestions, model_name = result
    assert summary_text == "这份笔记重点在函数单调性。"
    assert len(suggestions["suggestions"]) == 3
    assert model_name == "gpt-test"



def test_generate_embeddings_returns_hashing_fallback_vectors(monkeypatch) -> None:
    monkeypatch.setattr(llm_service, '_create_embeddings', lambda texts: None)

    vectors, model_name = llm_service.generate_embeddings(['limit theorem', 'derivative rule'])

    assert model_name.startswith('hashing-fallback-')
    assert len(vectors) == 2
    assert len(vectors[0]) == llm_service.EMBEDDING_DIMENSIONS
    assert vectors[0] != vectors[1]



def test_generate_embedding_reuses_batch_embedding_logic(monkeypatch) -> None:
    monkeypatch.setattr(
        llm_service,
        'generate_embeddings',
        lambda texts: ([[0.5, 0.5] + [0.0] * (llm_service.EMBEDDING_DIMENSIONS - 2)], 'test-embed'),
    )

    vector, model_name = llm_service.generate_embedding('limit')

    assert model_name == 'test-embed'
    assert vector[:2] == [0.5, 0.5]
