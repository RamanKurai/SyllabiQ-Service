from fastapi import APIRouter, HTTPException
from app.schemas import QueryRequest, QueryResponse
from app.agents import IntentAgent, RetrievalAgent, GenerationAgent, ValidationAgent

router = APIRouter()

# initialize lightweight agents (singletons for now)
intent_agent = IntentAgent()
retrieval_agent = RetrievalAgent()
generation_agent = GenerationAgent()
validation_agent = ValidationAgent()


@router.get("/", include_in_schema=False)
async def root():
    return {"message": "SyllabiQ backend. See /docs for API"}


@router.post("/v1/query", response_model=QueryResponse, tags=["query"])
async def query_endpoint(payload: QueryRequest):
    """
    Core query endpoint.
    Workflow:
      1. Intent detection
      2. Retrieval of relevant syllabus chunks
      3. Generation of response
      4. Validation (guardrails)
    """
    try:
        intent = await intent_agent.detect_intent(payload.query, payload.workflow)
        retrieved = await retrieval_agent.retrieve(payload.query, top_k=payload.top_k or 5)
        generated = await generation_agent.generate(
            query=payload.query, intent=intent, context=retrieved, marks=payload.marks
        )
        validated = await validation_agent.validate(generated, context=retrieved)

        return QueryResponse(
            answer=validated["answer"],
            citations=validated.get("citations", []),
            metadata={"intent": intent, "chunks_returned": len(retrieved)},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

