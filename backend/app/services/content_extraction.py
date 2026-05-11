from __future__ import annotations

import base64
import io
import re
import zlib
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import httpx
from PIL import Image

from app.core.config import settings


TEXT_FILE_EXTENSIONS = {'.txt', '.md', '.markdown', '.csv', '.json', '.py', '.js', '.ts', '.html', '.htm'}
DOCX_FILE_EXTENSIONS = {'.docx'}
PDF_FILE_EXTENSIONS = {'.pdf'}
IMAGE_FILE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff'}

DOCX_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}
PDF_MIME_TYPES = {'application/pdf'}
HTML_MIME_MARKERS = {'text/html', 'application/xhtml+xml'}

HTML_BLOCK_TAGS = {
    'article', 'aside', 'blockquote', 'br', 'div', 'dl', 'dt', 'dd', 'fieldset',
    'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'header', 'hr', 'li', 'main', 'nav', 'ol', 'p', 'pre', 'section', 'table', 'tbody',
    'td', 'th', 'thead', 'tr', 'ul'
}
HTML_IGNORED_TAGS = {'script', 'style', 'noscript', 'svg'}
WORD_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
PDF_LITERAL_RE = re.compile(rb'\((?:\\.|[^\\()])*\)')
PDF_HEX_RE = re.compile(rb'<([0-9A-Fa-f\s]+)>')
PDF_STREAM_RE = re.compile(rb'<<(.*?)>>\s*stream\r?\n(.*?)\r?\nendstream', re.DOTALL)


class ContentExtractionError(RuntimeError):
    pass


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._title_depth = 0
        self._body_parts: list[str] = []
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in HTML_IGNORED_TAGS:
            self._ignored_depth += 1
            return
        if tag == 'title':
            self._title_depth += 1
        if tag in HTML_BLOCK_TAGS:
            self._body_parts.append('\n')

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in HTML_IGNORED_TAGS and self._ignored_depth > 0:
            self._ignored_depth -= 1
            return
        if tag == 'title' and self._title_depth > 0:
            self._title_depth -= 1
        if tag in HTML_BLOCK_TAGS:
            self._body_parts.append('\n')

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text or self._ignored_depth > 0:
            return
        if self._title_depth:
            self._title_parts.append(text)
        self._body_parts.append(text)

    @property
    def title(self) -> str:
        return _normalize_text(' '.join(self._title_parts))

    @property
    def body_text(self) -> str:
        return _normalize_text(' '.join(self._body_parts))


def _normalize_text(text: str) -> str:
    normalized = text.replace('\r\n', '\n').replace('\r', '\n')
    normalized = re.sub(r'[ \t]+', ' ', normalized)
    normalized = re.sub(r' *\n *', '\n', normalized)
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)
    return normalized.strip()


def _best_effort_decode_text(data: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'gb18030', 'gbk', 'big5'):
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        if text and '\x00' not in text:
            return text

    text = data.decode('utf-8', errors='ignore')
    if text:
        return text
    return data.decode('latin-1', errors='ignore')


def _is_text_like(mime_type: str, extension: str) -> bool:
    return (
        extension in TEXT_FILE_EXTENSIONS
        or mime_type.startswith('text/')
        or 'json' in mime_type
        or 'xml' in mime_type
    )


def _extract_text_from_text_bytes(data: bytes) -> str:
    text = _best_effort_decode_text(data)
    return _normalize_text(text)


def _extract_text_from_html_bytes(data: bytes) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(_best_effort_decode_text(data))
    parser.close()

    title = parser.title
    body_text = parser.body_text
    if not body_text:
        raise ContentExtractionError('网页正文解析失败，未提取到可用文本。')
    if title and title not in body_text[:200]:
        return f'{title}\n\n{body_text}'
    return body_text


def _decode_pdf_string(raw: bytes) -> str:
    result = bytearray()
    index = 0
    while index < len(raw):
        current = raw[index]
        if current != 0x5C:
            result.append(current)
            index += 1
            continue

        index += 1
        if index >= len(raw):
            break
        escaped = raw[index]

        escape_map = {
            ord('n'): b'\n',
            ord('r'): b'\r',
            ord('t'): b'\t',
            ord('b'): b'\b',
            ord('f'): b'\f',
            ord('('): b'(',
            ord(')'): b')',
            ord('\\'): b'\\',
        }
        if escaped in escape_map:
            result.extend(escape_map[escaped])
            index += 1
            continue

        if escaped in b'01234567':
            octal = bytes([escaped])
            index += 1
            for _ in range(2):
                if index < len(raw) and raw[index] in b'01234567':
                    octal += bytes([raw[index]])
                    index += 1
                else:
                    break
            result.append(int(octal, 8))
            continue

        if escaped in (0x0A, 0x0D):
            if escaped == 0x0D and index + 1 < len(raw) and raw[index + 1] == 0x0A:
                index += 1
            index += 1
            continue

        result.append(escaped)
        index += 1

    data = bytes(result)
    if data.startswith((b'\xfe\xff', b'\xff\xfe')):
        try:
            return data.decode('utf-16')
        except UnicodeDecodeError:
            pass
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return data.decode('latin-1', errors='ignore')


def _decode_pdf_hex_string(raw: bytes) -> str:
    cleaned = re.sub(rb'\s+', b'', raw)
    if len(cleaned) % 2 == 1:
        cleaned += b'0'
    data = bytes.fromhex(cleaned.decode('ascii'))
    if data.startswith((b'\xfe\xff', b'\xff\xfe')):
        try:
            return data.decode('utf-16')
        except UnicodeDecodeError:
            pass
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return data.decode('latin-1', errors='ignore')


def _extract_strings_from_pdf_segment(segment: bytes) -> list[str]:
    texts: list[str] = []
    for match in PDF_LITERAL_RE.finditer(segment):
        decoded = _decode_pdf_string(match.group(0)[1:-1]).strip()
        if decoded:
            texts.append(decoded)
    for match in PDF_HEX_RE.finditer(segment):
        decoded = _decode_pdf_hex_string(match.group(1)).strip()
        if decoded:
            texts.append(decoded)
    return texts


def _extract_text_from_pdf_stream(stream_data: bytes) -> list[str]:
    texts: list[str] = []

    for match in re.finditer(rb'\[(.*?)\]\s*TJ', stream_data, re.DOTALL):
        texts.extend(_extract_strings_from_pdf_segment(match.group(1)))

    for pattern in (
        rb'(\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]+>)\s*Tj',
        rb'(\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]+>)\s*[\'"]',
    ):
        for match in re.finditer(pattern, stream_data):
            texts.extend(_extract_strings_from_pdf_segment(match.group(1)))

    return texts


def _extract_text_from_pdf_bytes_fallback(data: bytes) -> str:
    text_parts: list[str] = []

    for header, raw_stream in PDF_STREAM_RE.findall(data):
        stream_bytes = raw_stream.strip(b'\r\n')
        if b'/FlateDecode' in header:
            try:
                stream_bytes = zlib.decompress(stream_bytes)
            except zlib.error:
                continue
        text_parts.extend(_extract_text_from_pdf_stream(stream_bytes))

    text = _normalize_text('\n'.join(text_parts))
    if text:
        return text
    raise ContentExtractionError('PDF 解析失败，当前环境未能提取出可用文本。')


def _extract_text_from_pdf_bytes(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return _extract_text_from_pdf_bytes_fallback(data)

    try:
        reader = PdfReader(io.BytesIO(data))
        parts = [page.extract_text() or '' for page in reader.pages]
    except Exception:
        return _extract_text_from_pdf_bytes_fallback(data)

    text = _normalize_text('\n\n'.join(parts))
    if text:
        return text
    return _extract_text_from_pdf_bytes_fallback(data)


def _extract_text_from_docx_xml(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    paragraphs: list[str] = []

    for paragraph in root.iter(f'{WORD_NS}p'):
        fragments: list[str] = []
        for node in paragraph.iter():
            if node.tag == f'{WORD_NS}t' and node.text:
                fragments.append(node.text)
            elif node.tag in {f'{WORD_NS}tab'}:
                fragments.append('\t')
            elif node.tag in {f'{WORD_NS}br', f'{WORD_NS}cr'}:
                fragments.append('\n')

        paragraph_text = _normalize_text(''.join(fragments))
        if paragraph_text:
            paragraphs.append(paragraph_text)

    return paragraphs


def _extract_text_from_docx_bytes(data: bytes) -> str:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ContentExtractionError('DOCX 文件读取失败，文件可能已损坏。') from exc

    document_parts = [
        name for name in archive.namelist()
        if name == 'word/document.xml'
        or name.startswith('word/header')
        or name.startswith('word/footer')
        or name in {'word/footnotes.xml', 'word/endnotes.xml'}
    ]

    paragraphs: list[str] = []
    for part_name in document_parts:
        try:
            paragraphs.extend(_extract_text_from_docx_xml(archive.read(part_name)))
        except KeyError:
            continue

    text = _normalize_text('\n\n'.join(paragraphs))
    if not text:
        raise ContentExtractionError('DOCX 正文解析失败，未提取到可用文本。')
    return text


def _extract_text_from_image_with_tesseract(image: Image.Image) -> str | None:
    try:
        import pytesseract
    except ImportError:
        return None

    try:
        grayscale = image.convert('L')
        text = pytesseract.image_to_string(grayscale)
    except Exception:
        return None

    normalized = _normalize_text(text)
    return normalized or None


def _extract_text_from_image_with_openai(data: bytes, mime_type: str) -> str | None:
    if not settings.openai_api_key:
        return None

    try:
        from openai import OpenAI
    except Exception:
        return None

    encoded_image = base64.b64encode(data).decode('ascii')
    try:
        client_kwargs = {
            'api_key': settings.openai_api_key,
            'timeout': max(settings.openai_timeout_seconds, 30.0),
        }
        if settings.openai_base_url:
            client_kwargs['base_url'] = settings.openai_base_url
        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0,
            max_tokens=1600,
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': '请提取图片中的正文文本，只返回提取出的文字内容，不要解释。看不清时返回空字符串。',
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:{mime_type};base64,{encoded_image}',
                            },
                        },
                    ],
                }
            ],
        )
    except Exception:
        return None

    if not getattr(response, 'choices', None):
        return None
    content = (response.choices[0].message.content or '').strip()
    return _normalize_text(content) or None


def _extract_text_from_image_bytes(data: bytes, mime_type: str) -> str:
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as exc:
        raise ContentExtractionError('图片读取失败，无法执行 OCR。') from exc

    text = _extract_text_from_image_with_tesseract(image)
    if text:
        return text

    text = _extract_text_from_image_with_openai(data, mime_type or 'image/png')
    if text:
        return text

    raise ContentExtractionError('图片 OCR 当前不可用。请安装 pytesseract 并配置 Tesseract，或配置可用的 OpenAI 视觉模型。')


def _guess_extension(filename: str | None, mime_type: str) -> str:
    if filename:
        return Path(filename).suffix.lower()
    if mime_type in DOCX_MIME_TYPES:
        return '.docx'
    if mime_type in PDF_MIME_TYPES:
        return '.pdf'
    return ''


def extract_text_from_bytes(
    data: bytes,
    *,
    mime_type: str | None = None,
    filename: str | None = None,
    source_url: str | None = None,
) -> tuple[str, dict]:
    normalized_mime = (mime_type or '').lower()
    extension = _guess_extension(filename, normalized_mime)

    if extension in DOCX_FILE_EXTENSIONS or normalized_mime in DOCX_MIME_TYPES:
        text = _extract_text_from_docx_bytes(data)
        return text, {'kind': 'docx', 'mime_type': normalized_mime or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}

    if extension in PDF_FILE_EXTENSIONS or normalized_mime in PDF_MIME_TYPES:
        text = _extract_text_from_pdf_bytes(data)
        return text, {'kind': 'pdf', 'mime_type': normalized_mime or 'application/pdf'}

    if normalized_mime.startswith('image/') or extension in IMAGE_FILE_EXTENSIONS:
        text = _extract_text_from_image_bytes(data, normalized_mime or 'image/png')
        return text, {'kind': 'image', 'mime_type': normalized_mime or 'image/png'}

    if normalized_mime in HTML_MIME_MARKERS or extension in {'.html', '.htm'} or source_url:
        text = _extract_text_from_html_bytes(data)
        return text, {'kind': 'html', 'mime_type': normalized_mime or 'text/html'}

    if _is_text_like(normalized_mime, extension):
        text = _extract_text_from_text_bytes(data)
        return text, {'kind': 'text', 'mime_type': normalized_mime or 'text/plain'}

    raise ContentExtractionError('当前文件格式还不支持正文提取。')


def extract_text_from_path(
    file_path: Path,
    *,
    mime_type: str | None = None,
    filename: str | None = None,
) -> tuple[str, dict]:
    if not file_path.exists():
        raise ContentExtractionError('文件不存在，无法提取正文。')
    data = file_path.read_bytes()
    return extract_text_from_bytes(data, mime_type=mime_type, filename=filename or file_path.name)


def _validate_url(url: str) -> str:
    normalized = url.strip()
    parsed = urlparse(normalized)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise ContentExtractionError('仅支持 http 或 https 网页地址。')
    return normalized


def extract_text_from_url(url: str) -> tuple[str, dict]:
    normalized_url = _validate_url(url)

    try:
        response = httpx.get(
            normalized_url,
            follow_redirects=True,
            timeout=20.0,
            headers={
                'User-Agent': 'XueTaBot/1.0 (+https://localhost)',
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ContentExtractionError(f'网页获取失败：{exc}') from exc

    content_type = (response.headers.get('content-type') or '').split(';', 1)[0].strip().lower()
    filename = Path(urlparse(str(response.url)).path).name or None
    text, metadata = extract_text_from_bytes(
        response.content,
        mime_type=content_type,
        filename=filename,
        source_url=str(response.url),
    )
    metadata.update(
        {
            'source_url': normalized_url,
            'resolved_url': str(response.url),
            'status_code': response.status_code,
        }
    )
    return text, metadata
