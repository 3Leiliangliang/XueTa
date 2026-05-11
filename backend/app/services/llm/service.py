from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from functools import lru_cache
from typing import Iterator

from app.core.config import settings
from app.core.langfuse import safe_log_generation


logger = logging.getLogger(__name__)
EMBEDDING_DIMENSIONS = 1536
EMBEDDING_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


@lru_cache(maxsize=1)
def _get_openai_client():
    if not settings.openai_api_key:
        return None

    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover - depends on runtime install state
        logger.warning("OpenAI client is unavailable: %s", exc)
        return None

    kwargs = {
        'api_key': settings.openai_api_key,
        'timeout': settings.openai_timeout_seconds,
    }
    if settings.openai_base_url:
        kwargs['base_url'] = settings.openai_base_url

    return OpenAI(**kwargs)


def _create_completion(
    *,
    messages: list[dict[str, str]],
    temperature: float = 0.4,
    max_tokens: int = 900,
    response_format: dict | None = None,
    trace_name: str = "openai.chat.completions",
) -> tuple[str, str] | None:
    client = _get_openai_client()
    if client is None:
        return None

    kwargs = {
        'model': settings.openai_model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    if response_format is not None:
        kwargs['response_format'] = response_format

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        logger.warning('OpenAI completion request failed: %s', exc)
        return None

    if not getattr(response, 'choices', None):
        return None

    message = response.choices[0].message
    content = (message.content or '').strip()
    if not content:
        return None

    model_name = getattr(response, 'model', None) or settings.openai_model
    safe_log_generation(
        name=trace_name,
        model=model_name,
        input_payload={
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": response_format,
        },
        output_payload={"content": content},
        metadata={"provider": "openai"},
    )
    return content, model_name


def _create_embeddings(texts: list[str]) -> tuple[list[list[float]], str] | None:
    client = _get_openai_client()
    if client is None:
        return None

    try:
        response = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=[text[:8000] for text in texts],
        )
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        logger.warning('OpenAI embedding request failed: %s', exc)
        return None

    if not getattr(response, 'data', None):
        return None

    data = sorted(response.data, key=lambda item: item.index)
    vectors = [list(item.embedding) for item in data]
    if len(vectors) != len(texts):
        return None

    model_name = getattr(response, 'model', None) or settings.openai_embedding_model
    safe_log_generation(
        name="openai.embeddings",
        model=model_name,
        input_payload={"inputs": [text[:1200] for text in texts]},
        output_payload={"vector_count": len(vectors)},
        metadata={"provider": "openai"},
    )
    return vectors, model_name


def _normalize_embedding(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0:
        return vector
    return [value / norm for value in vector]


def _tokenize_for_embedding(text: str) -> list[str]:
    lowered = text.lower()
    tokens = EMBEDDING_TOKEN_RE.findall(lowered)
    if not tokens:
        return [lowered[:64] or '']

    extended = list(tokens)
    if len(tokens) > 1:
        extended.extend(f'{tokens[index]}::{tokens[index + 1]}' for index in range(len(tokens) - 1))
    return extended


def _stable_token_hash(token: str, salt: str) -> int:
    digest = hashlib.sha256(f'{salt}:{token}'.encode('utf-8')).digest()
    return int.from_bytes(digest[:8], 'big')


def _fallback_embedding(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    tokens = _tokenize_for_embedding(text)

    for index, token in enumerate(tokens, start=1):
        primary_slot = _stable_token_hash(token, 'primary') % EMBEDDING_DIMENSIONS
        secondary_slot = _stable_token_hash(token, 'secondary') % EMBEDDING_DIMENSIONS
        weight = 1.0 + min(len(token), 12) * 0.08 + index * 0.001
        vector[primary_slot] += weight
        vector[secondary_slot] += weight * 0.35

    return _normalize_embedding(vector)


def generate_embeddings(texts: list[str]) -> tuple[list[list[float]], str]:
    normalized_texts = [(text or '').strip() for text in texts]
    if not normalized_texts:
        return [], settings.openai_embedding_model

    result = _create_embeddings(normalized_texts)
    if result is not None:
        return result

    vectors = [_fallback_embedding(text) for text in normalized_texts]
    fallback_model = f'hashing-fallback-{EMBEDDING_DIMENSIONS}'
    safe_log_generation(
        name="fallback.embeddings",
        model=fallback_model,
        input_payload={"inputs": [text[:1200] for text in normalized_texts]},
        output_payload={"vector_count": len(vectors)},
        metadata={"provider": "fallback"},
    )
    return vectors, fallback_model


def generate_embedding(text: str) -> tuple[list[float], str]:
    vectors, model_name = generate_embeddings([text])
    if not vectors:
        return [0.0] * EMBEDDING_DIMENSIONS, model_name
    return vectors[0], model_name


def _build_chat_messages(
    question: str,
    subject: str | None = None,
    retrieved_chunks: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    topic = subject or 'general topic'
    prompt = (
        'You are XueTa\'s study assistant. Reply in Simplified Chinese.\n'
        '1. Start with a short summary of the question.\n'
        '2. Then explain the answer step by step.\n'
        '3. If reference material is provided, ground the answer in that material.\n'
        '4. If references are used, add citation markers like [1] or [2] inline.\n'
        '5. End with a short example or review suggestion.'
    )

    context_block = ''
    if retrieved_chunks:
        context_items = []
        for index, item in enumerate(retrieved_chunks[:4], start=1):
            document_title = item.get('document_title') or f'reference-{index}'
            content_text = (item.get('content') or '').strip()[:800]
            if not content_text:
                continue
            context_items.append(f'[{index}] {document_title}\n{content_text}')
        if context_items:
            context_block = '\n\nReference materials:\n' + '\n\n'.join(context_items)

    return [
        {'role': 'system', 'content': prompt},
        {
            'role': 'user',
            'content': f'Subject/topic: {topic}\n\nQuestion: {question.strip()}{context_block}',
        },
    ]


def generate_chat_reply(
    question: str,
    subject: str | None = None,
    retrieved_chunks: list[dict[str, str]] | None = None,
) -> tuple[str, str] | None:
    return _create_completion(
        messages=_build_chat_messages(question, subject, retrieved_chunks),
        temperature=0.35,
        max_tokens=900,
        trace_name="chat.reply",
    )


def _normalize_stream_delta(content: object) -> str:
    if content is None:
        return ''
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        fragments: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text_value = item.get('text')
                if isinstance(text_value, str):
                    fragments.append(text_value)
            else:
                text_value = getattr(item, 'text', None)
                if isinstance(text_value, str):
                    fragments.append(text_value)
        return ''.join(fragments)
    return ''


def open_chat_reply_stream(
    question: str,
    subject: str | None = None,
    retrieved_chunks: list[dict[str, str]] | None = None,
) -> tuple[Iterator[str], dict[str, str]] | None:
    client = _get_openai_client()
    if client is None:
        return None

    messages = _build_chat_messages(question, subject, retrieved_chunks)
    state = {'model_name': settings.openai_model}
    collected: list[str] = []

    try:
        stream = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.35,
            max_tokens=900,
            stream=True,
        )
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        logger.warning('OpenAI streaming request failed: %s', exc)
        return None

    def iterator() -> Iterator[str]:
        for chunk in stream:
            if getattr(chunk, 'model', None):
                state['model_name'] = chunk.model
            if not getattr(chunk, 'choices', None):
                continue
            delta = getattr(chunk.choices[0].delta, 'content', None)
            normalized = _normalize_stream_delta(delta)
            if normalized:
                collected.append(normalized)
                yield normalized
        if collected:
            safe_log_generation(
                name="chat.reply.stream",
                model=state.get("model_name", settings.openai_model),
                input_payload={"messages": messages, "stream": True},
                output_payload={"content": ''.join(collected)},
                metadata={"provider": "openai"},
            )

    return iterator(), state


def translate_text_with_model(
    *,
    source_text: str,
    source_language: str,
    target_language: str,
    mode: str,
) -> tuple[str, str] | None:
    prompt = (
        'You are a translation assistant. Output translation only.\n'
        '1. Preserve paragraph structure.\n'
        '2. In academic mode, be formal and accurate; in colloquial mode, be natural.\n'
        '3. If source and target language are the same, lightly polish the original text.'
    )
    return _create_completion(
        messages=[
            {'role': 'system', 'content': prompt},
            {
                'role': 'user',
                'content': (
                    f'Source language: {source_language}\n'
                    f'Target language: {target_language}\n'
                    f'Style: {mode}\n\n'
                    f'Text to translate:\n{source_text.strip()[:8000]}'
                ),
            },
        ],
        temperature=0.2,
        max_tokens=1200,
        trace_name="translate.text",
    )


def polish_text_with_model(
    *,
    text: str,
    language: str,
    mode: str,
) -> tuple[str, str] | None:
    prompt = (
        'You are a text polishing assistant. Output polished text only.\n'
        '1. Preserve the original meaning.\n'
        '2. In academic mode, be formal and rigorous; in colloquial mode, be natural.\n'
        '3. Preserve the original paragraph structure.'
    )
    return _create_completion(
        messages=[
            {'role': 'system', 'content': prompt},
            {
                'role': 'user',
                'content': (
                    f'Language: {language}\n'
                    f'Style: {mode}\n\n'
                    f'Text to polish:\n{text.strip()[:8000]}'
                ),
            },
        ],
        temperature=0.2,
        max_tokens=900,
        trace_name="translate.polish",
    )


def _extract_json_payload(content: str) -> dict | None:
    text = content.strip()
    if not text:
        return None

    candidates = [text]
    fenced = re.search(r'```json\s*(\{.*\})\s*```', text, flags=re.DOTALL)
    if fenced:
        candidates.insert(0, fenced.group(1).strip())

    generic = re.search(r'(\{.*\})', text, flags=re.DOTALL)
    if generic:
        candidates.append(generic.group(1).strip())

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload

    return None


def generate_note_summary(
    *,
    title: str,
    content_markdown: str,
) -> tuple[str, dict, str] | None:
    prompt = (
        'Return a JSON object with two fields only.\n'
        'summary_text: summarize the note in 2-5 sentences.\n'
        'suggestions: provide 3 concrete review suggestions.\n'
        'Do not output anything outside JSON.'
    )
    source = content_markdown.strip()[:6000]
    result = _create_completion(
        messages=[
            {'role': 'system', 'content': prompt},
            {
                'role': 'user',
                'content': f'Title: {title.strip()}\n\nNote content:\n{source}',
            },
        ],
        temperature=0.2,
        max_tokens=700,
        response_format={'type': 'json_object'},
        trace_name="notes.summary",
    )
    if result is None:
        return None

    content, model_name = result
    payload = _extract_json_payload(content)
    if payload is None:
        return None

    summary_text = str(payload.get('summary_text', '')).strip()
    raw_suggestions = payload.get('suggestions', [])
    if isinstance(raw_suggestions, list):
        suggestions = [str(item).strip() for item in raw_suggestions if str(item).strip()]
    else:
        suggestions = []

    if not summary_text:
        return None

    if len(suggestions) < 3:
        defaults = [
            '补充 1-2 道典型例题和完整解题步骤',
            '补一个最容易混淆的概念对比',
            '把当前笔记拆成更清晰的小标题结构',
        ]
        for item in defaults:
            if item not in suggestions:
                suggestions.append(item)
            if len(suggestions) >= 3:
                break

    return summary_text, {'suggestions': suggestions[:3]}, model_name













