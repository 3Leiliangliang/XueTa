const stripExtension = (filename = '') => filename.replace(/\.[^/.]+$/, '')

export const getUploadedFileType = (file) => {
  const filename = (file?.original_filename || file?.name || '').toLowerCase()
  const mimeType = (file?.mime_type || file?.type || '').toLowerCase()

  if (
    mimeType.startsWith('text/') ||
    filename.endsWith('.txt') ||
    filename.endsWith('.md') ||
    filename.endsWith('.csv') ||
    filename.endsWith('.json')
  ) {
    return 'text'
  }

  if (
    mimeType.startsWith('image/') ||
    filename.endsWith('.png') ||
    filename.endsWith('.jpg') ||
    filename.endsWith('.jpeg') ||
    filename.endsWith('.webp') ||
    filename.endsWith('.gif')
  ) {
    return 'image'
  }

  return 'other'
}

export const buildTranslateNoteTitle = ({ uploadedFile, sourceText }) => {
  const fileName = stripExtension(uploadedFile?.original_filename || '')
  if (fileName) return `${fileName} 翻译笔记`

  const preview = (sourceText || '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 18)

  return preview ? `${preview} 翻译笔记` : '翻译笔记'
}

export const buildTranslateNoteMarkdown = ({
  title,
  sourceLanguage,
  targetLanguage,
  mode,
  sourceText,
  translatedText,
  uploadedFile
}) => {
  const fileLine = uploadedFile?.original_filename
    ? `- 来源文件：${uploadedFile.original_filename}`
    : null

  return [
    `# ${title}`,
    '',
    '## 翻译信息',
    `- 源语言：${sourceLanguage}`,
    `- 目标语言：${targetLanguage}`,
    `- 翻译模式：${mode === 'academic' ? '学术模式' : '口语模式'}`,
    fileLine,
    '',
    '## 原文',
    sourceText.trim() || '（空）',
    '',
    '## 译文',
    translatedText.trim() || '（空）'
  ]
    .filter(Boolean)
    .join('\n')
}
