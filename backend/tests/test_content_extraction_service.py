import io
import zipfile

from PIL import Image

from app.services import content_extraction


def test_extract_text_from_html_bytes() -> None:
    text, metadata = content_extraction.extract_text_from_bytes(
        b'<html><head><title>Example Page</title></head><body><article><h1>Hello</h1><p>World body text.</p></article></body></html>',
        mime_type='text/html',
        filename='page.html',
    )

    assert metadata['kind'] == 'html'
    assert 'Example Page' in text
    assert 'World body text.' in text



def test_extract_text_from_docx_bytes() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr(
            'word/document.xml',
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body>'
            '<w:p><w:r><w:t>第一段内容</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>Second paragraph</w:t></w:r></w:p>'
            '</w:body>'
            '</w:document>',
        )

    text, metadata = content_extraction.extract_text_from_bytes(
        buffer.getvalue(),
        mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename='demo.docx',
    )

    assert metadata['kind'] == 'docx'
    assert '第一段内容' in text
    assert 'Second paragraph' in text



def test_extract_text_from_pdf_bytes_without_pypdf() -> None:
    pdf_bytes = b'''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 38 >>
stream
BT
/F1 12 Tf
72 720 Td
(Hello PDF World) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
trailer
<< /Root 1 0 R /Size 5 >>
startxref
0
%%EOF'''

    text, metadata = content_extraction.extract_text_from_bytes(
        pdf_bytes,
        mime_type='application/pdf',
        filename='demo.pdf',
    )

    assert metadata['kind'] == 'pdf'
    assert 'Hello PDF World' in text



def test_extract_text_from_image_bytes_uses_available_ocr(monkeypatch) -> None:
    image = Image.new('RGB', (32, 32), color='white')
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')

    monkeypatch.setattr(content_extraction, '_extract_text_from_image_with_tesseract', lambda *_: None)
    monkeypatch.setattr(content_extraction, '_extract_text_from_image_with_openai', lambda *_: '识别出的图片文字')

    text, metadata = content_extraction.extract_text_from_bytes(
        image_bytes.getvalue(),
        mime_type='image/png',
        filename='demo.png',
    )

    assert metadata['kind'] == 'image'
    assert text == '识别出的图片文字'
