from __future__ import annotations

import re
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import UploadedFile
from app.models.user import User
from app.schemas.translate import TranslatePolishRequest, TranslateTextRequest
from app.services.content_extraction import ContentExtractionError, extract_text_from_path, extract_text_from_url
from app.services.llm.service import polish_text_with_model, translate_text_with_model


EN_TO_ZH_PHRASES = {
    'machine learning': '机器学习',
    'artificial intelligence': '人工智能',
    'computer science': '计算机科学',
    'deep learning': '深度学习',
    'data structure': '数据结构',
    'algorithm': '算法',
    'algorithms': '算法',
    'data': '数据',
    'model': '模型',
    'models': '模型',
    'translation': '翻译',
    'document': '文档',
    'documents': '文档',
    'knowledge': '知识',
    'example': '例子',
    'examples': '例子',
    'summary': '总结',
    'practice': '练习',
    'study': '学习',
    'learning': '学习',
    'question': '问题',
    'answer': '答案',
}

ZH_TO_EN_PHRASES = {
    '机器学习': 'machine learning',
    '人工智能': 'artificial intelligence',
    '计算机科学': 'computer science',
    '深度学习': 'deep learning',
    '数据结构': 'data structure',
    '算法': 'algorithm',
    '数据': 'data',
    '模型': 'model',
    '翻译': 'translation',
    '文档': 'document',
    '知识': 'knowledge',
    '例子': 'example',
    '总结': 'summary',
    '练习': 'practice',
    '学习': 'study',
    '问题': 'question',
    '答案': 'answer',
}


def _storage_root() -> Path:
    configured = Path(settings.local_storage_path)
    if configured.is_absolute():
        return configured
    backend_root = Path(__file__).resolve().parents[3]
    return backend_root / configured


def _resolve_storage_path(file_record: UploadedFile) -> Path:
    root = _storage_root().resolve()
    file_path = (root / file_record.storage_path).resolve()
    if root != file_path and root not in file_path.parents:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Stored file path is invalid',
        )
    return file_path


def _get_uploaded_file_or_404(db: Session, user: User, file_id: UUID) -> UploadedFile:
    file_record = db.scalar(
        select(UploadedFile).where(
            UploadedFile.id == file_id,
            UploadedFile.user_id == user.id,
        )
    )
    if file_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Uploaded file not found')
    return file_record


def _read_uploaded_text(file_record: UploadedFile) -> str:
    file_path = _resolve_storage_path(file_record)
    try:
        text, _ = extract_text_from_path(
            file_path,
            mime_type=file_record.mime_type,
            filename=file_record.original_filename,
        )
    except ContentExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Uploaded file did not yield readable text.',
        )
    return text


def _read_url_text(source_url: str) -> str:
    try:
        text, _ = extract_text_from_url(source_url)
    except ContentExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Source URL did not yield readable text.',
        )
    return text


def _replace_phrases(text: str, replacements: dict[str, str]) -> str:
    output = text
    for source, target in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(re.escape(source), flags=re.IGNORECASE)
        output = pattern.sub(target, output)
    return output


def _normalize_text(text: str) -> str:
    normalized = text.replace('\r\n', '\n').strip()
    normalized = re.sub(r'[ \t]+', ' ', normalized)
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)
    return normalized


def _looks_chinese(language: str) -> bool:
    return any(token in language for token in ['中', '汉', '中文', '简体'])


def _fallback_translate_text(source_text: str, source_language: str, target_language: str, mode: str) -> str:
    normalized = _normalize_text(source_text)
    if not normalized:
        return normalized

    if source_language == target_language:
        return normalized

    if _looks_chinese(target_language):
        translated = _replace_phrases(normalized, EN_TO_ZH_PHRASES)
        translated = translated.replace(',', '，').replace(';', '；').replace(':', '：')
        translated = translated.replace('. ', '。').replace('?', '？').replace('!', '！')
        if mode == 'academic' and not translated.endswith(('。', '？', '！')):
            translated += '。'
        return translated

    translated = _replace_phrases(normalized, ZH_TO_EN_PHRASES)
    if mode == 'academic':
        translated = translated.replace('例子', 'example').replace('总结', 'summary')
    return translated


def _fallback_polish_text(text: str, language: str, mode: str) -> str:
    polished = _normalize_text(text)
    if _looks_chinese(language):
        polished = polished.replace(',', '，').replace(';', '；').replace(':', '：')
        polished = polished.replace(' .', '。').replace('.', '。').replace('?', '？').replace('!', '！')
        polished = re.sub(r'\s+([，。！？；：])', r'\1', polished)
        if mode == 'academic':
            polished = polished.replace('比如', '例如').replace('很多', '较多')
    else:
        polished = re.sub(r'\s+([,.!?;:])', r'\1', polished)
        if mode == 'academic':
            polished = polished.replace("can't", 'cannot').replace("won't", 'will not')
    return polished.strip()


def translate_text(db: Session, user: User, payload: TranslateTextRequest) -> dict:
    uploaded_file = None
    source_text = (payload.source_text or '').strip()
    source_url = (payload.source_url or '').strip() or None

    if payload.uploaded_file_id is not None:
        uploaded_file = _get_uploaded_file_or_404(db, user, payload.uploaded_file_id)
        if not source_text:
            source_text = _read_uploaded_text(uploaded_file).strip()

    if not source_text and source_url:
        source_text = _read_url_text(source_url)

    if not source_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No text available for translation')

    llm_result = translate_text_with_model(
        source_text=source_text,
        source_language=payload.source_language,
        target_language=payload.target_language,
        mode=payload.mode,
    )
    if llm_result is None:
        translated_text = _fallback_translate_text(
            source_text,
            payload.source_language,
            payload.target_language,
            payload.mode,
        )
        model_name = 'rule-based-draft'
        is_fallback = True
    else:
        translated_text, model_name = llm_result
        is_fallback = False

    return {
        'source_text': source_text,
        'source_url': source_url,
        'translated_text': translated_text,
        'source_language': payload.source_language,
        'target_language': payload.target_language,
        'mode': payload.mode,
        'model_name': model_name,
        'is_fallback': is_fallback,
        'uploaded_file_id': uploaded_file.id if uploaded_file else None,
        'uploaded_file_name': uploaded_file.original_filename if uploaded_file else None,
    }


def polish_translation(payload: TranslatePolishRequest) -> dict:
    original_text = payload.text.strip()
    llm_result = polish_text_with_model(
        text=original_text,
        language=payload.language,
        mode=payload.mode,
    )
    if llm_result is None:
        polished_text = _fallback_polish_text(original_text, payload.language, payload.mode)
        model_name = 'rule-based-draft'
        is_fallback = True
    else:
        polished_text, model_name = llm_result
        is_fallback = False

    return {
        'original_text': original_text,
        'polished_text': polished_text,
        'language': payload.language,
        'mode': payload.mode,
        'model_name': model_name,
        'is_fallback': is_fallback,
    }
