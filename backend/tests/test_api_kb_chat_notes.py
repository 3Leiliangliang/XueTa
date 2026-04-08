
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
