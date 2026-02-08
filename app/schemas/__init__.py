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


class Citation(BaseModel):
    id: str
    source: Optional[str]
    text: Optional[str]


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    metadata: Dict[str, Any] = {}

