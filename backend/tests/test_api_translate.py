
def test_translate_text_endpoint_returns_translation_payload(client) -> None:
    response = client.post(
        '/api/v1/translate/text',
        json={
            'source_text': 'Machine learning is built on data and algorithms.',
            'source_language': '英语',
            'target_language': '中文',
            'mode': 'academic',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['source_language'] == '英语'
    assert payload['target_language'] == '中文'
    assert payload['mode'] == 'academic'
    assert payload['translated_text']
    assert payload['model_name']



def test_translate_polish_endpoint_returns_polished_text(client) -> None:
    response = client.post(
        '/api/v1/translate/polish',
        json={
            'text': '机器学习, 是 人工智能 的 一个 分支.',
            'language': '中文',
            'mode': 'academic',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['original_text'] == '机器学习, 是 人工智能 的 一个 分支.'
    assert payload['polished_text']
    assert payload['language'] == '中文'
    assert payload['mode'] == 'academic'
    assert payload['model_name']
