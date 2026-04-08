import { describe, expect, it } from 'vitest'

import {
  buildTranslateNoteMarkdown,
  buildTranslateNoteTitle,
  getUploadedFileType
} from './translate-utils'

describe('translate utils', () => {
  it('classifies uploaded file types', () => {
    expect(getUploadedFileType({ original_filename: 'demo.txt', mime_type: 'text/plain' })).toBe('text')
    expect(getUploadedFileType({ original_filename: 'photo.png', mime_type: 'image/png' })).toBe('image')
    expect(getUploadedFileType({ original_filename: 'slides.pdf', mime_type: 'application/pdf' })).toBe('other')
  })

  it('builds note title from uploaded file first', () => {
    expect(
      buildTranslateNoteTitle({
        uploadedFile: { original_filename: 'linear-algebra.pdf' },
        sourceText: 'This text should not win'
      })
    ).toBe('linear-algebra 翻译笔记')
  })

  it('builds note markdown with source and translated text', () => {
    const markdown = buildTranslateNoteMarkdown({
      title: '极限翻译笔记',
      sourceLanguage: '英语',
      targetLanguage: '中文',
      mode: 'academic',
      sourceText: 'Limits are important.',
      translatedText: '极限很重要。',
      uploadedFile: { original_filename: 'limits.txt' }
    })

    expect(markdown).toContain('# 极限翻译笔记')
    expect(markdown).toContain('## 原文')
    expect(markdown).toContain('Limits are important.')
    expect(markdown).toContain('## 译文')
    expect(markdown).toContain('极限很重要。')
    expect(markdown).toContain('limits.txt')
  })
})
