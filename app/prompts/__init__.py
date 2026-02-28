"""
Prompt templates and constants.
Add prompt engineering helpers here so generation logic can import them cleanly.
"""

DEFAULT_QA_PROMPT = (
    "You are an assistant that answers questions strictly using the provided syllabus context. "
    "If the answer is not present, say you don't know."
)

SUMMARIZE_PROMPT = (
    "Summarize the provided text into concise, numbered bullet points suitable for exam revision. "
    "Focus on key concepts, definitions, formulas, and important facts."
)

GENERATION_PROMPT = (
    "Generate practice questions from the provided content suitable for exam preparation. "
    "Return ONLY a valid JSON array. Each element must have: "
    '"question" (string), "type" ("mcq"|"short"|"long"), '
    '"options" (array of 4 strings for mcq, null otherwise), "answer" (string).'
)

