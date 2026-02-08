# Database Schema (summary)

This file summarizes the tables and key fields in `app/models`.

Tables (backend):

- `user` (PK: `id` int)
  - `email`, `hashed_password`, `full_name`, `is_active`, `institution_id` (FK -> institution.id), `status`

- `role` (PK: `id` int)
  - `name`, `description`, `is_system`, `is_active`, `created_at`

- `role_assignment` (composite PK: `user_id`, `role_id`)
  - `institution_id` (optional scope), `assigned_at`, `expires_at`

- `institution` (PK: `id` int)
  - `name`, `slug`, `type`, `is_active`, `created_at`

- `course` (PK: `course_id` uuid)
  - `course_name`, `description`

- `subject` (PK: `subject_id` uuid)
  - `course_id` (FK -> course.course_id), `subject_name`, `semester`

- `syllabus` (PK: `syllabus_id` uuid)
  - `subject_id` (FK -> subject.subject_id), `unit_name`, `unit_order`

- `topic` (PK: `topic_id` uuid)
  - `syllabus_id` (FK -> syllabus.syllabus_id), `topic_name`, `description`

- `user_context` (PK: `context_id` uuid)
  - `user_id` (FK -> user.id), `subject_id` (FK -> subject.subject_id), `last_topic`, `last_intent`, `updated_at`

Notes:
- Content tables use UUID primary keys for portability/cross-tenant decoupling.
- User/tenant tables use integer PKs suitable for RBAC and indexing.
