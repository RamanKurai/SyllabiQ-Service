from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class TopicVisit(SQLModel, table=True):
    """
    TOPIC_VISIT {
        uuid visit_id PK
        int user_id FK -> user.id
        uuid subject_id FK
        uuid topic_id FK
        timestamp visited_at
    }
    """
    visit_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    subject_id: Optional[uuid.UUID] = Field(default=None, foreign_key="subject.subject_id", index=True)
    topic_id: Optional[uuid.UUID] = Field(default=None, foreign_key="topic.topic_id", index=True)
    visited_at: datetime = Field(default_factory=datetime.utcnow)

