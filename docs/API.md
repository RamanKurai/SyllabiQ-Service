# SyllabiQ Backend — API Reference

Base URL (dev): http://localhost:8000/api

Endpoints:

- GET /health
  - Description: Service health check
  - Response: { "status": "ok", "service": "syllabiq-backend" }

- POST /v1/query
  - Description: Main query endpoint. Accepts a query and orchestrates intent detection, retrieval, generation and validation.
  - Request body (JSON):
    - query: string (required)
    - workflow: string (optional) - hint like "qa", "summarize", "generate"
    - marks: integer (optional) - 2,5,10 to control answer length
    - top_k: integer (optional) - how many retrieval chunks to fetch
    - format: string (optional) - "bullets" | "paragraph"
  - Response:
    - answer: string
    - citations: array of citation objects {id, source, text}
    - metadata: object (intent, chunks_returned, etc)

See the live OpenAPI docs at /docs when running the app (FastAPI provides Swagger UI automatically).

