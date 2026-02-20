# Database Schema (summary)

This file summarizes the tables and key fields in `app/models`.

## ER Diagram

```mermaid
erDiagram
    user ||--o{ role_assignment : has
    role ||--o{ role_assignment : assigned_to
    institution ||--o{ role_assignment : "scopes"
    user }o--|| institution : "belongs to"
    user }o--o| department : "binds to"
    institution ||--o{ department : has
    department ||--o{ course : has
    course ||--o{ subject : has
    subject ||--o{ syllabus : has
    syllabus ||--o{ topic : has
    topic ||--o{ topic_content : contains
    user ||--o{ user_context : has
    subject ||--o{ user_context : "scopes"
    user ||--o{ topic_visit : "visits"
    subject ||--o{ topic_visit : "scopes"
    topic ||--o{ topic_visit : "visited"

    user {
        int id PK
        string email
        string hashed_password
        string full_name
        bool is_active
        int institution_id FK
        uuid department_id FK
        string status
        datetime created_at
    }

    role {
        int id PK
        string name
        string description
        bool is_system
        bool is_active
        datetime created_at
    }

    role_assignment {
        int user_id PK,FK
        int role_id PK,FK
        int institution_id FK
        datetime assigned_at
        datetime expires_at
    }

    institution {
        int id PK
        string name
        string slug
        string type
        bool is_active
        datetime created_at
    }

    department {
        uuid department_id PK
        int institution_id FK
        string name
        string slug
    }

    course {
        uuid course_id PK
        uuid department_id FK
        string course_name
        text description
    }

    subject {
        uuid subject_id PK
        uuid course_id FK
        string subject_name
        int semester
    }

    syllabus {
        uuid syllabus_id PK
        uuid subject_id FK
        string unit_name
        int unit_order
    }

    topic {
        uuid topic_id PK
        uuid syllabus_id FK
        string topic_name
        text description
    }

    topic_content {
        uuid content_id PK
        uuid topic_id FK
        string file_name
        string file_type
        string storage_path
        text extracted_text
        int file_size_bytes
        datetime created_at
        datetime updated_at
    }

    user_context {
        uuid context_id PK
        int user_id FK
        uuid subject_id FK
        string last_topic
        string last_intent
        datetime updated_at
    }

    topic_visit {
        uuid visit_id PK
        int user_id FK
        uuid subject_id FK
        uuid topic_id FK
        datetime visited_at
    }

    audit_log {
        int id PK
        int user_id
        string action
        string entity
        string entity_id
        json details
        datetime created_at
    }
```

## Tables (backend)

- `user` (PK: `id` int)
  - `email`, `hashed_password`, `full_name`, `is_active`, `institution_id` (FK -> institution.id), `department_id` (FK -> department.department_id), `status`, `created_at`

- `role` (PK: `id` int)
  - `name`, `description`, `is_system`, `is_active`, `created_at`

- `role_assignment` (composite PK: `user_id`, `role_id`)
  - `institution_id` (FK -> institution.id, optional scope), `assigned_at`, `expires_at`

- `institution` (PK: `id` int)
  - `name`, `slug`, `type`, `is_active`, `created_at`

- `department` (PK: `department_id` uuid)
  - `institution_id` (FK -> institution.id), `name`, `slug`

- `course` (PK: `course_id` uuid)
  - `department_id` (FK -> department.department_id), `course_name`, `description`

- `subject` (PK: `subject_id` uuid)
  - `course_id` (FK -> course.course_id), `subject_name`, `semester`

- `syllabus` (PK: `syllabus_id` uuid)
  - `subject_id` (FK -> subject.subject_id), `unit_name`, `unit_order`

- `topic` (PK: `topic_id` uuid)
  - `syllabus_id` (FK -> syllabus.syllabus_id), `topic_name`, `description`

- `topic_content` (PK: `content_id` uuid)
  - `topic_id` (FK -> topic.topic_id), `file_name`, `file_type`, `storage_path`, `extracted_text`, `file_size_bytes`, `created_at`, `updated_at`

- `user_context` (PK: `context_id` uuid)
  - `user_id` (FK -> user.id), `subject_id` (FK -> subject.subject_id), `last_topic`, `last_intent`, `updated_at`

- `topic_visit` (PK: `visit_id` uuid)
  - `user_id` (FK -> user.id), `subject_id` (FK -> subject.subject_id), `topic_id` (FK -> topic.topic_id), `visited_at`

- `audit_log` (PK: `id` int)
  - `user_id`, `action`, `entity`, `entity_id`, `details` (JSON), `created_at`

## Notes

- Content tables use UUID primary keys for portability/cross-tenant decoupling.
- User/tenant tables use integer PKs suitable for RBAC and indexing.
- `audit_log.user_id` is not a formal FK (soft reference) to support logging for deleted users.
- For existing databases, run migrations to add `department`, `topic_content`, `topic_visit`, `audit_log`, and new columns (`user.department_id`, `course.department_id`).
