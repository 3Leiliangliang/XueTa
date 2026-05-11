# Database Schema

This document summarizes the first-pass relational schema for the XueTa backend. The schema is designed for an AI learning assistant with four primary product loops:

1. personalized tutoring
2. note taking and knowledge retrieval
3. practice generation and grading
4. learning progress tracking

## Core Principles

- Use PostgreSQL as the source of truth for business data.
- Use `pgvector` for embeddings so relational and vector data live in one database.
- Keep table boundaries aligned with product modules.
- Prefer reusable generic tables such as `saved_items` over many tiny one-off collections.

## Table Groups

### User and auth

- `users`
- `user_profiles`
- `verification_codes`
- `refresh_tokens`
- `password_reset_tokens`

### Planning

- `study_goals`
- `study_tasks`
- `study_plan_snapshots`

### Notes

- `notebooks`
- `notes`
- `note_todos`
- `note_summaries`

### Chat and RAG

- `chat_sessions`
- `chat_messages`
- `chat_feedback`
- `knowledge_bases`
- `knowledge_documents`
- `knowledge_chunks`
- `knowledge_chunk_embeddings`

### Practice and progress

- `practice_sets`
- `practice_items`
- `practice_attempts`
- `practice_answers`
- `wrong_questions`
- `learning_records`
- `knowledge_mastery`
- `review_schedules`

### Personalization and files

- `desktop_layouts`
- `saved_items`
- `uploaded_files`

## Key Relationships

- `users 1-n study_goals`
- `study_goals 1-n study_tasks`
- `users 1-n notebooks`
- `notebooks 1-n notes`
- `users 1-n chat_sessions`
- `chat_sessions 1-n chat_messages`
- `knowledge_bases 1-n knowledge_documents`
- `knowledge_documents 1-n knowledge_chunks`
- `knowledge_chunks 1-1 knowledge_chunk_embeddings`
- `practice_sets 1-n practice_items`
- `practice_sets 1-n practice_attempts`
- `practice_attempts 1-n practice_answers`
- `users 1-n learning_records`
- `users 1-n knowledge_mastery`
- `users 1-n review_schedules`
- `users 1-n desktop_layouts`
- `users 1-n saved_items`
- `users 1-n uploaded_files`

## Table Details

### `users`
Stores the account identity and auth-ready fields.

Key columns:
- `id`
- `email`
- `phone`
- `username`
- `password_hash`
- `status`
- `email_verified`
- `phone_verified`
- `last_login_at`
- `created_at`
- `updated_at`

### `user_profiles`
Stores user preferences and profile information.

Key columns:
- `id`
- `user_id`
- `display_name`
- `avatar_url`
- `grade_level`
- `target_exam`
- `preferred_subjects`
- `learning_style`
- `bio`

### `study_goals`
Top-level learning goals displayed in the planner.

Key columns:
- `id`
- `user_id`
- `title`
- `description`
- `subject`
- `deadline`
- `progress`
- `status`
- `color`

### `study_tasks`
Individual planner tasks linked to goals.

Key columns:
- `id`
- `user_id`
- `goal_id`
- `title`
- `description`
- `task_date`
- `task_time`
- `duration_minutes`
- `priority`
- `status`
- `source`
- `metadata_json`

### `study_plan_snapshots`
Stores AI-generated or manually saved plan snapshots.

Key columns:
- `id`
- `user_id`
- `title`
- `summary`
- `plan_json`

### `notebooks`
Logical note collections.

Key columns:
- `id`
- `user_id`
- `name`
- `description`
- `color`
- `note_count`

### `notes`
Primary note records, stored as markdown-friendly content.

Key columns:
- `id`
- `user_id`
- `notebook_id`
- `title`
- `content_markdown`
- `summary`
- `source_type`
- `metadata_json`

### `note_todos`
Action items associated with a note.

Key columns:
- `id`
- `note_id`
- `text`
- `done`
- `sort_order`

### `note_summaries`
Generated summaries and follow-up suggestions for a note.

Key columns:
- `id`
- `note_id`
- `model_name`
- `summary_text`
- `suggestions_json`

### `chat_sessions`
Conversation containers for AI tutoring sessions.

Key columns:
- `id`
- `user_id`
- `title`
- `subject`
- `status`

### `chat_messages`
Individual messages inside a session.

Key columns:
- `id`
- `session_id`
- `role`
- `content`
- `citations_json`
- `tokens_prompt`
- `tokens_completion`
- `model_name`

### `chat_feedback`
Structured user feedback for assistant answers.

Key columns:
- `id`
- `message_id`
- `value`
- `reason`

### `knowledge_bases`
Top-level containers for a user’s course materials.

Key columns:
- `id`
- `user_id`
- `name`
- `description`
- `subject`
- `is_public`

### `knowledge_documents`
Uploaded or imported learning materials.

Key columns:
- `id`
- `knowledge_base_id`
- `uploaded_file_id`
- `title`
- `source_type`
- `source_url`
- `mime_type`
- `content_text`
- `tags`
- `metadata_json`

### `knowledge_chunks`
Chunked document segments used for retrieval.

Key columns:
- `id`
- `document_id`
- `chunk_index`
- `content`
- `metadata_json`

### `knowledge_chunk_embeddings`
Vector storage for chunk embeddings.

Key columns:
- `id`
- `chunk_id`
- `embedding_model`
- `dimensions`
- `embedding`

### `practice_sets`
Generated or curated exercise sets.

Key columns:
- `id`
- `user_id`
- `title`
- `subject`
- `source`
- `config_json`

### `practice_items`
Questions inside a practice set.

Key columns:
- `id`
- `set_id`
- `type`
- `stem`
- `options_json`
- `answer_json`
- `explanation`
- `difficulty`
- `knowledge_points_json`

### `practice_attempts`
User-level submissions for a practice set.

Key columns:
- `id`
- `user_id`
- `set_id`
- `status`
- `score`
- `evaluation_json`

### `practice_answers`
Per-question answer records.

Key columns:
- `id`
- `attempt_id`
- `item_id`
- `answer_json`
- `is_correct`
- `score`
- `feedback_text`

### `wrong_questions`
Persistent wrong-question notebook entries.

Key columns:
- `id`
- `user_id`
- `item_id`
- `answer_id`
- `wrong_count`
- `last_feedback`

### `learning_records`
Unified user activity log for study analytics.

Key columns:
- `id`
- `user_id`
- `record_type`
- `subject`
- `duration_minutes`
- `score`
- `reference_type`
- `reference_id`
- `metadata_json`

### `knowledge_mastery`
Aggregated per-knowledge-point mastery state.

Key columns:
- `id`
- `user_id`
- `knowledge_point`
- `subject`
- `mastery_score`
- `accuracy_rate`
- `last_practiced_at`
- `next_review_at`

### `review_schedules`
Future review queue, useful for SM-2 style scheduling.

Key columns:
- `id`
- `user_id`
- `knowledge_point`
- `subject`
- `scheduled_for`
- `status`
- `review_payload`

### `desktop_layouts`
User-specific workspace layouts for the study desktop.

Key columns:
- `id`
- `user_id`
- `name`
- `layout_json`

### `saved_items`
Generic saved content collection for answers, translations, notes or snippets.

Key columns:
- `id`
- `user_id`
- `item_type`
- `title`
- `source_type`
- `payload_json`

### `uploaded_files`
Metadata layer for user uploads.

Key columns:
- `id`
- `user_id`
- `filename`
- `original_filename`
- `mime_type`
- `extension`
- `size_bytes`
- `storage_path`
- `checksum`
- `metadata_json`

## Suggested Migration Order

1. user and auth tables
2. planner and note tables
3. chat and knowledge-base tables
4. practice and progress tables
5. personalization and file tables

## Notes

- The ORM models in `app/models/` represent the working schema source for this backend skeleton.
- The first Alembic migration should be generated after the team confirms enum names and nullable constraints.
- Embedding dimensions are currently set to `1536` to align with `text-embedding-3-small` as the initial default.
