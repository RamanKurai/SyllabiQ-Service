# Soft Delete Feature — Design & Implementation Reference

This document describes the design for a **soft delete** (archive) feature. Data is marked as archived instead of being removed from the database. Only **SuperAdmin** can permanently remove (hard delete) data.

---

## Table of contents

1. [Overview](#overview)
2. [Concepts](#concepts)
3. [Model changes](#model-changes)
4. [Query behavior](#query-behavior)
5. [API design](#api-design)
6. [Permissions](#permissions)
7. [Unique constraints](#unique-constraints)
8. [Foreign keys & dependencies](#foreign-keys--dependencies)
9. [Migration & rollout](#migration--rollout)
10. [Checklist for implementation](#checklist-for-implementation)

---

## Overview

| Current behavior | With soft delete |
|------------------|------------------|
| Delete = row removed from DB | Delete = row marked archived (`deleted_at` set) |
| No way to recover | Archived data can be restored (optional) |
| Any allowed role can remove data | Same roles can “delete” (archive); only SuperAdmin can permanently remove |

**Goals**

- Keep data for audit and recovery.
- Normal lists and reads exclude archived rows by default.
- SuperAdmin can permanently remove data when required.

---

## Concepts

- **Soft delete (archive):** Set `deleted_at` (and optionally `deleted_by_id`) on the row. Row stays in the DB but is treated as archived.
- **Hard delete (permanent remove):** Actual `DELETE` from the database. SuperAdmin only.
- **Restore:** Clear `deleted_at` (and `deleted_by_id`) so the row is active again.

---

## Model changes

Add the same archive fields to every entity that should support soft delete.

### Standard fields to add

```python
from datetime import datetime
from typing import Optional

# On each soft-deletable model (e.g. Institution, Department, Course, Subject, Syllabus, Topic, Role):
deleted_at: Optional[datetime] = Field(default=None, index=True)
deleted_by_id: Optional[int] = Field(default=None, foreign_key="user.id")
```

- **`deleted_at`**: `None` = active, non-null timestamp = archived.
- **`deleted_by_id`**: Optional audit; user who archived the row.

### Entities to extend

| Model | Location | Notes |
|-------|----------|--------|
| Institution | `app/models/institution.py` | Add `deleted_at`, `deleted_by_id` |
| Department | `app/models/content.py` | Same |
| Course | `app/models/content.py` | Same |
| Subject | `app/models/content.py` | Same |
| Syllabus | `app/models/content.py` | Same |
| Topic | `app/models/content.py` | Same |
| Role | `app/models/role.py` | Same |
| User | `app/models/user.py` | Can reuse `is_active` and/or add `deleted_at`; “archive” = set `is_active = False` and `deleted_at` |

### User model

- Option A: Add `deleted_at` and `deleted_by_id`; treat “archived user” as `deleted_at` set (and optionally set `is_active = False`).
- Option B: Use only `is_active = False` for “deactivated” and add `deleted_at` only when you want a distinct “archived” state.

### TopicContent / UserContext / TopicVisit / AuditLog

- Typically **no** soft delete: either hard delete when allowed, or leave as-is and rely on parent (e.g. Topic) being archived.

---

## Query behavior

### Default (active only)

- All list and read queries should **exclude archived rows** unless otherwise specified.
- Filter: `WHERE deleted_at IS NULL` (or equivalent in SQLModel).

### Admin “list all”

- Add optional query parameter, e.g. `include_archived: bool = False`.
- When `True`, do not filter by `deleted_at`; optionally include an `archived: bool` (or `deleted_at`) in the response.

### Get by ID

- **Normal users:** Return 404 if the row is archived (so archived data is hidden).
- **SuperAdmin (and possibly other admins):** When viewing “archive” or “restore/permanent delete” flows, allow loading by ID even when `deleted_at` is set.

### Where to apply

- Admin list/detail endpoints for institutions, departments, courses, subjects, syllabi, topics, users, roles.
- Content read endpoints (e.g. departments, courses, subjects, syllabi, topics) so archived items do not appear in dropdowns or content trees.
- Dashboard and any reports: exclude archived entities unless “include archived” is requested.

---

## API design

### 1. “Delete” = soft delete (archive)

- **Who:** Same roles that can delete today (e.g. admin for resource, SuperAdmin for global).
- **Action:** Set `deleted_at = now()`, `deleted_by_id = current_user.id`. Do **not** remove the row.
- **Endpoints:** Either:
  - **Option A:** Keep existing `DELETE /api/admin/.../{id}` and change implementation to soft delete, or
  - **Option B:** New action, e.g. `POST /api/admin/institutions/{id}/archive`, and keep `DELETE` for SuperAdmin hard delete only.

Recommended: **Option A** for backward compatibility — `DELETE` means “archive” for non–SuperAdmin; add a separate permanent-delete action for SuperAdmin.

### 2. Restore (optional)

- **Who:** Admin or SuperAdmin (as defined).
- **Action:** Set `deleted_at = None`, `deleted_by_id = None`.
- **Endpoint:** e.g. `POST /api/admin/institutions/{id}/restore` (and similarly for other entities).

### 3. Permanent remove (hard delete)

- **Who:** **SuperAdmin only.**
- **Action:** Actual `DELETE` from the database; handle FKs (cascade or 409) as today.
- **Endpoint:** Either:
  - **Option A:** `DELETE /api/admin/.../permanent` (e.g. `DELETE /api/admin/institutions/{id}/permanent`), or
  - **Option B:** Keep `DELETE /api/admin/.../{id}` and branch: if SuperAdmin → hard delete; else → soft delete.

Recommended: **Option A** — explicit “permanent” endpoint so behavior is clear and easier to secure/audit.

### Example endpoint matrix

| Action | Endpoint | Role | Behavior |
|--------|----------|------|----------|
| Archive (soft delete) | `DELETE /api/admin/institutions/{id}` | Admin / SuperAdmin | Set `deleted_at`, `deleted_by_id` |
| Restore | `POST /api/admin/institutions/{id}/restore` | Admin / SuperAdmin | Clear `deleted_at`, `deleted_by_id` |
| Permanent remove | `DELETE /api/admin/institutions/{id}/permanent` | SuperAdmin only | Real DELETE; handle FKs |

Repeat the same pattern for departments, courses, subjects, syllabi, topics, users, roles.

---

## Permissions

| Role | Archive (soft delete) | Restore | Permanent remove (hard delete) |
|------|----------------------|--------|---------------------------------|
| SuperAdmin | Yes | Yes | Yes |
| InstitutionAdmin | Within scope | Within scope | No |
| Other admins | Per existing rules | Per existing rules | No |

- Enforce “SuperAdmin only” for permanent-delete endpoints (e.g. `DELETE .../permanent`) in the route handler.
- Archive and restore follow existing admin scope (institution, resource type, etc.).

---

## Unique constraints

Tables with `unique=True` on `name` or `slug` (e.g. **Institution**) will conflict if you archive one row and create a new one with the same name.

### Approach: partial unique index

- **PostgreSQL:** `CREATE UNIQUE INDEX ... ON institution (name) WHERE deleted_at IS NULL;`
- So: only one active row per `name`; multiple archived rows can share the same `name`.

Apply the same idea for:

- Institution: `name`, `slug`
- Role: `name`
- User: `email` (if users are soft deleted)
- Department/Course/Subject/Syllabus/Topic: any unique (name/slug) columns

SQLModel/Alembic: add the index in a migration; ensure normal unique constraints are replaced or relaxed where needed.

---

## Foreign keys & dependencies

- **Soft delete:** Rows are not removed, so FKs (e.g. `User.institution_id`, `Department.institution_id`) continue to point to the same row. No FK schema change required.
- **Listing:** When listing “active” entities, filter by `deleted_at IS NULL`. When building dropdowns (e.g. institutions), use the same filter so archived items do not appear.
- **Hard delete (SuperAdmin):** Same as today — either cascade (null out or delete dependents in the correct order) or return 409 with a clear message. Existing logic in `app/admin/routes.py` (IntegrityError handling, cascade for User/Role/Topic) still applies to permanent delete.

---

## Migration & rollout

1. **Schema:** Add `deleted_at` and `deleted_by_id` to the relevant tables (Alembic or SQLModel `create_all` after model change).
2. **Partial unique indexes:** Add `WHERE deleted_at IS NULL` for any unique columns that must stay unique only among active rows.
3. **Backfill:** Existing rows stay active: `deleted_at IS NULL` (default).
4. **Code:**  
   - Update models.  
   - Change “delete” handlers to soft delete (set `deleted_at`).  
   - Add permanent-delete endpoints (SuperAdmin only).  
   - Add restore endpoints.  
   - Add `include_archived` to list endpoints and default all reads/lists to `deleted_at IS NULL`.

---

## Checklist for implementation

- [ ] Add `deleted_at` and `deleted_by_id` to Institution, Department, Course, Subject, Syllabus, Topic, Role (and optionally User).
- [ ] Create DB migration; add partial unique indexes where needed.
- [ ] Default all list/read queries to `WHERE deleted_at IS NULL`.
- [ ] Add `include_archived` query param to admin list endpoints; include `archived`/`deleted_at` in response when used.
- [ ] Change existing `DELETE /api/admin/.../{id}` to perform soft delete (set `deleted_at`, `deleted_by_id`).
- [ ] Add `DELETE /api/admin/.../{id}/permanent` (or equivalent) for SuperAdmin-only hard delete; reuse existing FK/cascade logic.
- [ ] Add `POST /api/admin/.../{id}/restore` for each entity (optional).
- [ ] Enforce SuperAdmin for permanent-delete endpoints.
- [ ] Update API documentation (e.g. `docs/API.md`) with archive, restore, and permanent-delete behavior.
- [ ] Update OpenAPI/Swagger descriptions for the new/updated endpoints.

---

*This document is a design reference for implementing the soft delete feature in the SyllabiQ backend. Update it as the implementation evolves.*
