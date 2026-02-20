from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class Department(SQLModel, table=True):
    """
    DEPARTMENT {
        uuid department_id PK
        int institution_id FK
        string name
        string slug (optional)
    }
    """
    department_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    institution_id: Optional[int] = Field(default=None, foreign_key="institution.id", index=True)
    name: str = Field(index=True, nullable=False)
    slug: Optional[str] = Field(default=None, index=True)


class Course(SQLModel, table=True):
    """
    COURSE {
        uuid course_id PK
        uuid department_id FK (optional)
        string course_name
        text description
    }
    """
    course_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    department_id: Optional[uuid.UUID] = Field(default=None, foreign_key="department.department_id", index=True)
    course_name: str
    description: Optional[str] = Field(default=None, sa_column=Column(Text))


class Subject(SQLModel, table=True):
    """
    SUBJECT {
        uuid subject_id PK
        uuid course_id FK
        string subject_name
        int semester
    }
    """
    subject_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.course_id")
    subject_name: str
    semester: Optional[int] = Field(default=1, sa_column=Column(Integer))


class Syllabus(SQLModel, table=True):
    """
    SYLLABUS {
        uuid syllabus_id PK
        uuid subject_id FK
        string unit_name
        int unit_order
    }
    """
    syllabus_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subject_id: uuid.UUID = Field(foreign_key="subject.subject_id")
    unit_name: str
    unit_order: Optional[int] = Field(default=1, sa_column=Column(Integer))


class Topic(SQLModel, table=True):
    """
    TOPIC {
        uuid topic_id PK
        uuid syllabus_id FK
        string topic_name
        text description
    }
    """
    topic_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    syllabus_id: uuid.UUID = Field(foreign_key="syllabus.syllabus_id")
    topic_name: str
    description: Optional[str] = Field(default=None, sa_column=Column(Text))


class TopicContent(SQLModel, table=True):
    """
    TOPIC_CONTENT {
        uuid content_id PK
        uuid topic_id FK
        string file_name
        file_type (pdf, csv, doc, docx)
        storage_path (optional)
        extracted_text (TEXT)
        file_size_bytes
        created_at, updated_at
    }
    """
    content_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    topic_id: uuid.UUID = Field(foreign_key="topic.topic_id", index=True)
    file_name: str
    file_type: str = Field(index=True)  # pdf, csv, doc, docx
    storage_path: Optional[str] = Field(default=None)
    extracted_text: Optional[str] = Field(default=None, sa_column=Column(Text))
    file_size_bytes: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserContext(SQLModel, table=True):
    """
    USER_CONTEXT {
        uuid context_id PK
        uuid user_id FK
        uuid subject_id FK
        string last_topic
        string last_intent
        timestamp updated_at
    }
    """
    context_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Note: existing User model uses integer `id` primary key; keep FK to that.
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    subject_id: Optional[uuid.UUID] = Field(default=None, foreign_key="subject.subject_id")
    last_topic: Optional[str] = None
    last_intent: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

