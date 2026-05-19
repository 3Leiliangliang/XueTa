
def test_kb_document_chunk_and_retrieve_flow(client) -> None:
    base_response = client.post(
        "/api/v1/kb/bases",
        json={"name": "数学资料", "subject": "math", "description": "高数知识库"},
    )
    assert base_response.status_code == 201
    base = base_response.json()
    base_id = base["id"]

    document_response = client.post(
        "/api/v1/kb/documents",
        json={
            "knowledge_base_id": base_id,
            "title": "函数极限讲义",
            "source_type": "manual",
            "content_text": "函数极限是高等数学中的重要概念。\n\n求极限时需要先看定义，再看条件与典型题型。",
        },
    )
    assert document_response.status_code == 201
    document = document_response.json()
    document_id = document["id"]
    assert document["chunk_count"] >= 1

    documents_list_response = client.get("/api/v1/kb/documents", params={"knowledge_base_id": base_id})
    assert documents_list_response.status_code == 200
    assert len(documents_list_response.json()) == 1

    chunks_response = client.get(f"/api/v1/kb/documents/{document_id}/chunks")
    assert chunks_response.status_code == 200
    chunks = chunks_response.json()
    assert len(chunks) >= 1
    assert chunks[0]["document_id"] == document_id

    retrieve_response = client.post(
        "/api/v1/kb/retrieve",
        json={"query": "极限", "knowledge_base_id": base_id, "limit": 3},
    )
    assert retrieve_response.status_code == 200
    retrieve_payload = retrieve_response.json()
    assert retrieve_payload["total_hits"] >= 1
    assert retrieve_payload["hits"][0]["document_title"] == "函数极限讲义"



def test_chat_sync_and_stream_endpoints(client) -> None:
    session_response = client.post("/api/v1/chat/sessions", json={"subject": "math", "title": "极限答疑"})
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    sync_response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "请解释一下函数极限"},
    )
    assert sync_response.status_code == 201
    sync_payload = sync_response.json()
    assert sync_payload["assistant_message"]["model_name"] == "rule-based-draft"
    assert "函数极限" in sync_payload["assistant_message"]["content"]

    stream_response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages/stream",
        json={"content": "再举一个简单例子"},
    )
    assert stream_response.status_code == 200
    assert stream_response.headers["content-type"].startswith("text/event-stream")
    assert "event: message_start" in stream_response.text
    assert "event: message_end" in stream_response.text
    assert "event: done" in stream_response.text

    messages_response = client.get(f"/api/v1/chat/sessions/{session_id}/messages")
    assert messages_response.status_code == 200
    assert len(messages_response.json()) == 4



def test_note_summarize_endpoint_falls_back_to_rule_based(client) -> None:
    notebook_response = client.post(
        "/api/v1/notes/notebooks",
        json={"name": "高数笔记", "description": "积分与极限"},
    )
    assert notebook_response.status_code == 201
    notebook_id = notebook_response.json()["id"]

    note_response = client.post(
        "/api/v1/notes",
        json={
            "notebook_id": notebook_id,
            "title": "函数极限整理",
            "content_markdown": "定义\n左右极限\n典型例题",
        },
    )
    assert note_response.status_code == 201
    note_id = note_response.json()["id"]

    summarize_response = client.post(f"/api/v1/notes/{note_id}/summarize")
    assert summarize_response.status_code == 201
    summary = summarize_response.json()
    assert summary["model_name"] == "rule-based-draft"
    assert "函数极限整理" in summary["summary_text"] or "定义" in summary["summary_text"]
    assert len(summary["suggestions_json"]["suggestions"]) == 3


def test_notes_can_create_blank_notebook_and_blank_note(client) -> None:
    notebook_response = client.post(
        "/api/v1/notes/notebooks",
        json={"name": "", "description": "   ", "color": "#10B981"},
    )
    assert notebook_response.status_code == 201
    notebook = notebook_response.json()
    assert notebook["name"] == "新建笔记本 1"
    assert notebook["description"] is None
    assert notebook["color"] == "#10B981"
    assert notebook["note_count"] == 0

    note_response = client.post(
        "/api/v1/notes",
        json={
            "notebook_id": notebook["id"],
            "title": "",
            "content_markdown": "",
        },
    )
    assert note_response.status_code == 201
    note = note_response.json()
    assert note["title"] == "未命名笔记"
    assert note["content_markdown"] == ""
    assert note["notebook_id"] == notebook["id"]

    notebooks_response = client.get("/api/v1/notes/notebooks")
    assert notebooks_response.status_code == 200
    assert notebooks_response.json()[0]["note_count"] == 1


def test_note_create_without_notebook_uses_default_notebook(client) -> None:
    note_response = client.post("/api/v1/notes", json={})
    assert note_response.status_code == 201
    note = note_response.json()
    assert note["title"] == "未命名笔记"
    assert note["content_markdown"] == ""
    assert note["notebook_id"] is not None

    notebooks_response = client.get("/api/v1/notes/notebooks")
    assert notebooks_response.status_code == 200
    notebooks = notebooks_response.json()
    assert len(notebooks) == 1
    assert notebooks[0]["name"] == "默认笔记本"
    assert notebooks[0]["note_count"] == 1


from app.services.rag import service as rag_service


def test_kb_document_can_extract_content_from_source_url(client, monkeypatch) -> None:
    monkeypatch.setattr(
        rag_service,
        'extract_text_from_url',
        lambda url: ('???????????', {'kind': 'html', 'resolved_url': url, 'mime_type': 'text/html'}),
    )

    base_response = client.post(
        "/api/v1/kb/bases",
        json={"name": "????", "subject": "cs"},
    )
    assert base_response.status_code == 201
    base_id = base_response.json()["id"]

    document_response = client.post(
        "/api/v1/kb/documents",
        json={
            "knowledge_base_id": base_id,
            "title": "??????",
            "source_type": "web",
            "source_url": "https://example.com/article",
        },
    )
    assert document_response.status_code == 201
    payload = document_response.json()
    assert payload["source_url"] == "https://example.com/article"
    assert payload["content_text"] == '???????????'
    assert payload["chunk_count"] >= 1



def test_kb_document_creates_embeddings_and_supports_vector_retrieve(client, session_factory, monkeypatch) -> None:
    from app.models.knowledge import KnowledgeChunkEmbedding
    from app.services.rag import service as rag_service

    def make_vector(slot: int) -> list[float]:
        vector = [0.0] * 1536
        vector[slot] = 1.0
        return vector

    monkeypatch.setattr(
        rag_service,
        'generate_embeddings',
        lambda texts: (
            [make_vector(0) if 'topic-a' in text else make_vector(1) for text in texts],
            'test-embedding',
        ),
    )
    monkeypatch.setattr(
        rag_service,
        'generate_embedding',
        lambda text: (make_vector(1), 'test-embedding'),
    )

    base_response = client.post(
        "/api/v1/kb/bases",
        json={"name": "vector-base", "subject": "math"},
    )
    assert base_response.status_code == 201
    base_id = base_response.json()["id"]

    first_doc = client.post(
        "/api/v1/kb/documents",
        json={
            "knowledge_base_id": base_id,
            "title": "Doc A",
            "source_type": "manual",
            "content_text": "content for topic-a only",
        },
    )
    assert first_doc.status_code == 201

    second_doc = client.post(
        "/api/v1/kb/documents",
        json={
            "knowledge_base_id": base_id,
            "title": "Doc B",
            "source_type": "manual",
            "content_text": "content for topic-b only",
        },
    )
    assert second_doc.status_code == 201

    with session_factory() as db:
        embedding_count = db.query(KnowledgeChunkEmbedding).count()
        assert embedding_count == 2

    retrieve_response = client.post(
        "/api/v1/kb/retrieve",
        json={"query": "latent semantic query", "knowledge_base_id": base_id, "limit": 2},
    )
    assert retrieve_response.status_code == 200
    payload = retrieve_response.json()
    assert payload["total_hits"] >= 1
    assert payload["hits"][0]["document_title"] == "Doc B"


def test_kb_document_pads_short_embedding_vectors(client, session_factory, monkeypatch) -> None:
    from app.models.knowledge import KnowledgeChunkEmbedding
    from app.services.rag import service as rag_service

    monkeypatch.setattr(
        rag_service,
        'generate_embeddings',
        lambda texts: ([[0.25] * 1024 for _ in texts], 'short-embedding-model'),
    )

    base_response = client.post(
        "/api/v1/kb/bases",
        json={"name": "short-vector-base", "subject": "math"},
    )
    assert base_response.status_code == 201
    base_id = base_response.json()["id"]

    document_response = client.post(
        "/api/v1/kb/documents",
        json={
            "knowledge_base_id": base_id,
            "title": "Short Vector Doc",
            "source_type": "manual",
            "content_text": "content that receives a 1024 dimension embedding",
        },
    )
    assert document_response.status_code == 201

    with session_factory() as db:
        embedding = db.query(KnowledgeChunkEmbedding).one()
        assert embedding.dimensions == 1536
        assert embedding.chunk.metadata_json["original_embedding_dimensions"] == 1024



def test_chat_response_includes_rag_citations_when_kb_matches(client, monkeypatch) -> None:
    from app.services import chat_service

    monkeypatch.setattr(chat_service, 'generate_chat_reply', lambda question, subject=None, retrieved_chunks=None: None)

    base_response = client.post(
        "/api/v1/kb/bases",
        json={"name": "math-rag", "subject": "math"},
    )
    assert base_response.status_code == 201
    base_id = base_response.json()["id"]

    document_response = client.post(
        "/api/v1/kb/documents",
        json={
            "knowledge_base_id": base_id,
            "title": "Limit Notes",
            "source_type": "manual",
            "content_text": "The limit of a function describes the value that the function approaches.",
        },
    )
    assert document_response.status_code == 201

    session_response = client.post(
        "/api/v1/chat/sessions",
        json={"subject": "math", "title": "RAG Session"},
    )
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    message_response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "What is the limit of a function?"},
    )
    assert message_response.status_code == 201
    payload = message_response.json()
    assistant_message = payload["assistant_message"]
    assert assistant_message["model_name"] == "rule-based-draft"
    assert assistant_message["citations_json"]
    assert assistant_message["citations_json"][0]["document_title"] == "Limit Notes"



def test_chat_stream_endpoint_uses_true_stream_deltas(client, monkeypatch) -> None:
    from app.api.v1 import chat as chat_api

    session_response = client.post(
        "/api/v1/chat/sessions",
        json={"subject": "math", "title": "Streaming Session"},
    )
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    monkeypatch.setattr(
        chat_api,
        'open_chat_reply_stream',
        lambda question, subject=None, retrieved_chunks=None: (iter(['chunk-1 ', 'chunk-2']), {'model_name': 'stream-test-model'}),
    )

    stream_response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages/stream",
        json={"content": "stream this answer"},
    )
    assert stream_response.status_code == 200
    assert 'event: delta' in stream_response.text
    assert 'chunk-1 ' in stream_response.text
    assert 'chunk-2' in stream_response.text

    messages_response = client.get(f"/api/v1/chat/sessions/{session_id}/messages")
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert len(messages) == 2
    assistant_message = messages[-1]
    assert assistant_message['model_name'] == 'stream-test-model'
    assert assistant_message['content'] == 'chunk-1 chunk-2'
