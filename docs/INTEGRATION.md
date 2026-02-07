# Frontend Integration & Efficient API Usage

This guide explains recommended patterns for integrating the Next.js frontend with the SyllabiQ FastAPI backend, focusing on efficient API calls and a good skeleton/loading experience.

1) Debounce user input
- Don't call the API on every keystroke. Debounce (300–600ms) and cancel in-flight requests when a new query is issued.

2) Use small payloads
- Send only necessary fields (query, workflow, marks). Avoid sending user notes unless required.

3) Progressive / streaming UX
- For long answers, prefer a streaming endpoint (SSE or WebSocket). The backend skeleton currently returns full responses; add a streaming generation in the future for token-by-token UX.

4) Skeleton & loading states
- Show a compact skeleton card while waiting for the response:
  - Title: "Generating answer..."
  - Small animated lines for bullets
  - Show estimated time or spinner
- Replace skeleton with final content when returned. If streaming is implemented, progressively append tokens.

5) Caching & re-use
- Cache recent queries client-side (session storage) keyed by query + marks + workflow.
- Use ETag caching on static syllabus metadata endpoints (future).

6) API call example (fetch)

```javascript
// POST /api/v1/query
async function querySyllabiQ(query, workflow, marks=5) {
  const res = await fetch('/api/v1/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, workflow, marks })
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}
```

7) Error handling
- Surface friendly messages: "We couldn't fetch the syllabus content right now — try again."
- If validation fails (400), show actionable hints.

Accessibility
- Ensure skeletons are accessible (aria-busy, role="status") and keyboard-focusable elements are present.

