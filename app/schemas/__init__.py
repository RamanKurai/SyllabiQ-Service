from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., example="Explain dynamic programming for knapsack")
    workflow: Optional[str] = Field(None, description="Optional workflow hint (qa|summarize|generate)")
    marks: Optional[int] = Field(None, description="Exam marks (2|5|10) to control answer length")
    top_k: Optional[int] = Field(5, description="Number of retrieval chunks to fetch")
    format: Optional[str] = Field(None, description="Preferred answer format (bullets|paragraph)")
    subject: Optional[str] = Field(None, description="Selected subject id or name")
    topic: Optional[str] = Field(None, description="Selected topic or subtopic")
    notes: Optional[str] = Field(None, description="User-provided notes text for summarization")
    difficulty: Optional[str] = Field(None, description="Question difficulty (easy|medium|hard)")
    question_type: Optional[str] = Field(None, description="Question type (mcq|short|long|mixed)")
    num_questions: Optional[int] = Field(None, description="Number of practice questions to generate")


class Citation(BaseModel):
    id: str
    source: Optional[str]
    text: Optional[str]


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    metadata: Dict[str, Any] = {}


class EmbeddingRequest(BaseModel):
    """Request to generate embeddings for text(s)."""
    text: Optional[str] = Field(None, description="Single text to embed")
    texts: Optional[List[str]] = Field(None, description="Multiple texts to embed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "What is machine learning?"
            }
        }


class EmbeddingResponse(BaseModel):
    """Response containing embeddings."""
    embeddings: List[List[float]] = Field(..., description="List of embeddings (vectors)")
    texts: List[str] = Field(..., description="Texts corresponding to embeddings")
    dimension: int = Field(..., description="Dimension of each embedding vector")
    model: str = Field(..., description="Embedding model used")


class EmbedTextResponse(BaseModel):
    """Response for embedding a single text."""
    text: str
    embedding: List[float] = Field(..., description="Embedding vector")
    dimension: int
    model: str


class SubjectListItem(BaseModel):
    id: str
    name: str


class TopicListItem(BaseModel):
    id: str
    name: str

