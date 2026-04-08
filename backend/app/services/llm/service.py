from __future__ import annotations

import json
import logging
import re
from functools import lru_cache

from app.core.config import settings


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_openai_client():
    if not settings.openai_api_key:
        return None

    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover - depends on runtime install state
        logger.warning("OpenAI client is unavailable: %s", exc)
        return None

    return OpenAI(api_key=settings.openai_api_key, timeout=20.0)


def _create_completion(
    *,
    messages: list[dict[str, str]],
    temperature: float = 0.4,
    max_tokens: int = 900,
    response_format: dict | None = None,
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
    return content, model_name


def generate_chat_reply(question: str, subject: str | None = None) -> tuple[str, str] | None:
    topic = subject or '当前问题'
    prompt = (
        '你是学塔的学习助手。请使用简体中文回答，要求：\n'
        '1. 先用 1-2 句话概括问题核心。\n'
        '2. 再给出分步骤讲解。\n'
        '3. 最后补一个简短示例或复习建议。\n'
        '4. 不要编造参考资料，不要说自己看到了不存在的教材。'
    )
    return _create_completion(
        messages=[
            {'role': 'system', 'content': prompt},
            {
                'role': 'user',
                'content': f'学科/主题：{topic}\n\n问题：{question.strip()}',
            },
        ],
        temperature=0.35,
        max_tokens=900,
    )


def translate_text_with_model(
    *,
    source_text: str,
    source_language: str,
    target_language: str,
    mode: str,
) -> tuple[str, str] | None:
    prompt = (
        '你是专业翻译助手。请只输出译文，不要额外解释。\n'
        '要求：\n'
        '1. 保留原始段落结构。\n'
        '2. 学术模式下使用更准确、更正式的表达；口语模式下更自然。\n'
        '3. 如果源语言与目标语言相同，请做最轻量的润色后返回。'
    )
    return _create_completion(
        messages=[
            {'role': 'system', 'content': prompt},
            {
                'role': 'user',
                'content': (
                    f'源语言：{source_language}\n'
                    f'目标语言：{target_language}\n'
                    f'风格：{mode}\n\n'
                    f'待翻译文本：\n{source_text.strip()[:8000]}'
                ),
            },
        ],
        temperature=0.2,
        max_tokens=1200,
    )


def polish_text_with_model(
    *,
    text: str,
    language: str,
    mode: str,
) -> tuple[str, str] | None:
    prompt = (
        '你是专业文本润色助手。请只输出润色后的文本，不要解释。\n'
        '要求：\n'
        '1. 保留原始含义。\n'
        '2. 学术模式下更严谨、正式；口语模式下更自然流畅。\n'
        '3. 保留原有段落结构。'
    )
    return _create_completion(
        messages=[
            {'role': 'system', 'content': prompt},
            {
                'role': 'user',
                'content': (
                    f'语言：{language}\n'
                    f'风格：{mode}\n\n'
                    f'待润色文本：\n{text.strip()[:8000]}'
                ),
            },
        ],
        temperature=0.2,
        max_tokens=900,
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
        '你是学习笔记整理助手。请返回 JSON 对象，必须包含两个字段：\n'
        'summary_text: string，2-5 句话总结这份笔记的核心内容；\n'
        'suggestions: string[]，给出 3 条具体的复习或补充建议。\n'
        '不要输出 JSON 之外的解释。'
    )
    source = content_markdown.strip()[:6000]
    result = _create_completion(
        messages=[
            {'role': 'system', 'content': prompt},
            {
                'role': 'user',
                'content': f'标题：{title.strip()}\n\n笔记内容：\n{source}',
            },
        ],
        temperature=0.2,
        max_tokens=700,
        response_format={'type': 'json_object'},
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
