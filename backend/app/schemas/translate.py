from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class TranslateTextRequest(BaseModel):
    source_text: str | None = None
    source_language: str = Field(default='auto', max_length=64)
    target_language: str = Field(default='中文', max_length=64)
    mode: str = Field(default='academic', max_length=32)
    uploaded_file_id: UUID | None = None

    @model_validator(mode='after')
    def validate_payload(self) -> 'TranslateTextRequest':
        has_text = bool((self.source_text or '').strip())
        if not has_text and self.uploaded_file_id is None:
            raise ValueError('Either source_text or uploaded_file_id is required')
        return self


class TranslateTextResponse(BaseModel):
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    mode: str
    model_name: str
    is_fallback: bool = False
    uploaded_file_id: UUID | None = None
    uploaded_file_name: str | None = None


class TranslatePolishRequest(BaseModel):
    text: str = Field(min_length=1)
    language: str = Field(default='中文', max_length=64)
    mode: str = Field(default='academic', max_length=32)


class TranslatePolishResponse(BaseModel):
    original_text: str
    polished_text: str
    language: str
    mode: str
    model_name: str
    is_fallback: bool = False
