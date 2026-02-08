from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from datetime import datetime
from sqlalchemy import Column, Text, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class Course(SQLModel, table=True):
    """
    COURSE {
        uuid course_id PK
        string course_name
        text description
    }
    """
    course_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
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

